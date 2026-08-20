"""One runnable check per piece of non-trivial logic. `python test_main.py`.

Nothing here calls the API — these cover the request assembly, the packet
arithmetic, and the two mechanical repairs, all of which are wrong in ways a
live run would only reveal after spending money.
"""

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

import docs
import llm
from main import (
    extract_template,
    mark_frame_status,
    repair,
    snapshot_times,
    trim_packets,
    write_storyboard,
)


def _usage(**kw):
    defaults = dict(
        input_tokens=1000,
        output_tokens=200,
        cache_read_input_tokens=0,
        cache_creation_input_tokens=0,
        server_tool_use=SimpleNamespace(web_search_requests=0),
    )
    return SimpleNamespace(**{**defaults, **kw})


def _model(name):
    """A Model with a stubbed client, so no credential is needed."""
    with patch("anthropic.Anthropic"):
        return llm.Model(name)


def test_request_shape_per_model() -> None:
    """`effort` is rejected on Haiku 4.5 and `temperature` on every 5-series
    model, so the request must carry neither by default."""
    for name, wants_effort in (
        ("claude-haiku-4-5", False),
        ("claude-sonnet-5", True),
    ):
        model = _model(name)
        model.client.messages.create.return_value = SimpleNamespace(
            content=[SimpleNamespace(type="text", text="<template></template>")],
            stop_reason="end_turn",
            usage=_usage(),
        )
        model.author("frame", "ROLE CONTRACT", "PACKET")
        request = model.client.messages.create.call_args.kwargs

        assert "temperature" not in request, name
        assert ("effort" in request.get("output_config", {})) is wants_effort, name

        # The shared contract carries the cache breakpoint; the per-frame task
        # must stay in the user turn or the prefix differs every call and nothing
        # is ever read back.
        assert request["system"][0]["cache_control"] == {"type": "ephemeral"}
        assert request["system"][0]["text"] == "ROLE CONTRACT"
        assert request["messages"][0]["content"] == "PACKET"


def test_truncation_and_refusal_raise() -> None:
    """A truncated or declined answer must not be written to disk as a frame."""
    for stop_reason, expected in (
        ("max_tokens", "truncated"),
        ("refusal", "declined"),
    ):
        model = _model("claude-haiku-4-5")
        model.client.messages.create.return_value = SimpleNamespace(
            content=[SimpleNamespace(type="text", text="half a fra")],
            stop_reason=stop_reason,
            stop_details=SimpleNamespace(category="cyber"),
            usage=_usage(),
        )
        try:
            model.author("frame", "role", "packet")
        except RuntimeError as exc:
            assert expected in str(exc), (stop_reason, exc)
        else:
            raise AssertionError(f"{stop_reason} should raise")


def test_ledger_prices_cache_and_search() -> None:
    """Cache reads bill at 0.1x, writes at 1.25x, and search is per request."""
    ledger = llm.Ledger()
    ledger.record(
        "r",
        "claude-haiku-4-5",  # $1 / $5 per MTok
        _usage(
            input_tokens=1_000_000,
            output_tokens=1_000_000,
            cache_read_input_tokens=1_000_000,
            cache_creation_input_tokens=1_000_000,
            server_tool_use=SimpleNamespace(web_search_requests=3),
        ),
        1.0,
    )
    # 1.00 input + 5.00 output + 0.10 cache read + 1.25 cache write + 0.03 search
    assert abs(ledger.total_usd() - 7.38) < 1e-9, ledger.total_usd()
    assert "3 web search(es)" in ledger.summary()


def test_packet_trim_drops_largest_rule_first() -> None:
    """The biggest blueprint plus four big rules cannot fit the 48 KB packet."""
    big = max(docs.blueprints(), key=docs.blueprint_bytes)
    rules = sorted(docs.rule_names(), key=docs.rule_bytes, reverse=True)[:4]
    with TemporaryDirectory() as tmp:
        project = Path(tmp)
        (project / "STORYBOARD.md").write_text(
            "---\nformat: 1080x1920\n---\n\n## Frame 1 — Hook\n\n"
            "- src: compositions/frames/01-hook.html\n- duration: 6.0s\n"
            f"- blueprint: {big}\n- rules: {', '.join(rules)}\n\nNarrative.\n",
            encoding="utf-8",
        )
        trim_packets(project)
        kept_text = (project / "STORYBOARD.md").read_text(encoding="utf-8")

    kept = [r for r in rules if r in kept_text]
    assert kept, "the trimmer removed every rule"
    assert len(kept) < len(rules), "nothing was trimmed despite overflowing"
    assert sum(docs.rule_bytes(r) for r in kept) < docs.PACKET_LIMIT - docs.blueprint_bytes(big)
    # Largest goes first, so the smallest cited rule always survives.
    assert min(rules, key=docs.rule_bytes) in kept


def test_repair_fixes_only_what_has_one_answer() -> None:
    html = """<template><style>
    @font-face { font-family: "Archivo Black"; src: url(assets/fonts/a.woff2); }
    #f01-a { transform: scale(0.8); }
    #f01-untouched { transform: rotate(3deg); }
    #f01-centered { transform: translateX(-50%) scale(0.9); }
    </style>
    <div id="f01-inline" style="opacity: 0; transform: translateY(20px);"></div>
    <script>
      tl.to("#f01-a", { scale: 1 });
      tl.to("#f01-inline", { y: 0 });
      tl.to("#f01-centered", { scale: 1 });
    </script></template>"""
    fixed = repair(html, "01-hook")

    assert "@font-face" not in fixed          # bundled already; the path 404s
    assert "scale(0.8)" not in fixed          # tweened, so CSS initial state goes
    assert "translateY(20px)" not in fixed
    assert "rotate(3deg)" in fixed            # never tweened — author's call
    assert "translateX(-50%)" in fixed        # centering; removing it moves it
    assert "opacity: 0" in fixed and fixed.count("<script>") == 1


def test_repair_separates_overlapping_clips() -> None:
    html = """<template>
    <div class="clip" data-start="0" data-duration="2" data-track-index="1"></div>
    <div class="clip" data-start="1" data-duration="2" data-track-index="1"></div>
    </template>"""
    fixed = repair(html, "01-hook")

    assert 'data-track-index="1"' in fixed
    assert 'data-track-index="2"' in fixed


def test_extracts_only_the_template() -> None:
    assert extract_template("chat <template><div/></template> more") == (
        "<template><div/></template>"
    )
    assert extract_template("I cannot help with that.") is None


def test_vocabularies_and_prompts() -> None:
    """The schema enums are only as real as these parsers."""
    assert len(docs.blueprints()) == 22
    assert len(docs.rule_names()) == 48
    # Every enum value must have a file the packet builder can inline, or a legal
    # model answer produces an unbuildable packet.
    assert all(docs.blueprint_bytes(b) > 0 for b in docs.blueprint_ids())
    assert all(docs.rule_bytes(r) > 0 for r in docs.rule_names())

    filled = docs.prompt(
        "story", length=45, topic="t", canvas="1080x1920", frame_count=6,
        per_frame="7.5", words=20, source_material="notes",
    )
    assert "${" not in filled and "notes" in filled
    try:
        docs.prompt("story", length=45)
    except KeyError:
        pass
    else:
        raise AssertionError("a missing prompt value should raise")


def test_storyboard_writer_and_midpoint_snapshots() -> None:
    """The visual pass must write its shot sequence and useful proof times."""
    plan = {
        "message": "A useful list",
        "arc": "listicle: compare five tools",
        "audience": "local owners: practical learners",
        "music": "calm minimal",
        "frames": [
            {
                "title": "Hook",
                "scene": "A sharp question: what is affordable?",
                "duration_s": 3.0,
                "transition_in": "cut",
                "voiceover": "Start with the task, not the tool.",
                "role": "Hook",
                "type": "hook",
                "persuasion": "Question and answer",
                "beat": "curiosity",
                "narrative_role": "Opens the cost question.",
                "key_message": "Choose the task before the subscription.",
                "frame_id": "01-hook",
            },
            {
                "title": "Payoff",
                "scene": "One rule lands cleanly.",
                "duration_s": 5.0,
                "transition_in": "crossfade",
                "voiceover": "Review the result before adopting it.",
                "role": "CTA",
                "frame_id": "02-payoff",
            },
        ],
    }
    design = {
        "direction": {"current": "UP", "primary_transition": "crossfade", "notes": "Hold the rule."},
        "frames": [
            {
                "frame": 1,
                "blueprint": "kinetic-type-beats",
                "focal": "the question",
                "roles": ["foreground", "background"],
                "rules": ["dynamic-content-sequencing"],
                "scenes": [{"at_s": 0, "shows": "Question enters."}, {"at_s": 2, "shows": "Accent lands."}],
            }
        ],
    }
    with TemporaryDirectory() as tmp:
        project = Path(tmp)
        write_storyboard(project, plan, "1080x1920", 8, design)
        mark_frame_status(project, "01-hook", "animated")
        written = (project / "STORYBOARD.md").read_text(encoding="utf-8")
        assert "Scene at 2s: Accent lands." in written
        assert 'arc: "listicle: compare five tools"' in written
        assert "- type: hook" in written
        assert "- status: animated" in written
        assert snapshot_times(project) == "1.50,5.50"


def main() -> None:
    test_request_shape_per_model()
    test_truncation_and_refusal_raise()
    test_ledger_prices_cache_and_search()
    test_packet_trim_drops_largest_rule_first()
    test_repair_fixes_only_what_has_one_answer()
    test_repair_separates_overlapping_clips()
    test_extracts_only_the_template()
    test_vocabularies_and_prompts()
    test_storyboard_writer_and_midpoint_snapshots()
    print("ok")


if __name__ == "__main__":
    main()

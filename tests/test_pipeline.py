import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from video_pipeline.composition import (
    add_frame_ids,
    inject_visual_transitions,
    render_frames,
    write_catalog_selection,
    write_storyboard,
)
from video_pipeline.planning import validate
from video_pipeline.runtime import slugify
from video_pipeline.research import as_notes, cache_path, validate as validate_research, write_artifacts
import video_pipeline.runtime as runtime_module

def make_plan(transition: str = "push-slide LEFT") -> dict:
    plan = {
        "message": "Choose tools by the work they improve.",
        "audience": "Small local teams",
        "music": "minimal",
        "scenes": [
            {
                "title": "Hook",
                "slug": "hook",
                "voiceover": "Start with one task your team repeats every week.",
                "duration_s": 4,
                "transition_in": "cut",
                "kind": "hero",
                "eyebrow": "START HERE",
                "headline": "Choose the task first.",
                "subhead": "Useful tools solve repeated work.",
                "hero": "01",
                "hero_label": "One workflow",
                "items": [],
            },
            {
                "title": "Proof",
                "slug": "proof",
                "voiceover": "Compare the result against one clear measure before subscribing.",
                "duration_s": 4,
                "transition_in": transition,
                "kind": "interface",
                "eyebrow": "CHECK THE RESULT",
                "headline": "Measure before subscribing.",
                "subhead": "Use one repeatable task.",
                "hero": "VERIFY",
                "hero_label": "Test workflow",
                "items": [],
            },
            {
                "title": "Follow",
                "slug": "follow",
                "voiceover": "Follow Pupukahi Tech for practical technology guidance.",
                "duration_s": 4,
                "transition_in": "push-slide LEFT",
                "kind": "cta",
                "eyebrow": "",
                "headline": "Follow",
                "subhead": "",
                "hero": "",
                "hero_label": "",
                "items": [],
            },
        ],
    }
    validate(plan, 3)
    return plan

def test_external_template_builds_safe_hyperframes_scene() -> None:
    plan = make_plan()
    add_frame_ids(plan)
    plan["scenes"][0]["headline"] = "Safe <script>alert(1)</script>"
    with TemporaryDirectory() as tmp:
        project = Path(tmp)
        write_storyboard(project, plan, 12)
        write_catalog_selection(project, plan)
        render_frames(project, plan)
        scene = (project / "compositions/frames/01-hook.html").read_text(encoding="utf-8")
    assert "@@" not in scene
    assert "Safe &lt;script&gt;alert(1)&lt;/script&gt;" in scene
    assert 'data-composition-id="01-hook"' in scene
    assert "window.__timelines['01-hook']" in scene
    assert 'class="visual-stage hero-stage"' in scene
    assert "FIELD NOTE" not in scene
    assert "Useful technology" not in scene
    assert "registration" not in scene
    assert "visual-rule" not in scene


# Verify plans without catalog choices do not create unnecessary files.
def test_empty_catalog_selection_writes_nothing() -> None:
    plan = make_plan()
    with TemporaryDirectory() as tmp:
        project = Path(tmp)
        write_catalog_selection(project, plan)
        assert not (project / "catalog-selection.json").exists()
        assert not (project / "catalog-install.sh").exists()
        assert not (project / "catalog-allowlist.json").exists()

def test_legacy_visual_kind_is_normalized() -> None:
    plan = {
        "message": "Use one task to choose a tool.",
        "audience": "Small teams",
        "music": "quiet",
        "scenes": [
            {
                "title": "Hook",
                "slug": "hook",
                "voiceover": "Start with the task you repeat.",
                "duration_s": 4,
                "transition_in": "cut",
                "layout": "hero",
                "visual_kind": "prompt-reply",
                "eyebrow": "START",
                "headline": "Start with the task",
                "subhead": "",
                "hero": "01",
                "hero_label": "",
                "items": [],
            },
            {
                "title": "End",
                "slug": "end",
                "voiceover": "Follow for practical tools.",
                "duration_s": 4,
                "transition_in": "push-slide LEFT",
                "layout": "cta",
                "visual_kind": "cta",
                "eyebrow": "",
                "headline": "Anything",
                "subhead": "",
                "hero": "",
                "hero_label": "",
                "items": [],
            },
        ],
    }
    validate(plan, 2)
    assert plan["scenes"][0]["kind"] == "hero"
    assert plan["scenes"][-1]["headline"] == "FOLLOW @pupukahi_tech"
    assert plan["scenes"][-1]["catalog_item"] == "none"

def test_visual_transition_targets_visual_group_not_scene_shell() -> None:
    for transition, expected_property in (
        ("push-slide LEFT", '"--hf-visual-x"'),
        ("zoom-through", '"--hf-visual-scale"'),
    ):
        plan = make_plan(transition)
        add_frame_ids(plan)
        with TemporaryDirectory() as tmp:
            project = Path(tmp)
            write_storyboard(project, plan, 12)
            hosts = "\n".join(
                f'<div id="el-{scene["frame_id"]}" data-composition-id="{scene["frame_id"]}"></div>'
                for scene in plan["scenes"]
            )
            (project / "index.html").write_text(
                '<div data-composition-id="main" data-duration="12"></div>\n'
                'window.__timelines["main"] = gsap.timeline({ paused: true });\n'
                + hosts,
                encoding="utf-8",
            )
            inject_visual_transitions(project, plan)
            html = (project / "index.html").read_text(encoding="utf-8")
        assert expected_property in html
        assert 'tl.to("#el-' not in html

def test_research_cache_keeps_only_sourced_facts() -> None:
    payload = validate_research(
        {
            "topic": "A useful topic",
            "audience": "Local businesses",
            "facts": [
                {
                    "claim": "An official program opened in 2026.",
                    "detail": "Applications require one named eligibility step.",
                    "source_title": "Official program page",
                    "source_url": "https://example.gov/program",
                },
                {
                    "claim": "This unsupported row is removed.",
                    "detail": "It has no usable source URL.",
                    "source_title": "Missing source",
                    "source_url": "not-a-url",
                },
            ],
        },
        "A useful topic",
    )
    assert [fact["id"] for fact in payload["facts"]] == ["F1"]
    assert "[F1]" in as_notes(payload)
    assert "https://example.gov/program" in as_notes(payload)
    assert cache_path("A useful topic").name == "a-useful-topic.json"
    with TemporaryDirectory() as tmp:
        write_artifacts(Path(tmp), payload)
        assert (Path(tmp) / "research.json").is_file()
        assert "F1" in (Path(tmp) / "SOURCES.md").read_text(encoding="utf-8")
    try:
        validate_research(payload, "A useful topic", {"https://example.gov/other"})
    except ValueError as exc:
        assert "no usable sourced facts" in str(exc)
    else:
        raise AssertionError("research accepted a URL absent from web-search results")

def test_plan_rejects_unknown_research_fact() -> None:
    plan = make_plan()
    plan["scenes"][0]["fact_ids"] = ["F9"]
    try:
        validate(plan, 3, {"F1"})
    except ValueError as exc:
        assert "unknown research facts" in str(exc)
    else:
        raise AssertionError("unknown research fact was accepted")

def test_plan_normalizes_unicode_dashes() -> None:
    plan = make_plan()
    plan["scenes"][0]["voiceover"] = "Fast aid—with a human making the final decision."
    validate(plan, 3)
    assert "—" not in plan["scenes"][0]["voiceover"]

def test_plan_rejects_wordy_on_screen_copy() -> None:
    plan = make_plan()
    plan["scenes"][0]["headline"] = "This headline has far too many words for video"
    try:
        validate(plan, 3)
    except ValueError as exc:
        assert "six words or fewer" in str(exc)
    else:
        raise AssertionError("wordy headline was accepted")


# Verify output names are predictable, safe, and length-limited.
def test_slugify_is_stable() -> None:
    assert slugify("  A useful project!!! ") == "a-useful-project"
    assert len(slugify("x" * 100)) == 60

def test_incomplete_scaffold_is_resumed() -> None:
    with TemporaryDirectory() as tmp:
        old_output = runtime_module.OUTPUT
        runtime_module.OUTPUT = Path(tmp)
        try:
            incomplete = Path(tmp) / "topic-v1"
            incomplete.mkdir()
            (incomplete / "hyperframes.json").write_text("{}")
            assert runtime_module.next_project("Topic") == incomplete
            (incomplete / "plan.json").write_text("{}")
            assert runtime_module.next_project("Topic") == Path(tmp) / "topic-v2"
            (Path(tmp) / "topic-v4").mkdir()
            assert runtime_module.next_project("Topic") == Path(tmp) / "topic-v5"
        finally:
            runtime_module.OUTPUT = old_output


if __name__ == "__main__":
    test_external_template_builds_safe_hyperframes_scene()
    test_empty_catalog_selection_writes_nothing()
    test_legacy_visual_kind_is_normalized()
    test_visual_transition_targets_visual_group_not_scene_shell()
    test_research_cache_keeps_only_sourced_facts()
    test_plan_rejects_unknown_research_fact()
    test_plan_normalizes_unicode_dashes()
    test_plan_rejects_wordy_on_screen_copy()
    test_slugify_is_stable()
    test_incomplete_scaffold_is_resumed()
    print("ok")

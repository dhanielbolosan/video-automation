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
from video_pipeline.planning import load_plan, validate
from video_pipeline.project import ROOT, slugify
from video_pipeline.research import as_notes, cache_path, validate as validate_research, write_artifacts
import video_pipeline.project as project_module


def test_external_template_builds_safe_hyperframes_scene() -> None:
    plan = load_plan(ROOT / "examples" / "ai-subscriptions-plan.json", 6)
    add_frame_ids(plan)
    plan["scenes"][0]["headline"] = "Safe <script>alert(1)</script>"
    with TemporaryDirectory() as tmp:
        project = Path(tmp)
        write_storyboard(project, plan, 43)
        write_catalog_selection(project, plan)
        render_frames(project, plan)
        scene = (project / "compositions/frames/01-start-with-work.html").read_text(encoding="utf-8")
    assert "@@" not in scene
    assert "Safe &lt;script&gt;alert(1)&lt;/script&gt;" in scene
    assert 'data-composition-id="01-start-with-work"' in scene
    assert "window.__timelines['01-start-with-work']" in scene
    assert 'class="visual-stage hero-stage"' in scene
    assert "FIELD NOTE" not in scene
    assert "Useful technology" not in scene
    assert "registration" not in scene
    assert "visual-rule" not in scene


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
    plan = load_plan(ROOT / "examples" / "ai-subscriptions-plan.json", 6)
    add_frame_ids(plan)
    with TemporaryDirectory() as tmp:
        project = Path(tmp)
        write_storyboard(project, plan, 43)
        hosts = "\n".join(
            f'<div id="el-{scene["frame_id"]}" data-composition-id="{scene["frame_id"]}"></div>'
            for scene in plan["scenes"]
        )
        (project / "index.html").write_text(
            '<div data-composition-id="main" data-duration="43"></div>\n'
            'window.__timelines["main"] = gsap.timeline({ paused: true });\n'
            + hosts,
            encoding="utf-8",
        )
        inject_visual_transitions(project, plan)
        html = (project / "index.html").read_text(encoding="utf-8")
    assert '"--hf-visual-x"' in html
    assert '"--hf-visual-scale"' in html
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
    plan = load_plan(ROOT / "examples" / "ai-subscriptions-plan.json", 6)
    plan["scenes"][0]["fact_ids"] = ["F9"]
    try:
        validate(plan, 6, {"F1"})
    except ValueError as exc:
        assert "unknown research facts" in str(exc)
    else:
        raise AssertionError("unknown research fact was accepted")


def test_plan_normalizes_unicode_dashes() -> None:
    plan = load_plan(ROOT / "examples" / "ai-subscriptions-plan.json", 6)
    plan["scenes"][0]["voiceover"] = "Fast aid—with a human making the final decision."
    validate(plan, 6)
    assert "—" not in plan["scenes"][0]["voiceover"]


def test_plan_rejects_wordy_on_screen_copy() -> None:
    plan = load_plan(ROOT / "examples" / "ai-subscriptions-plan.json", 6)
    plan["scenes"][0]["headline"] = "This headline has far too many words for video"
    try:
        validate(plan, 6)
    except ValueError as exc:
        assert "six words or fewer" in str(exc)
    else:
        raise AssertionError("wordy headline was accepted")


def test_slugify_is_stable() -> None:
    assert slugify("  A useful project!!! ") == "a-useful-project"
    assert len(slugify("x" * 100)) == 60


def test_incomplete_scaffold_is_resumed() -> None:
    with TemporaryDirectory() as tmp:
        old_output = project_module.OUTPUT
        project_module.OUTPUT = Path(tmp)
        try:
            incomplete = Path(tmp) / "topic-v1"
            incomplete.mkdir()
            (incomplete / "hyperframes.json").write_text("{}")
            assert project_module.next_project("Topic") == incomplete
            (incomplete / "plan.json").write_text("{}")
            assert project_module.next_project("Topic") == Path(tmp) / "topic-v2"
            (Path(tmp) / "topic-v4").mkdir()
            assert project_module.next_project("Topic") == Path(tmp) / "topic-v5"
        finally:
            project_module.OUTPUT = old_output


if __name__ == "__main__":
    test_external_template_builds_safe_hyperframes_scene()
    test_legacy_visual_kind_is_normalized()
    test_visual_transition_targets_visual_group_not_scene_shell()
    test_research_cache_keeps_only_sourced_facts()
    test_plan_rejects_unknown_research_fact()
    test_plan_normalizes_unicode_dashes()
    test_plan_rejects_wordy_on_screen_copy()
    test_slugify_is_stable()
    test_incomplete_scaffold_is_resumed()
    print("ok")

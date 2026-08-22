import sys
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from video_pipeline.composition import add_frame_ids, render_frames, write_storyboard
from video_pipeline.planning import load_plan
from video_pipeline.project import ROOT, slugify
import video_pipeline.project as project_module


def test_external_template_builds_safe_hyperframes_scene() -> None:
    plan = load_plan(ROOT / "examples" / "ai-subscriptions-plan.json", 6)
    add_frame_ids(plan)
    plan["scenes"][0]["headline"] = "Safe <script>alert(1)</script>"
    with TemporaryDirectory() as tmp:
        project = Path(tmp)
        write_storyboard(project, plan, 43)
        render_frames(project, plan)
        scene = (project / "compositions/frames/01-start-with-work.html").read_text(encoding="utf-8")
    assert "@@" not in scene
    assert "Safe &lt;script&gt;alert(1)&lt;/script&gt;" in scene
    assert 'data-composition-id="01-start-with-work"' in scene
    assert "window.__timelines['01-start-with-work']" in scene


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
        finally:
            project_module.OUTPUT = old_output


if __name__ == "__main__":
    test_external_template_builds_safe_hyperframes_scene()
    test_slugify_is_stable()
    test_incomplete_scaffold_is_resumed()
    print("ok")

"""Render structured scene data through external HyperFrames HTML templates."""

from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path

from .project import ROOT

TEMPLATES = ROOT / "video_pipeline" / "templates"


def _clean(value: object) -> str:
    return html.escape(" ".join(str(value or "").split()), quote=True)


def _replace(template: str, values: dict[str, object]) -> str:
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace(f"@@{key}@@", str(value))
    missing = sorted(set(re.findall(r"@@([A-Z_]+)@@", rendered)))
    if missing:
        raise ValueError(f"unfilled template slots: {', '.join(missing)}")
    return rendered


def add_frame_ids(plan: dict) -> dict:
    for number, scene in enumerate(plan["scenes"], 1):
        scene["frame_id"] = f"{number:02d}-{scene['slug']}"
    return plan


def write_brief(project: Path, topic: str, destination: str, length: int, voice: str) -> None:
    (project / "BRIEF.md").write_text(
        f"""# BRIEF — {topic}

- workflow: faceless-explainer
- flow: automation
- storyboard: no
- destination: {destination}
- aspect: 1080x1920
- length: {length}s
- captions: on
- voice: {voice}
- style: dark-technical-editorial

## Direction

Reference-driven layouts based on `references/social-video/`. AI supplies only
structured content; external templates own typography, spacing, graphics, and motion.
""",
        encoding="utf-8",
    )
    shutil.copyfile(ROOT / "brand" / "frame.md", project / "frame.md")
    brand_assets = project / "assets" / "brand"
    brand_assets.mkdir(parents=True, exist_ok=True)
    for source, name in (
        (ROOT / "brand/.media/images/logo_002.svg", "logo-white.svg"),
        (ROOT / "brand/.media/images/logo_001.webp", "logo-color.webp"),
        (ROOT / "brand/.media/images/image_001.webp", "website-hero.webp"),
    ):
        if not source.is_file():
            raise RuntimeError(f"missing official brand asset: {source}")
        shutil.copyfile(source, brand_assets / name)
    skin = ROOT / ".agents/skills/hyperframes-creative/frame-presets/code-editorial/caption-skin.html"
    if skin.is_file():
        (project / ".hyperframes").mkdir(exist_ok=True)
        shutil.copyfile(skin, project / ".hyperframes" / "caption-skin.html")


def write_storyboard(project: Path, plan: dict, length: int) -> None:
    lines = [
        "---", "format: 1080x1920", f"duration: {length}s",
        f"message: {json.dumps(plan['message'], ensure_ascii=False)}",
        f"audience: {json.dumps(plan['audience'], ensure_ascii=False)}",
        f"music: {json.dumps(plan['music'], ensure_ascii=False)}", "mode: autonomous", "---", "",
    ]
    for number, scene in enumerate(plan["scenes"], 1):
        lines += [
            f"## Frame {number} — {scene['title']}", "",
            f"- scene: {json.dumps(scene['headline'], ensure_ascii=False)}",
            f"- duration: {scene['duration_s']:g}s",
            f"- transition_in: {scene['transition_in']}",
            "- status: animated",
            f"- voiceover: {json.dumps(scene['voiceover'], ensure_ascii=False)}",
            f"- role: {'CTA' if scene['layout'] == 'cta' else 'Key_Feature'}",
            f"- type: {'cta' if scene['layout'] == 'cta' else 'feature_showcase'}",
            f"- src: compositions/frames/{scene['frame_id']}.html", "",
            f"Layout: {scene['layout']}. Hero: {scene['hero'] or scene['headline']}", "",
        ]
    lines += ["## Video direction", "", "- current: LEFT", "- primary_transition: push-slide LEFT", ""]
    (project / "STORYBOARD.md").write_text("\n".join(lines), encoding="utf-8")


def write_script(project: Path, plan: dict, voice: str) -> None:
    lines = [f"# SCRIPT — {project.name}", "", f"**Voice:** {voice} (Kokoro, local)", "", "---", ""]
    for number, scene in enumerate(plan["scenes"], 1):
        lines += [f"## Line {number} — {scene['title']} (Frame {number})", "", f"    {scene['voiceover']}", ""]
    (project / "SCRIPT.md").write_text("\n".join(lines), encoding="utf-8")


def storyboard_durations(project: Path) -> dict[str, float]:
    text = (project / "STORYBOARD.md").read_text(encoding="utf-8")
    durations: dict[str, float] = {}
    for block in re.split(r"(?m)^(?=## Frame )", text):
        src = re.search(r"compositions/frames/([\w.-]+)\.html", block)
        duration = re.search(r"(?m)^- duration:\s*([\d.]+)s", block)
        if src and duration:
            durations[src.group(1)] = float(duration.group(1))
    return durations


def render_frames(project: Path, plan: dict) -> None:
    template = (TEMPLATES / "frame.html").read_text(encoding="utf-8")
    durations = storyboard_durations(project)
    target = project / "compositions" / "frames"
    target.mkdir(parents=True, exist_ok=True)
    for scene in plan["scenes"]:
        frame_id = scene["frame_id"]
        items = "".join(
            f'<div class="item"><span class="item-index">{index:02d}</span>'
            f'<span class="item-label">{_clean(item["label"])}</span>'
            f'<strong class="item-value">{_clean(item["value"])}</strong></div>'
            for index, item in enumerate(scene["items"], 1)
        )
        values = {
            "FRAME_ID": frame_id,
            "LAYOUT": scene["layout"],
            "DURATION": f"{durations.get(frame_id, scene['duration_s']):g}",
            "EYEBROW": _clean(scene["eyebrow"]),
            "HEADLINE": _clean(scene["headline"]),
            "SUBHEAD": _clean(scene["subhead"]),
            "HERO": _clean(scene["hero"]),
            "HERO_LABEL": _clean(scene["hero_label"]),
            "ITEMS": items,
        }
        (target / f"{frame_id}.html").write_text(_replace(template, values), encoding="utf-8")


def snapshot_times(project: Path) -> str:
    total = 0.0
    times = []
    for duration in storyboard_durations(project).values():
        times.append(f"{total + duration / 2:.2f}")
        total += duration
    return ",".join(times) or "0"

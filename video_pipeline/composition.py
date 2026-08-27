"""Compile a validated plan into deterministic, portrait-native HyperFrames scenes."""

from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path

from .catalog import install_commands, selected_items
from .project import ROOT

TEMPLATES = ROOT / "video_pipeline" / "templates"
CATALOG = ROOT / "video_pipeline" / "catalog"

CAPTION_OVERRIDE = """
<style>
  .caption-pill { max-width: 86%; padding: 0; background: transparent; border: 0; border-radius: 0; box-shadow: none; }
  .caption-line { font-family: "Inter", sans-serif; font-weight: 700; text-shadow: 0 3px 12px rgba(0,0,0,.8); }
  .caption-word, .caption-word.is-spoken { padding: .08em .12em; color: #fff; border: 0; background: transparent; }
  .caption-word.is-active { padding: .08em .12em; color: #fff; background: transparent; border: 0; border-bottom: 3px solid #39a1ac; box-shadow: none; }
</style>
"""


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


def _items(scene: dict) -> list[dict[str, str]]:
    return [
        {"label": _clean(item.get("label")), "value": _clean(item.get("value"))}
        for item in scene.get("items", [])
    ]


def _rows(items: list[dict[str, str]], class_name: str = "visual-row") -> str:
    return "".join(
        f'<div class="{class_name}"><span class="row-index">{index:02d}</span>'
        f'<span class="row-label">{item["label"]}</span><strong class="row-value">{item["value"]}</strong></div>'
        for index, item in enumerate(items, 1)
    )


def _hero(scene: dict, items: list[dict[str, str]], *, rank: bool = False) -> str:
    raw_hero = str(scene.get("hero") or "").strip()
    ordinal = bool(re.fullmatch(r"#?\d{1,3}", raw_hero))
    value = _clean(scene.get("hero_label") if rank else ("" if ordinal else (raw_hero or scene.get("headline"))))
    label = _clean(scene.get("hero_label"))
    rows = _rows(items, "visual-row rank-row" if rank else "visual-row")
    stage_class = "visual-stage rank-stage" if rank else "visual-stage hero-stage"
    index = f'<span class="rank-index">{_clean(raw_hero or "01")}</span>' if rank else ""
    signal = '<div class="hero-signal" aria-hidden="true"><span></span><i>→</i></div>' if ordinal and not rank else ""
    return (
        f'<div class="{stage_class}" data-catalog-item="{_clean(scene.get("catalog_item", "none"))}">'
        f'<div class="hero-main">{index}<div class="visual-number">{value}</div>{signal}'
        f'<div class="visual-label">{"" if rank else label}</div></div>'
        f'<div class="visual-rows">{rows}</div></div>'
    )


def _stat(scene: dict, items: list[dict[str, str]]) -> str:
    value = _clean(scene.get("hero") or scene.get("headline"))
    label = _clean(scene.get("hero_label"))
    return (
        f'<div class="visual-stage stat-stage" data-catalog-item="{_clean(scene.get("catalog_item", "none"))}">'
        f'<div class="stat-number visual-number">{value}</div><div class="visual-label">{label}</div>'
        '<div class="stat-track"><span class="stat-fill"></span></div>'
        f'<div class="visual-rows">{_rows(items)}</div></div>'
    )


def _compare(scene: dict, items: list[dict[str, str]]) -> str:
    columns = []
    for index, item in enumerate(items[:2]):
        columns.append(
            f'<div class="compare-column visual-item"><span class="compare-kicker">{chr(65 + index)}</span>'
            f'<strong class="compare-title">{item["label"]}</strong><span class="compare-value">{item["value"]}</span>'
            '</div>'
        )
    joined = '<span class="compare-seam"></span>'.join(columns)
    return (
        f'<div class="visual-stage compare-stage" data-catalog-item="{_clean(scene.get("catalog_item", "none"))}">'
        f'<div class="compare-columns">{joined}</div>'
        f'<div class="compare-caption">{_clean(scene.get("hero_label"))}</div></div>'
    )


def _process(scene: dict, items: list[dict[str, str]]) -> str:
    steps = []
    for index, item in enumerate(items[:3], 1):
        steps.append(
            f'<div class="process-step visual-item"><span class="process-index">{index:02d}</span>'
            f'<div><strong>{item["label"]}</strong><span>{item["value"]}</span></div></div>'
        )
    return (
        f'<div class="visual-stage process-stage" data-catalog-item="{_clean(scene.get("catalog_item", "none"))}">'
        '<div class="process-line"></div><div class="process-steps">'
        f'{"".join(steps)}</div><div class="process-caption">{_clean(scene.get("hero") or scene.get("hero_label"))}</div></div>'
    )


def _interface(scene: dict, items: list[dict[str, str]]) -> str:
    rows = []
    for index, item in enumerate(items[:3], 1):
        rows.append(
            f'<div class="interface-row visual-item"><span class="interface-dot">{index:02d}</span>'
            f'<span>{item["label"]}</span><strong>{item["value"]}</strong></div>'
        )
    if not rows:
        rows.append(
            f'<div class="interface-row visual-item"><span class="interface-dot">01</span>'
            f'<span>State</span><strong>{_clean(scene.get("hero"))}</strong></div>'
        )
    return (
        f'<div class="visual-stage interface-stage" data-catalog-item="{_clean(scene.get("catalog_item", "none"))}">'
        '<div class="interface-window"><div class="interface-bar"><span></span><span></span><span></span>'
        f'<strong>{_clean(scene.get("hero_label") or "WORKFLOW")}</strong></div>'
        f'<div class="interface-rows">{"".join(rows)}</div></div></div>'
    )


def _media(scene: dict) -> str:
    return (
        f'<div class="visual-stage media-stage" data-catalog-item="{_clean(scene.get("catalog_item", "none"))}">'
        '<div class="media-frame"><img src="assets/brand/website-hero.webp" alt="" /></div>'
        f'<div class="media-note visual-item"><span>{_clean(scene.get("hero_label"))}</span>'
        f'<strong>{_clean(scene.get("hero") or scene.get("headline"))}</strong></div></div>'
    )


def _visual(scene: dict) -> str:
    kind = scene.get("kind", scene.get("layout", "hero"))
    items = _items(scene)
    if kind == "stat":
        return _stat(scene, items)
    if kind == "rank":
        return _hero(scene, items, rank=True)
    if kind == "compare":
        return _compare(scene, items)
    if kind == "process":
        return _process(scene, items)
    if kind == "interface":
        return _interface(scene, items)
    if kind == "media":
        return _media(scene)
    if kind == "cta":
        return ""
    return _hero(scene, items)


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
validated scene data; portrait templates own typography, spacing, graphics, and motion.
""",
        encoding="utf-8",
    )
    shutil.copyfile(ROOT / "brand" / "frame.md", project / "frame.md")
    shutil.copyfile(CATALOG / "registry.json", project / "catalog-registry.json")
    shutil.copyfile(CATALOG / "allowlist.json", project / "catalog-allowlist.json")
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
        (project / ".hyperframes" / "caption-skin.html").write_text(
            skin.read_text(encoding="utf-8") + CAPTION_OVERRIDE,
            encoding="utf-8",
        )


def write_catalog_selection(project: Path, plan: dict) -> None:
    """Record optional registry installs without making network calls during compilation."""
    commands = install_commands(plan)
    (project / "catalog-selection.json").write_text(
        json.dumps({"items": selected_items(plan), "commands": commands}, indent=2) + "\n",
        encoding="utf-8",
    )
    script = ["#!/usr/bin/env sh", "set -eu", ""]
    script.extend(commands or ["# No catalog item was selected for this plan."])
    (project / "catalog-install.sh").write_text("\n".join(script) + "\n", encoding="utf-8")


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
            f"- kind: {scene['kind']}",
            f"- variant: {scene['variant']}",
            f"- catalog_item: {scene['catalog_item']}",
            f"- motion_purpose: {scene['motion_purpose']}",
            f"- fact_ids: {json.dumps(scene.get('fact_ids', []))}",
            "- status: animated",
            f"- voiceover: {json.dumps(scene['voiceover'], ensure_ascii=False)}",
            f"- role: {'CTA' if scene['kind'] == 'cta' else 'Key_Feature'}",
            f"- type: {'cta' if scene['kind'] == 'cta' else 'feature_showcase'}",
            f"- src: compositions/frames/{scene['frame_id']}.html", "",
            f"Visual: {scene['kind']} / {scene['variant']}. Hero: {scene['hero'] or scene['headline']}", "",
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
        duration = durations.get(frame_id, scene["duration_s"])
        values = {
            "FRAME_ID": frame_id,
            "LAYOUT": scene["kind"],
            "DURATION": f"{duration:g}",
            "EYEBROW": _clean(scene.get("eyebrow")),
            "HEADLINE": _clean(scene.get("headline")),
            "SUBHEAD": _clean(scene.get("subhead")),
            "VISUAL": _visual(scene),
        }
        (target / f"{frame_id}.html").write_text(_replace(template, values), encoding="utf-8")


def snapshot_times(project: Path) -> str:
    total = 0.0
    times = []
    for duration in storyboard_durations(project).values():
        times.append(f"{total + duration / 2:.2f}")
        total += duration
    return ",".join(times) or "0"


def inject_visual_transitions(project: Path, plan: dict) -> None:
    """Move only a frame's visual group at seams; keep the scene shell still.

    The shared faceless-explainer transition injector targets the whole scene
    wrapper. That makes the background, typography, and visual travel together.
    Our portrait template exposes the `.visual` group instead, so the master
    timeline can animate that group through inherited CSS variables without
    touching the scene shell.
    """
    index_path = project / "index.html"
    source = index_path.read_text(encoding="utf-8")
    anchor = 'window.__timelines["main"] = gsap.timeline({ paused: true });'
    if anchor not in source:
        raise RuntimeError("master timeline anchor not found in index.html")

    durations = storyboard_durations(project)
    starts: dict[str, float] = {}
    total = 0.0
    for scene in plan["scenes"]:
        frame_id = scene["frame_id"]
        starts[frame_id] = total
        total += durations.get(frame_id, float(scene["duration_s"]))

    lines: list[str] = []
    for scene in plan["scenes"][1:]:
        frame_id = scene["frame_id"]
        kind = scene.get("kind", "hero")
        transition = scene.get("transition_in", "cut")
        if kind == "cta" or transition == "cut":
            continue
        host = f'"#el-{frame_id}"'
        if f'id="el-{frame_id}"' not in source:
            raise RuntimeError(f"assembled index is missing scene host {frame_id}")
        start = f"{starts[frame_id]:g}"
        if transition == "push-slide LEFT":
            lines.append(
                f'tl.fromTo({host}, {{ "--hf-visual-x": 1080 }}, '
                f'{{ "--hf-visual-x": 0, duration: 0.5, ease: "power3.inOut" }}, {start});'
            )
        elif transition == "zoom-through":
            lines.append(
                f'tl.fromTo({host}, {{ "--hf-visual-scale": 0.78, "--hf-visual-opacity": 0.35 }}, '
                f'{{ "--hf-visual-scale": 1, "--hf-visual-opacity": 1, duration: 0.42, ease: "power3.out" }}, {start});'
            )

    block = [
        anchor,
        "      // visual-only seam motion; scene shell/background stays fixed",
        '      (function () { var tl = window.__timelines["main"];',
        *[f"        {line}" for line in lines],
        f"        tl.to({{}}, {{ duration: {total:g} }}, 0);",
        "      })();",
    ]
    source = source.replace(anchor, "\n".join(block), 1)
    index_path.write_text(source, encoding="utf-8")


def hide_cta_captions(project: Path, plan: dict) -> None:
    """Fade the global caption track out for a caption-free CTA hold."""
    cta_index = next((i for i, scene in enumerate(plan["scenes"]) if scene["kind"] == "cta"), None)
    if cta_index is None:
        return
    durations = storyboard_durations(project)
    start = sum(durations.get(scene["frame_id"], scene["duration_s"]) for scene in plan["scenes"][:cta_index])
    index_path = project / "index.html"
    source = index_path.read_text(encoding="utf-8")
    marker = 'var tl = window.__timelines["main"];'
    if marker not in source or 'id="el-captions"' not in source or 'tl.to("#el-captions"' in source:
        return
    cue = max(0, start - 0.15)
    fade = f'        tl.to("#el-captions", {{ opacity: 0, duration: 0.15, ease: "power1.out" }}, {cue:g});\n'
    index_path.write_text(source.replace(marker, marker + "\n" + fade, 1), encoding="utf-8")

"""End-to-end orchestration; creative work remains in plans and templates."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from .audio import build_audio, build_captions
from .composition import (
    add_frame_ids,
    hide_cta_captions,
    inject_visual_transitions,
    render_frames,
    snapshot_times,
    write_catalog_selection,
    write_brief,
    write_script,
    write_storyboard,
)
from .planning import load_plan, make_plan
from .runtime import check_tools, hyperframes, init_project, next_project, node
from .research import as_notes, get_research, load_research, write_artifacts

# Orchestrate research, planning, composition, audio, validation, and rendering.
def build_video(
    *,
    topic: str,
    source_path: Path | None,
    research_path: Path | None,
    plan_path: Path | None,
    refresh_research: bool,
    audience: str,
    destination: str,
    length: int,
    frame_count: int,
    voice: str,
    model: str,
    subscription: bool,
    audio: bool,
    render: bool,
) -> dict:
    if not 3 <= frame_count <= 10:
        raise ValueError("frames must be between 3 and 10")

    check_tools()
    project = next_project(topic)
    init_project(project, destination)
    write_brief(project, topic, destination, length, voice)

    research = None
    research_cache = None
    research_reused = False
    model_calls = 0

    if plan_path:
        if refresh_research:
            raise ValueError("--refresh-research cannot be used with --plan")
        plan = load_plan(plan_path, frame_count)
    else:
        if research_path:
            if refresh_research:
                raise ValueError("--refresh-research cannot be used with --research")
            research = load_research(research_path)
            research_cache = research_path
            research_reused = True
            notes = as_notes(research)
        elif source_path:
            if not source_path.is_file():
                raise ValueError(f"source notes do not exist: {source_path}")
            notes = source_path.read_text(encoding="utf-8")
            if not notes.strip():
                raise ValueError("source notes are empty")
        else:
            research, research_cache, research_reused = get_research(
                topic, audience, model, subscription, refresh_research
            )
            notes = as_notes(research)
            model_calls += 0 if research_reused else 1

        known_fact_ids = {fact["id"] for fact in research["facts"]} if research else None
        plan = make_plan(topic, notes, frame_count, length, model, subscription, known_fact_ids)
        model_calls += 1

    if research:
        write_artifacts(project, research)

    add_frame_ids(plan)
    (project / "plan.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
    write_catalog_selection(project, plan)
    write_storyboard(project, plan, length)
    write_script(project, plan, voice)

    if audio:
        build_audio(project, voice)
    render_frames(project, plan)

    if audio:
        build_captions(project)
    node("assemble-index", "--storyboard", "./STORYBOARD.md", "--hyperframes", ".", cwd=project)
    inject_visual_transitions(project, plan)
    hide_cta_captions(project, plan)

    hyperframes("check", cwd=project, timeout=2400)
    hyperframes("snapshot", "--at", snapshot_times(project), cwd=project, timeout=1800)

    result: dict[str, object] = {
        "project": str(project),
        "plan": str(project / "plan.json"),
        "contact_sheet": str(project / "snapshots" / "contact-sheet.jpg"),
        "model_calls": model_calls,
    }

    if research_cache:
        result.update(
            research=str(project / "research.json"),
            research_cache=str(research_cache),
            research_reused=research_reused,
        )

    if render:
        output = project / "renders" / "video.mp4"
        hyperframes(
            "render", "--skill", "faceless-explainer", "--quality", "high",
            "--output", "renders/video.mp4", cwd=project, timeout=7200,
        )
        if not output.is_file() or not output.stat().st_size:
            raise RuntimeError("render completed without a usable video")
        result["video"] = str(output)
        if shutil.which("ffprobe"):
            done = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(output)],
                capture_output=True, text=True, check=True,
            )
            result["duration_s"] = round(float(done.stdout), 2)
            
    return result

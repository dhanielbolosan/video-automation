"""One structured AI decision: story, narration, layout, and template content."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from string import Template

import anthropic

from .project import ROOT

LAYOUTS = ("hero", "rank", "comparison", "process", "interface", "cta")
TRANSITIONS = ("cut", "push-slide LEFT", "zoom-through")


def schema(frame_count: int) -> dict:
    item = {
        "type": "object",
        "additionalProperties": False,
        "required": ["label", "value"],
        "properties": {"label": {"type": "string"}, "value": {"type": "string"}},
    }
    scene = {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "title", "slug", "voiceover", "duration_s", "transition_in", "layout",
            "eyebrow", "headline", "subhead", "hero", "hero_label", "items",
        ],
        "properties": {
            "title": {"type": "string", "minLength": 2},
            "slug": {"type": "string", "pattern": "^[a-z][a-z0-9-]*$"},
            "voiceover": {"type": "string", "minLength": 8},
            "duration_s": {"type": "number", "minimum": 2},
            "transition_in": {"type": "string", "enum": list(TRANSITIONS)},
            "layout": {"type": "string", "enum": list(LAYOUTS)},
            "eyebrow": {"type": "string"},
            "headline": {"type": "string", "minLength": 2},
            "subhead": {"type": "string"},
            "hero": {"type": "string"},
            "hero_label": {"type": "string"},
            "items": {"type": "array", "minItems": 0, "maxItems": 3, "items": item},
        },
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["message", "audience", "music", "scenes"],
        "properties": {
            "message": {"type": "string", "minLength": 8},
            "audience": {"type": "string", "minLength": 4},
            "music": {"type": "string"},
            "scenes": {
                "type": "array", "minItems": frame_count, "maxItems": frame_count,
                "items": scene,
            },
        },
    }


def load_plan(path: Path, frame_count: int) -> dict:
    plan = json.loads(path.read_text(encoding="utf-8"))
    validate(plan, frame_count)
    return plan


def validate(plan: dict, frame_count: int) -> None:
    scenes = plan.get("scenes")
    if not isinstance(scenes, list) or len(scenes) != frame_count:
        raise ValueError(f"plan must contain exactly {frame_count} scenes")
    for index, scene in enumerate(scenes, 1):
        if scene.get("layout") not in LAYOUTS:
            raise ValueError(f"scene {index} has unsupported layout {scene.get('layout')!r}")
        if not re.fullmatch(r"[a-z][a-z0-9-]*", scene.get("slug", "")):
            raise ValueError(f"scene {index} has an invalid slug")
        if len(scene.get("items", [])) > 3:
            raise ValueError(f"scene {index} has more than three items")
    scenes[0]["transition_in"] = "cut"
    scenes[-1].update(
        layout="cta",
        eyebrow="PŪPŪKAHI TECH",
        headline="Follow @pupukahi_tech",
        subhead="Practical technology for local people and small businesses.",
        hero="",
        hero_label="",
        items=[],
    )


def make_plan(topic: str, notes: str, frame_count: int, length: int, model: str, subscription: bool) -> dict:
    prompt = Template((ROOT / "video_pipeline" / "prompts" / "plan.md").read_text(encoding="utf-8")).substitute(
        topic=topic,
        notes=notes,
        frame_count=frame_count,
        length=length,
        seconds=round(length / frame_count, 1),
    )
    plan_schema = schema(frame_count)
    if subscription:
        if not shutil.which("claude"):
            raise RuntimeError("claude CLI is not installed")
        command = [
            "claude", "-p", prompt, "--model", model, "--output-format", "json",
            "--json-schema", json.dumps(plan_schema, separators=(",", ":")),
            "--no-session-persistence", "--permission-mode", "dontAsk", "--tools", "",
        ]
        done = subprocess.run(command, capture_output=True, text=True, timeout=1800)
        if done.returncode:
            raise RuntimeError((done.stdout + "\n" + done.stderr)[-4000:])
        payload = json.loads(done.stdout[done.stdout.index("{"):])
        raw = payload.get("result", "")
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise RuntimeError("Claude returned no plan JSON")
        plan = json.loads(match.group(0))
    else:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=model,
            max_tokens=12000,
            messages=[{"role": "user", "content": prompt}],
            output_config={"format": {"type": "json_schema", "schema": plan_schema}},
        )
        raw = "".join(block.text for block in response.content if block.type == "text")
        plan = json.loads(raw)
    validate(plan, frame_count)
    return plan

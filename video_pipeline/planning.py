"""One bounded AI decision: content and an approved scene recipe, never code."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from string import Template

import anthropic

from .catalog import catalog_choices, catalog_item
from .project import ROOT

SCENE_KINDS = ("hero", "stat", "rank", "compare", "process", "interface", "media", "cta")
VARIANTS = (
    "headline", "metric", "ranked-bars", "split", "steps", "screen", "split-media", "follow", "default",
)
MOTION_PURPOSES = ("orient", "prove", "compare", "sequence", "demonstrate", "reveal", "brand_follow")
TRANSITIONS = ("cut", "push-slide LEFT", "zoom-through")

LEGACY_KIND_MAP = {
    "tool-stack": "hero",
    "prompt-reply": "interface",
    "format-carousel": "compare",
    "editor-timeline": "interface",
    "constellation": "process",
    "trigger-action": "process",
    "cta": "cta",
}
LAYOUT_MAP = {"comparison": "compare"}
DEFAULT_VARIANT = {
    "hero": "headline",
    "stat": "metric",
    "rank": "ranked-bars",
    "compare": "split",
    "process": "steps",
    "interface": "screen",
    "media": "split-media",
    "cta": "follow",
}
DEFAULT_MOTION = {
    "hero": "orient",
    "stat": "prove",
    "rank": "compare",
    "compare": "compare",
    "process": "sequence",
    "interface": "demonstrate",
    "media": "reveal",
    "cta": "brand_follow",
}


def schema(frame_count: int) -> dict:
    item = {
        "type": "object",
        "additionalProperties": False,
        "required": ["label", "value"],
        "properties": {
            "label": {"type": "string", "minLength": 1, "maxLength": 42},
            "value": {"type": "string", "minLength": 1, "maxLength": 72},
        },
    }
    scene = {
        "type": "object",
        "additionalProperties": False,
        "allOf": [
            {
                "if": {"properties": {"kind": {"const": "compare"}}, "required": ["kind"]},
                "then": {"properties": {"items": {"minItems": 2, "maxItems": 2}}},
            },
            {
                "if": {"properties": {"kind": {"const": "process"}}, "required": ["kind"]},
                "then": {"properties": {"items": {"minItems": 3, "maxItems": 3}}},
            },
        ],
        "required": [
            "title", "slug", "voiceover", "duration_s", "transition_in", "kind", "variant",
            "catalog_item", "motion_purpose", "fact_ids", "eyebrow", "headline", "subhead", "hero", "hero_label", "items",
        ],
        "properties": {
            "title": {"type": "string", "minLength": 2, "maxLength": 80},
            "slug": {"type": "string", "pattern": "^[a-z][a-z0-9-]*$"},
            "voiceover": {"type": "string", "minLength": 8, "maxLength": 420},
            "duration_s": {"type": "number", "minimum": 2, "maximum": 30},
            "transition_in": {"type": "string", "enum": list(TRANSITIONS)},
            "kind": {"type": "string", "enum": list(SCENE_KINDS)},
            "variant": {"type": "string", "enum": list(VARIANTS)},
            "catalog_item": {"type": "string", "enum": catalog_choices()},
            "motion_purpose": {"type": "string", "enum": list(MOTION_PURPOSES)},
            "fact_ids": {"type": "array", "maxItems": 6, "items": {"type": "string", "pattern": "^F[1-9][0-9]*$"}},
            "eyebrow": {"type": "string", "maxLength": 48},
            "headline": {"type": "string", "minLength": 2, "maxLength": 64},
            "subhead": {"type": "string", "maxLength": 110},
            "hero": {"type": "string", "maxLength": 72},
            "hero_label": {"type": "string", "maxLength": 64},
            "items": {"type": "array", "minItems": 0, "maxItems": 3, "items": item},
        },
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["message", "audience", "music", "scenes"],
        "properties": {
            "message": {"type": "string", "minLength": 8, "maxLength": 220},
            "audience": {"type": "string", "minLength": 4, "maxLength": 120},
            "music": {"type": "string", "maxLength": 120},
            "scenes": {
                "type": "array", "minItems": frame_count, "maxItems": frame_count,
                "items": scene,
            },
        },
    }


def _kind_for(scene: dict) -> str:
    raw_kind = str(scene.get("kind") or "").strip()
    if raw_kind in SCENE_KINDS:
        return raw_kind
    layout = LAYOUT_MAP.get(str(scene.get("layout") or "").strip(), str(scene.get("layout") or "").strip())
    if layout in SCENE_KINDS:
        return layout
    return LEGACY_KIND_MAP.get(str(scene.get("visual_kind") or "").strip(), "hero")


def _normalize_scene(scene: dict) -> None:
    for field in ("title", "voiceover", "eyebrow", "headline", "subhead", "hero", "hero_label"):
        if isinstance(scene.get(field), str):
            scene[field] = scene[field].replace("—", " - ").replace("–", " - ")
    kind = _kind_for(scene)
    scene["kind"] = kind
    scene["layout"] = kind
    scene["variant"] = scene.get("variant") if scene.get("variant") in VARIANTS else DEFAULT_VARIANT[kind]
    scene["catalog_item"] = catalog_item(scene.get("catalog_item"))
    scene["motion_purpose"] = (
        scene.get("motion_purpose") if scene.get("motion_purpose") in MOTION_PURPOSES else DEFAULT_MOTION[kind]
    )
    scene["transition_in"] = scene.get("transition_in") if scene.get("transition_in") in TRANSITIONS else "push-slide LEFT"
    scene["items"] = scene.get("items") if isinstance(scene.get("items"), list) else []
    scene["fact_ids"] = [str(value) for value in scene.get("fact_ids", [])] if isinstance(scene.get("fact_ids"), list) else []


def load_plan(path: Path, frame_count: int) -> dict:
    plan = json.loads(path.read_text(encoding="utf-8"))
    validate(plan, frame_count)
    return plan


def validate(plan: dict, frame_count: int, known_fact_ids: set[str] | None = None) -> None:
    if not isinstance(plan, dict):
        raise ValueError("plan must be an object")
    scenes = plan.get("scenes")
    if not isinstance(scenes, list) or len(scenes) != frame_count:
        raise ValueError(f"plan must contain exactly {frame_count} scenes")
    slugs: set[str] = set()
    for index, scene in enumerate(scenes, 1):
        if not isinstance(scene, dict):
            raise ValueError(f"scene {index} must be an object")
        _normalize_scene(scene)
        if not re.fullmatch(r"[a-z][a-z0-9-]*", str(scene.get("slug", ""))):
            raise ValueError(f"scene {index} has an invalid slug")
        if scene["slug"] in slugs:
            raise ValueError(f"scene {index} repeats slug {scene['slug']!r}")
        slugs.add(scene["slug"])
        if not isinstance(scene.get("voiceover"), str) or len(scene["voiceover"].strip()) < 8:
            raise ValueError(f"scene {index} has unusable voiceover text")
        if not isinstance(scene.get("duration_s"), (int, float)) or scene["duration_s"] < 2:
            raise ValueError(f"scene {index} has an invalid duration")
        if any("—" in str(scene.get(field, "")) for field in ("title", "voiceover", "eyebrow", "headline", "subhead", "hero", "hero_label")):
            raise ValueError(f"scene {index} uses an em dash; use plain punctuation")
        if scene["kind"] != "cta" and len(str(scene.get("headline", "")).split()) > 6:
            raise ValueError(f"scene {index} headline must be six words or fewer")
        if len(str(scene.get("subhead", "")).split()) > 12:
            raise ValueError(f"scene {index} subhead must be twelve words or fewer")
        if len(scene["items"]) > 3:
            raise ValueError(f"scene {index} has more than three items")
        if known_fact_ids is not None:
            unknown = set(scene["fact_ids"]) - known_fact_ids
            if unknown:
                raise ValueError(f"scene {index} cites unknown research facts: {', '.join(sorted(unknown))}")
        if scene["kind"] == "compare" and len(scene["items"]) != 2:
            raise ValueError(f"scene {index} compare scenes need exactly two items")
        if scene["kind"] == "process" and len(scene["items"]) != 3:
            raise ValueError(f"scene {index} process scenes need exactly three items")
        for item in scene["items"]:
            if not isinstance(item, dict) or not str(item.get("label", "")).strip() or not str(item.get("value", "")).strip():
                raise ValueError(f"scene {index} has an incomplete evidence item")
    scenes[0]["transition_in"] = "cut"
    zooms = 0
    for scene in scenes:
        if scene["transition_in"] == "zoom-through":
            zooms += 1
            if zooms > 1:
                scene["transition_in"] = "push-slide LEFT"
    scenes[-1].update(
        layout="cta",
        kind="cta",
        variant="follow",
        catalog_item="none",
        motion_purpose="brand_follow",
        eyebrow="",
        headline="FOLLOW @pupukahi_tech",
        subhead="",
        hero="",
        hero_label="",
        items=[],
        fact_ids=[],
    )
    referenced_facts = {fact_id for scene in scenes[:-1] for fact_id in scene["fact_ids"]}
    if known_fact_ids and not referenced_facts:
        raise ValueError("the plan does not cite any researched facts")


def make_plan(
    topic: str,
    notes: str,
    frame_count: int,
    length: int,
    model: str,
    subscription: bool,
    known_fact_ids: set[str] | None = None,
) -> dict:
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
        try:
            payload = json.loads(done.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Claude returned invalid JSON") from exc
        if isinstance(payload.get("structured_output"), dict):
            plan = payload["structured_output"]
        elif isinstance(payload.get("result"), dict):
            plan = payload["result"]
        else:
            raw = str(payload.get("result", ""))
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if not match:
                raise RuntimeError("Claude returned no plan JSON")
            plan = json.loads(match.group(0))
    else:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=model,
            max_tokens=6000,
            messages=[{"role": "user", "content": prompt}],
            output_config={"format": {"type": "json_schema", "schema": plan_schema}},
        )
        raw = "".join(block.text for block in response.content if block.type == "text")
        plan = json.loads(raw)
    validate(plan, frame_count, known_fact_ids)
    return plan

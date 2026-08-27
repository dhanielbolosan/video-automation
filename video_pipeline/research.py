"""Bounded, source-backed topic research with a human-readable JSON cache."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from string import Template
from urllib.parse import urlparse

import anthropic

from .project import ROOT, slugify

RESEARCH_DIR = ROOT / "research"
PROMPT = ROOT / "video_pipeline" / "prompts" / "research.md"


def schema() -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["facts"],
        "properties": {
            "facts": {
                "type": "array",
                "minItems": 1,
                "maxItems": 6,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["claim", "detail", "source_title", "source_url"],
                    "properties": {
                        "claim": {"type": "string", "minLength": 8, "maxLength": 240},
                        "detail": {"type": "string", "minLength": 8, "maxLength": 500},
                        "source_title": {"type": "string", "minLength": 2, "maxLength": 180},
                        "source_url": {"type": "string", "minLength": 12, "maxLength": 500},
                    },
                },
            }
        },
    }


def cache_path(topic: str) -> Path:
    return RESEARCH_DIR / f"{slugify(topic)}.json"


def _text(value: object) -> str:
    return " ".join(str(value or "").split())


def _usable_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and "." in parsed.netloc


def _url_key(value: str) -> str:
    parsed = urlparse(value)
    return parsed._replace(fragment="").geturl().rstrip("/")


def validate(
    payload: dict,
    expected_topic: str | None = None,
    allowed_urls: set[str] | None = None,
) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("research must be an object")
    topic = _text(payload.get("topic") or expected_topic)
    if not topic:
        raise ValueError("research is missing its topic")
    if expected_topic and topic.casefold() != _text(expected_topic).casefold():
        raise ValueError(f"research topic {topic!r} does not match {expected_topic!r}")

    allowed = {_url_key(url) for url in allowed_urls} if allowed_urls is not None else None
    facts = []
    seen: set[tuple[str, str]] = set()
    for raw in payload.get("facts", []):
        if not isinstance(raw, dict):
            continue
        claim = _text(raw.get("claim"))
        detail = _text(raw.get("detail"))
        title = _text(raw.get("source_title"))
        url = _text(raw.get("source_url"))
        key = (claim.casefold(), url)
        if (
            not claim or not detail or not title or not _usable_url(url) or key in seen
            or (allowed is not None and _url_key(url) not in allowed)
        ):
            continue
        seen.add(key)
        facts.append(
            {"id": f"F{len(facts) + 1}", "claim": claim, "detail": detail, "source_title": title, "source_url": url}
        )
        if len(facts) == 6:
            break
    if not facts:
        raise ValueError("research returned no usable sourced facts")
    return {
        "version": 1,
        "topic": topic,
        "audience": _text(payload.get("audience")),
        "researched_at": _text(payload.get("researched_at")) or datetime.now(timezone.utc).date().isoformat(),
        "model": _text(payload.get("model")),
        "facts": facts,
    }


def load(path: Path, expected_topic: str | None = None) -> dict:
    if not path.is_file():
        raise ValueError(f"research file does not exist: {path}")
    return validate(json.loads(path.read_text(encoding="utf-8")), expected_topic)


def _result_json(raw: str, label: str) -> dict:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise RuntimeError(f"{label} returned no JSON")
        payload = json.loads(match.group(0))
    if isinstance(payload, dict) and isinstance(payload.get("structured_output"), dict):
        return payload["structured_output"]
    if isinstance(payload, dict) and isinstance(payload.get("result"), dict):
        return payload["result"]
    if isinstance(payload, dict) and isinstance(payload.get("result"), str):
        return _result_json(payload["result"], label)
    if not isinstance(payload, dict):
        raise RuntimeError(f"{label} returned unusable JSON")
    return payload


def _prompt(topic: str, audience: str) -> str:
    return Template(PROMPT.read_text(encoding="utf-8")).substitute(
        topic=topic,
        audience=audience,
        today=datetime.now(timezone.utc).date().isoformat(),
        schema=json.dumps(schema(), separators=(",", ":")),
    )


def _research_cli(topic: str, audience: str, model: str) -> tuple[dict, None]:
    if not shutil.which("claude"):
        raise RuntimeError("claude CLI is not installed")
    command = [
        "claude", "-p", _prompt(topic, audience), "--model", model,
        "--output-format", "json", "--json-schema", json.dumps(schema(), separators=(",", ":")),
        "--no-session-persistence", "--permission-mode", "dontAsk",
        "--tools", "WebSearch", "--allowedTools", "WebSearch",
        "--max-budget-usd", os.environ.get("VIDEO_RESEARCH_BUDGET_USD", "0.75"),
    ]
    done = subprocess.run(command, capture_output=True, text=True, timeout=900)
    if done.returncode:
        raise RuntimeError((done.stdout + "\n" + done.stderr)[-4000:])
    return _result_json(done.stdout, "Claude research"), None


def _research_api(topic: str, audience: str, model: str) -> tuple[dict, set[str]]:
    response = anthropic.Anthropic().messages.create(
        model=model,
        max_tokens=4000,
        messages=[{"role": "user", "content": _prompt(topic, audience)}],
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 5}],
    )
    urls = {
        result.url
        for block in response.content
        if block.type == "web_search_tool_result" and isinstance(block.content, list)
        for result in block.content
        if result.type == "web_search_result"
    }
    raw = "".join(block.text for block in response.content if block.type == "text")
    return _result_json(raw, "Anthropic research"), urls


def get(topic: str, audience: str, model: str, subscription: bool, refresh: bool = False) -> tuple[dict, Path, bool]:
    path = cache_path(topic)
    if path.is_file() and not refresh:
        cached = load(path, topic)
        if not cached["audience"] or cached["audience"].casefold() == _text(audience).casefold():
            return cached, path, True
    raw, urls = _research_cli(topic, audience, model) if subscription else _research_api(topic, audience, model)
    payload = validate({**raw, "topic": topic, "audience": audience, "model": model}, topic, urls)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload, path, False


def as_notes(payload: dict) -> str:
    lines = [f"# Verified research — {payload['topic']}", ""]
    for fact in payload["facts"]:
        lines += [
            f"## [{fact['id']}] {fact['claim']}", "",
            fact["detail"], "",
            f"Source: {fact['source_title']} — {fact['source_url']}", "",
        ]
    return "\n".join(lines)


def write_artifacts(project: Path, payload: dict) -> None:
    (project / "research.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    lines = [f"# Sources — {payload['topic']}", "", f"Researched: {payload['researched_at']}", ""]
    for fact in payload["facts"]:
        lines += [f"- **{fact['id']}: {fact['claim']}**", f"  [{fact['source_title']}]({fact['source_url']})", ""]
    (project / "SOURCES.md").write_text("\n".join(lines), encoding="utf-8")

"""Allowlisted HyperFrames graphics and their reproducible install commands."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ALLOWLIST = Path(__file__).with_name("allowlist.json")
NONE = "none"

@lru_cache(maxsize=1)
def _items() -> dict[str, dict]:
    payload = json.loads(ALLOWLIST.read_text(encoding="utf-8"))
    return {item["name"]: item for item in payload.get("items", [])}

def catalog_choices() -> list[str]:
    return [NONE, *_items()]

def catalog_item(value: object) -> str:
    name = str(value or NONE).strip()
    if name != NONE and name not in _items():
        raise ValueError(f"catalog item is not allowlisted: {name!r}")

    return name

def selected_items(plan: dict) -> list[str]:
    selected: list[str] = []

    for scene in plan.get("scenes", []):
        name = catalog_item(scene.get("catalog_item"))
        if name != NONE and name not in selected:
            selected.append(name)

    return selected

def install_commands(plan: dict) -> list[str]:
    version = json.loads(ALLOWLIST.read_text(encoding="utf-8")).get("hyperframes", "0.8.15")
    return [
        f"npx hyperframes@{version} add {name} --dir . --force --no-clipboard"
        for name in selected_items(plan)
    ]

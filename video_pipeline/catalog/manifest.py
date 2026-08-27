"""Small, local catalog policy layer.

The renderer does not copy catalog demos into the source tree. A plan may name
one approved registry item, and the generated project records the exact command
needed to install it. Layout and motion remain owned by our portrait templates.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ALLOWLIST = Path(__file__).with_name("allowlist.json")
NONE = "none"


@lru_cache(maxsize=1)
def _items() -> dict[str, dict]:
    payload = json.loads(ALLOWLIST.read_text(encoding="utf-8"))
    return {item["name"]: item for item in payload.get("items", [])}


def catalog_choices() -> list[str]:
    """Return schema-safe item names, including the intentional no-catalog choice."""
    return [NONE, *_items()]


def catalog_item(value: object) -> str:
    """Validate one plan selection and normalize an empty value to ``none``."""
    name = str(value or NONE).strip()
    if name == NONE:
        return NONE
    if name not in _items():
        raise ValueError(f"catalog item is not allowlisted: {name!r}")
    return name


def selected_items(plan: dict) -> list[str]:
    """Return unique approved catalog IDs in scene order."""
    result: list[str] = []
    for scene in plan.get("scenes", []):
        name = catalog_item(scene.get("catalog_item"))
        if name != NONE and name not in result:
            result.append(name)
    return result


def install_commands(plan: dict) -> list[str]:
    """Return reproducible registry commands for a generated project."""
    version = json.loads(ALLOWLIST.read_text(encoding="utf-8")).get("hyperframes", "0.8.15")
    return [
        f"npx hyperframes@{version} add {name} --dir . --force --no-clipboard"
        for name in selected_items(plan)
    ]

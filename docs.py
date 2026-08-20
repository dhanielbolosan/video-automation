"""Reads the installed HyperFrames skills, so the prompts quote them.

Every vocabulary handed to a model — blueprint ids, motion rule names, the frame
worker's role contract, a frame's packet — has one source of truth: the skill
files on disk. Nothing here paraphrases them. Upgrade the skills and the prompts
and schemas follow, because they are read at import time rather than copied.
"""

from __future__ import annotations

import functools
import re
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parent
SKILLS = ROOT / ".agents" / "skills"
FACELESS = SKILLS / "faceless-explainer"
ANIMATION = SKILLS / "hyperframes-animation"

# `frame-packets.mjs` inlines a frame's whole blueprint body plus every rule
# recipe it cites, then hard-fails over this many bytes. It is a default
# parameter of the script with no CLI flag, so the caller has to predict the size
# and trim the citation list before dispatch.
PACKET_LIMIT = 48_000


def _read(path: Path) -> str:
    if not path.is_file():
        raise RuntimeError(
            f"Missing skill file {path}. Install the skills with "
            "`npx skills add heygen-com/hyperframes --all --full-depth`."
        )
    return path.read_text(encoding="utf-8")


def script(name: str) -> str:
    """Absolute path to one of the workflow's own Node scripts."""
    path = FACELESS / "scripts" / f"{name}.mjs"
    if not path.is_file():
        raise RuntimeError(f"Missing workflow script {path}.")
    return str(path)


@functools.lru_cache(maxsize=1)
def blueprints() -> dict[str, dict[str, str]]:
    """The proven shapes: id → {roles, duration, summary}.

    A blueprint is a product-agnostic, time-coded shot template with `[slots]`
    and one named signature move, reverse-engineered from real clips. It encodes
    a whole shot across its full duration, so instantiating one keeps content
    arriving instead of freezing after the first second.
    """
    text = _read(ANIMATION / "blueprints-index.md")
    found = {}
    for match in re.finditer(
        r'<blueprint id="([a-z0-9-]+)"\s+roles="([^"]*)"\s+duration="([^"]*)">\s*(.*?)\s*</blueprint>',
        text,
        re.DOTALL,
    ):
        bid, roles, duration, body = match.groups()
        found[bid] = {
            "roles": roles,
            "duration": duration,
            "summary": " ".join(body.split()),
        }
    if not found:
        raise RuntimeError("Parsed no blueprints out of blueprints-index.md.")
    return found


def blueprint_ids() -> list[str]:
    return sorted(blueprints())


@functools.lru_cache(maxsize=1)
def rule_names() -> tuple[str, ...]:
    """Valid atomic motion rule names. The skill's instruction is explicit — do
    not invent motion names — so these become a schema enum."""
    text = _read(ANIMATION / "rules-index.md")
    names = sorted(set(re.findall(r'<([a-z0-9][a-z0-9-]*) path="rules/', text)))
    if not names:
        raise RuntimeError("Parsed no motion rules out of rules-index.md.")
    return tuple(names)


def blueprint_menu() -> str:
    return "\n".join(
        f"- `{bid}` (roles: {meta['roles']}; {meta['duration']})\n  {meta['summary']}"
        for bid, meta in sorted(blueprints().items())
    )


def rule_menu() -> str:
    text = _read(ANIMATION / "rules-index.md")
    lines = []
    for name, body in re.findall(
        r'<([a-z0-9][a-z0-9-]*) path="rules/[^"]*">(.*?)</\1>', text, re.DOTALL
    ):
        # The trailing "Tags: …" is for retrieval, not for the model's choice.
        summary = re.split(r"\s*Tags:", " ".join(body.split()))[0]
        lines.append(f"- `{name}` — {summary}")
    return "\n".join(lines)


def blueprint_bytes(blueprint_id: str) -> int:
    path = ANIMATION / "blueprints" / f"{blueprint_id}.md"
    return path.stat().st_size if path.is_file() else 0


def rule_bytes(rule: str) -> int:
    path = ANIMATION / "rules" / f"{rule}.md"
    return path.stat().st_size if path.is_file() else 0


def frame_md(project: Path) -> str:
    """The project's design system, written by `build-frame.mjs`."""
    return _read(project / "frame.md")


def worker_role(project: Path) -> str:
    """`_role.md` — the frame-worker contract, assembled by `frame-packets.mjs`
    from the core contract plus this workflow's delta, verbatim. A worker starts
    from exactly this document plus one packet."""
    return _read(project / ".hyperframes" / "frame-packets" / "_role.md")


def frame_packet(project: Path, frame_id: str) -> str:
    """One frame's bounded packet: its storyboard block, its blueprint body, and
    every rule recipe it cited — already inlined by the packet builder."""
    return _read(project / ".hyperframes" / "frame-packets" / f"{frame_id}.md")


def prompt(name: str, **values: object) -> str:
    """One prompt, loaded from `prompts/<name>.md`.

    `string.Template` rather than an f-string so the prompts live on disk as
    readable markdown you can edit without touching Python, and `$name` cannot
    collide with the braces in the CSS and GSAP the prompts quote. Substitution
    is strict: a missing value raises instead of shipping a literal `${hole}`.
    """
    return Template(_read(ROOT / "prompts" / f"{name}.md")).substitute(values)

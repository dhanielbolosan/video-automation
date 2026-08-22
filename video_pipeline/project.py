"""Project paths, environment loading, and subprocess boundaries."""

from __future__ import annotations

import os
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "output"
SKILL = ROOT / ".agents" / "skills" / "faceless-explainer"


def load_dotenv(path: Path = ROOT / ".env") -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip("'\"")
        if value:
            os.environ.setdefault(key.strip(), value)


def slugify(value: str, limit: int = 60) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:limit].rstrip("-")
    if not slug:
        raise ValueError("topic must contain a letter or number")
    return slug


def next_project(topic: str) -> Path:
    base = slugify(topic)
    version = 1
    while (OUTPUT / f"{base}-v{version}").exists():
        version += 1
    incomplete = OUTPUT / f"{base}-v{version - 1}"
    if version > 1 and (incomplete / "hyperframes.json").is_file() and not (incomplete / "plan.json").exists():
        return incomplete
    return OUTPUT / f"{base}-v{version}"


def run(command: list[str], cwd: Path, timeout: int = 3600, env: dict[str, str] | None = None) -> str:
    print(f"run: {' '.join(command[:4])}…", flush=True)
    done = subprocess.run(
        command,
        cwd=cwd,
        env={**os.environ, **(env or {})},
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if done.returncode:
        raise RuntimeError((done.stdout + "\n" + done.stderr)[-8000:])
    return done.stdout


def node(script: str, *args: str, cwd: Path, timeout: int = 3600) -> str:
    path = SKILL / "scripts" / f"{script}.mjs"
    if not path.is_file():
        raise RuntimeError(f"missing HyperFrames workflow script: {path}")
    return run(["node", str(path), *args], cwd, timeout)


def _cached_hyperframes() -> Path | None:
    """Use an installed CLI directly so offline runs never wait on npm."""
    candidates = []
    for package in (Path.home() / ".npm/_npx").glob("*/node_modules/hyperframes/package.json"):
        try:
            version = tuple(int(part) for part in json.loads(package.read_text())["version"].split("."))
        except (KeyError, ValueError, json.JSONDecodeError):
            continue
        binary = package.parent / "bin/hyperframes.mjs"
        if binary.is_file():
            candidates.append((version, binary))
    return max(candidates, default=((), None))[1]


def hyperframes(*args: str, cwd: Path, timeout: int = 3600) -> str:
    if binary := _cached_hyperframes():
        return run(["node", str(binary), *args], cwd, timeout)
    return run(["npx", "--yes", "hyperframes", *args], cwd, timeout)


def check_tools() -> None:
    missing = [name for name in ("node", "npx", "ffmpeg") if not shutil.which(name)]
    if missing:
        raise RuntimeError(f"missing required tools: {', '.join(missing)}")


def init_project(project: Path, destination: str) -> None:
    if (project / "hyperframes.json").is_file():
        return
    project.parent.mkdir(parents=True, exist_ok=True)
    resolution = "portrait" if destination in {"tiktok", "instagram-reels", "youtube-shorts"} else destination
    hyperframes(
        "init", project.name, "--example", "blank", "--resolution", resolution,
        "--skill", "faceless-explainer", "--non-interactive",
        cwd=project.parent,
        timeout=900,
    )

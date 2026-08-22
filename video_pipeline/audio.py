"""Local Kokoro narration, Whisper timings, captions, and assembly."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from .project import node


def build_audio(project: Path, voice: str) -> None:
    env = {
        "HYPERFRAMES_PYTHON": sys.executable,
        "HEYGEN_API_KEY": "",
        "HYPERFRAMES_API_KEY": "",
        "ELEVENLABS_API_KEY": "",
        "HEYGEN_CONFIG_DIR": str(project / ".local-audio"),
    }
    whisper = Path.home() / ".cache/hyperframes/whisper/whisper.cpp/build/bin/whisper-cli"
    if whisper.is_file():
        env["HYPERFRAMES_WHISPER_PATH"] = str(whisper)
    old = {key: os.environ.get(key) for key in env}
    os.environ.update(env)
    try:
        output = node(
            "audio", "--script", "./SCRIPT.md", "--storyboard", "./STORYBOARD.md",
            "--hyperframes", ".", "--out", "./audio_meta.json", "--voice", voice,
            cwd=project,
        )
        meta = project / "audio_meta.json"
        voices = json.loads(meta.read_text(encoding="utf-8")).get("voices", []) if meta.is_file() else []
        if not voices:
            raise RuntimeError(f"Kokoro produced no narration:\n{output[-3000:]}")
        node("audio", "sync-durations", "--audio-meta", "./audio_meta.json", "--storyboard", "./STORYBOARD.md", cwd=project)
    finally:
        for key, value in old.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def build_captions(project: Path) -> None:
    node(
        "captions", "build", "--storyboard", "./STORYBOARD.md", "--audio-meta", "./audio_meta.json",
        "--hyperframes", ".", "--out", "./caption_groups.json", cwd=project, timeout=1200,
    )

"""Thin command-line runner for the video pipeline."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from video_pipeline.pipeline import build_video
from video_pipeline.project import ROOT, load_dotenv


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Build a template-driven HyperFrames explainer.")
    parser.add_argument("--topic", default="Five affordable AI tools for small business")
    parser.add_argument("--source", type=Path, default=ROOT / "notes" / "example.md")
    parser.add_argument("--plan", type=Path, help="Use an existing JSON plan; makes no model calls.")
    parser.add_argument("--destination", default="tiktok", choices=("tiktok", "instagram-reels", "youtube-shorts"))
    parser.add_argument("--length", type=int, default=45)
    parser.add_argument("--frames", type=int, default=6)
    parser.add_argument("--voice", default="af_heart")
    parser.add_argument("--model", default=os.environ.get("VIDEO_MODEL", "claude-haiku-4-5"))
    parser.add_argument("--subscription", action="store_true")
    parser.add_argument("--no-audio", action="store_true", help="Skip TTS/captions for cheap visual development.")
    parser.add_argument("--render", action="store_true")
    args = parser.parse_args()

    try:
        result = build_video(
            topic=args.topic,
            source_path=args.source,
            plan_path=args.plan,
            destination=args.destination,
            length=args.length,
            frame_count=args.frames,
            voice=args.voice,
            model=args.model,
            subscription=args.subscription,
            audio=not args.no_audio,
            render=args.render,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""command-line runner for the video pipeline."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from video_pipeline.pipeline import build_video
from video_pipeline.runtime import load_dotenv

def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Build a template-driven HyperFrames explainer.")
    parser.add_argument("--topic", default="Five affordable AI tools for small business")
    inputs = parser.add_mutually_exclusive_group()
    inputs.add_argument("--source", type=Path, help="Use human-verified notes and skip web research.")
    inputs.add_argument("--research", type=Path, help="Use a cached research JSON file.")
    inputs.add_argument("--plan", type=Path, help="Use an existing JSON plan; makes no model calls.")
    parser.add_argument("--refresh-research", action="store_true", help="Ignore the topic research cache.")
    parser.add_argument("--audience", default="Hawaii small businesses, nonprofit staff, and local learners")
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
            research_path=args.research,
            plan_path=args.plan,
            refresh_research=args.refresh_research,
            audience=args.audience,
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

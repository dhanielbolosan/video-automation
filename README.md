# Pūpūkahi social video pipeline

Reference-driven faceless explainers rendered with HyperFrames. AI writes one
validated content plan. External HTML templates own the design and animation, so
each scene cannot invent a different visual language.

## Structure

```text
main.py                         thin CLI runner
video_pipeline/pipeline.py      orchestration
video_pipeline/planning.py      one structured model call
video_pipeline/composition.py   plan → template data
video_pipeline/audio.py         local Kokoro + Whisper captions
video_pipeline/templates/       actual HTML/CSS/GSAP
brand/frame.md                  visual rules and reference links
references/social-video/        source videos, contact sheets, sampled frames
output/<project>-vN/            generated projects and renders
```

## Visual-only development (no Claude usage)

```bash
.venv/bin/python main.py \
  --topic "Affordable AI subscriptions for small business" \
  --plan examples/ai-subscriptions-plan.json \
  --frames 6 --length 43 --no-audio
```

This builds, validates, and snapshots the composition. Add `--render` for an MP4.

## Generated plan

```bash
.venv/bin/python main.py \
  --topic "Affordable AI subscriptions for small business" \
  --source notes/verified-ai-subscriptions.md \
  --frames 6 --length 45 --render
```

The default API path needs `ANTHROPIC_API_KEY` in `.env`. `--subscription` uses
the local Claude CLI for development. Research is deliberately separated: save
verified source notes first, then generate. Every project is written to
`output/<topic-slug>-vN/`; renders are always under its `renders/` directory.

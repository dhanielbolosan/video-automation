# Pūpūkahi social video pipeline

Reference-driven faceless explainers rendered with HyperFrames. AI writes one
validated storyboard recipe. Portrait templates own the design and animation, so
each scene cannot invent a different visual language or spend agent turns writing code.

## Structure

```text
main.py                         thin CLI runner
video_pipeline/pipeline.py      orchestration
video_pipeline/research.py      bounded web research + reusable JSON cache
video_pipeline/planning.py      sourced facts → schema-constrained plan
video_pipeline/composition.py   plan → portrait scene templates
video_pipeline/audio.py         local Kokoro + Whisper captions
video_pipeline/templates/       actual HTML/CSS/GSAP
video_pipeline/catalog/         allowlist + registry install commands (no vendored demos)
brand/frame.md                  visual rules and reference links
references/social-video/        source videos, contact sheets, sampled frames
output/<project>-vN/            generated projects and renders
research/<topic-slug>.json      reusable source-backed research
```

## Visual-only development (no Claude usage)

```bash
.venv/bin/python main.py \
  --topic "Affordable AI subscriptions for small business" \
  --plan examples/ai-subscriptions-plan.json \
  --frames 6 --length 43 --no-audio
```

This builds, validates, and snapshots the composition. Add `--render` for an MP4.
Selected registry items are recorded in `catalog-selection.json` and
`catalog-install.sh`; the renderer does not mount a catalog demo automatically.
Each demo still needs a portrait adapter and data wiring, so the render remains
on the deterministic local template until that adapter exists.

## Topic-only research and render

```bash
.venv/bin/python main.py \
  --topic "Affordable AI subscriptions for small business" \
  --frames 6 --length 45 --subscription --render
```

Topic-only runs search the web, save reusable facts to
`research/<topic-slug>.json`, plan from those facts, and render. The researcher
can only search; the planner has no tools; graphics remain deterministic.
`--refresh-research` replaces the cache for time-sensitive topics.

The default API path needs `ANTHROPIC_API_KEY` in `.env`; `--subscription` uses
the local Claude CLI. `--research research/example.json` reuses an explicit
cache, `--source notes.md` skips web research, and `--plan plan.json` makes no
model calls. Every project is written to `output/<topic-slug>-vN/`.

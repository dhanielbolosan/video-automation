# Agent Instructions

This handoff starts from a blank repository.

Read this file completely, inspect the repository, and identify the active milestone. If the user does not specify one, start with Milestone 1. Do not load every handoff document at once.

Always read:

1. `handoff/README.md`
2. the introduction, Sections 1–2, and the active milestone in Section 14 of `handoff/LOCAL_VIDEO_CREATOR_BLUEPRINT.md`

For Milestone 1, also read:

- Sections 10–11 of `handoff/LOCAL_VIDEO_CREATOR_BLUEPRINT.md`
- `handoff/video/frame.md`
- `handoff/video/STORY_RULES.md`
- `handoff/video/SCENE_LIBRARY.md`
- `handoff/video/QUALITY_GATES.md`

For Milestone 2, also read:

- Sections 4, 6–7, and Milestone 2 of `handoff/LOCAL_VIDEO_CREATOR_BLUEPRINT.md`
- `handoff/RESEARCH_POLICY.md`

For Milestone 3, also read:

- Sections 3, 5, 8–9, 12–13, and Milestone 3 of `handoff/LOCAL_VIDEO_CREATOR_BLUEPRINT.md`
- `handoff/RUNBOOK.md`

Read a deferred document only when the current work actually reaches it. Implement only the active milestone. For any HyperFrames composition work, load the current HyperFrames entry skill and the relevant core, creative, animation, media, and CLI guidance before authoring.

Non-negotiable:

- use FastAPI, Pydantic, standard-library SQLite, one worker, Ollama, and HyperFrames
- use a repository-local `.venv` created with `python -m venv`; do not require another Python environment manager
- the model returns validated planning data; it does not write arbitrary composition code during a normal job
- facts and online assets require ledger records and human approval
- only approved scene templates may render
- preview review happens before final MP4 rendering
- do not add speculative infrastructure or silently weaken a safety rule
- preserve unrelated user work and record meaningful assumptions in `DECISIONS.md`

Milestone 1 stops after one hand-authored, sourced, visually approved gold-standard video and the templates actually used by it. Do not implement automated topic-to-storyboard planning yet.

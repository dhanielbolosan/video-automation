# Local Video Creator Handoff

This folder is a self-contained specification for starting a blank repository. It describes a local-first educational video creator for Pūpūkahi Tech.

## Start here

1. Create an empty repository and copy this `handoff/` directory into it.
2. Start Codex or Claude Code at the repository root.
3. Tell the agent to read `handoff/AGENTS.md` or `handoff/CLAUDE.md` and follow it.
4. Implement only Milestone 1 from the canonical blueprint.

Recommended kickoff prompt:

> Read `handoff/AGENTS.md` first and follow only its Milestone 1 reading list. Treat this as a blank repository. Build one manually authored, sourced, visually approved gold-standard video. Do not scaffold later milestones.

## Document map

| Document | Authority |
|---|---|
| `LOCAL_VIDEO_CREATOR_BLUEPRINT.md` | Product intent, architecture, pipeline, API, data model, milestones, and deferred work |
| `video/frame.md` | Normative Pūpūkahi visual and brand values |
| `video/STORY_RULES.md` | Editorial, narration, storyboard, continuity, and audio rules |
| `video/SCENE_LIBRARY.md` | Approved scene types and their implementation contracts |
| `RESEARCH_POLICY.md` | Sources, factual claims, online access, assets, licensing, and approval |
| `video/QUALITY_GATES.md` | Human and automated acceptance gates |
| `RUNBOOK.md` | End-to-end local commands from topic submission through final approval |
| `AGENTS.md` | Short Codex entry point |
| `CLAUDE.md` | Short Claude Code entry point |

If two documents appear to conflict:

1. factual and safety requirements in `RESEARCH_POLICY.md` win
2. exact brand values in `video/frame.md` win
3. story decisions in `video/STORY_RULES.md` win over a template default
4. `LOCAL_VIDEO_CREATOR_BLUEPRINT.md` owns architecture and scope

Current HyperFrames skills and framework rules always win over stale CLI syntax in these documents. Record any necessary adjustment in `DECISIONS.md` in the new repository.

## Where these files belong during implementation

Keep `handoff/` as the canonical specification. HyperFrames also needs the frame specification beside the composition, so Milestone 1 makes one exact working copy:

```text
handoff/video/frame.md -> video/composition/frame.md
```

Do not copy the other policies or maintain divergent versions. When the canonical frame changes, replace the working copy before the next render.

## Scope warning

The first milestone proves one excellent video. It does not need authentication, social posting, cloud storage, Redis, Celery, Postgres, React, multiple themes, or autonomous code generation.

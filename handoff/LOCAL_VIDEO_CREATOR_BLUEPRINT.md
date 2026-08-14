# Local Educational Video Creator — Canonical Handoff

## Read this first — handoff for a new Codex or Claude Code session

This document is the source of truth for a blank new repository.

### User and organization intent

- The user is most comfortable with Python and wants FastAPI.
- The project is for a local Hawaii nonprofit that helps the community learn about AI, crypto/digital safety, and practical technology while supporting local businesses.
- Videos should teach something useful: sourced infographics, short tutorials, comparisons, checklists, and explainers.
- Primary output is short-form vertical video for TikTok, Instagram, and similar platforms; landscape should remain an option.
- Factual trust and visible sourcing matter because the organization teaches media and technology literacy.
- The system should run primarily on the user's laptop with an RTX 5070 Ti Laptop GPU and avoid Claude/OpenAI usage charges during routine production.
- Finished videos should remain on the laptop in a predictable local output directory for the first version.

### Scope and quality constraints

- Routine production must not depend on paid model credits or a long autonomous coding session.
- No single model should simultaneously research, design, illustrate, animate, code, mix, and approve a video.
- Models must not improvise organic SVG illustration, chart systems, transitions, or SFX choices during routine rendering.
- Every video must use a recognizable Pūpūkahi visual language and reviewed scene templates.
- Each video begins with a topic supplied by the user.
- The first version is a local single-user application, not a distributed platform.

### Product principles

1. **Truth before scripting.** Research becomes a reviewed fact ledger. The model may not cite its own memory.
2. **Rights before assets.** Online images need a recorded creator, source page, and usable license.
3. **Taste lives in templates.** The model chooses among approved scene types; it does not invent a new design system every run.
4. **Motion explains.** Movement, transitions, and SFX need a stated narrative purpose.
5. **Human approval happens before expensive rendering.** Review facts and a contact sheet, not a finished bad video.
6. **Local first.** Routine inference, job state, working files, and rendered videos stay local. Web research is the only required network stage.
7. **Keep the stack boring.** FastAPI, Pydantic, SQLite, one worker, Ollama, HyperFrames, and FFmpeg.

### Instructions to the implementation agent

- Read `handoff/AGENTS.md` first and follow its milestone-specific reading order. Do not load this entire blueprint when only one milestone is active.
- Read the current HyperFrames skills/documentation before authoring composition code.
- Start a fresh repository unless the user explicitly changes that instruction.
- Implement milestones in order. Do not scaffold later milestones “for completeness.”
- Build and visually approve one excellent template video before automating topic generation.
- Do not add Redis, Celery, Postgres, an ORM, React, or a generic autonomous-agent framework.
- Do not allow arbitrary shell commands or unrestricted network access from model output.
- Do not silently weaken factual, copyright, input-validation, or SSRF protections to make a demo pass.
- When an assumption is necessary, record it in the new repository's `DECISIONS.md`.

### What this architecture can and cannot improve

- FastAPI, SQLite, and Ollama do not make pixels prettier. They make the workflow cheaper, inspectable, and resumable.
- Visual quality comes from the approved Pūpūkahi frame system, reviewed scene templates, grounded media, deliberate choreography, and human review.
- A local model will usually be weaker than a frontier cloud model at unconstrained art direction. This design improves results by removing unconstrained art direction from routine generation.
- HyperFrames validation proves technical correctness, not taste. A contact sheet and watched render remain required.
- The first automated output is not the quality target. The first target is one manually authored gold-standard video from which templates are extracted.

## 1. Goal

Build a local-first service that turns a sourced educational brief into a polished vertical video for a nonprofit.

Typical outputs:

- infographics and data explainers
- short tutorials and checklists
- before/after comparisons
- process and flow explanations
- community, AI, small-business, and digital-safety education

The application should be inexpensive to run, understandable by one maintainer, and visually consistent. It should not depend on an LLM to invent a new visual system or write an entire video application for every render.

## 2. Core decision

Use the local model as a **planner**, not as an unrestricted coding agent.

```text
user topic, provided URLs, or provided source text
    -> web research and licensed-image discovery
    -> source, fact, and asset ledgers
    -> human evidence approval
    -> validated educational brief using ledger IDs
    -> Ollama creates structured storyboard JSON
    -> HyperFrames templates create a contact-sheet preview
    -> human reviews script, storyboard, motion, audio, and preview
    -> deterministic HyperFrames templates create the composition
    -> HyperFrames checks and renders
    -> human watches the rendered video
    -> final MP4 moves into local output storage
```

This is intentionally different from asking an agent to create arbitrary HTML, CSS, SVG, GSAP, narration, sound, and transitions in one long session. A constrained planner plus reviewed templates should be cheaper, more predictable, and easier to improve.

### Topic input

The user supplies the educational topic directly. Topic discovery, popularity scoring, and a `niche` input are outside version one. `POST /videos` begins from the supplied topic or source material.

### Input routing

| User provides | Pipeline behavior |
|---|---|
| Topic only | Search the web, freeze sources, extract proposed facts, and find licensed asset candidates |
| Topic plus source URLs | Start with those URLs; supplement them only when `research_mode` is `auto` |
| Source text | Treat it as supplied material; use the web only when `research_mode` is `auto` |
| Local asset paths | Use those assets and skip online image discovery unless `image_policy` requests it |

### One video run

1. `POST /videos` validates the request, writes a `queued` job to SQLite, and returns immediately.
2. The worker researches only as requested and freezes every downloaded page and asset locally.
3. It creates source, fact, and asset ledgers, then pauses at `awaiting_evidence_review`.
4. The user approves specific facts and assets. Only approved ledger IDs continue.
5. Ollama makes a small number of structured planning calls for the brief, narration, and storyboard. It does not edit repository files or run commands.
6. The worker creates narration, captions, the HyperFrames composition, technical checks, snapshots, and a local preview.
7. The job pauses at `awaiting_preview_review`; the user reviews the script, storyboard, motion, sound, contact sheet, and preview.
8. `POST /videos/{id}/render` queues the approved revision for a high-quality render.
9. The worker writes a checked candidate MP4 and pauses at `awaiting_final_review`.
10. The user watches the whole video. Final approval moves the MP4, credits, ledgers, and manifest under `output/JOB_ID/` and marks the job `complete`.

Each completed stage is a checkpoint in SQLite. Retrying a failed render resumes from the last valid artifact instead of repeating research or regenerating approved work.

## 3. Minimal stack

| Need | Choice | Why |
|---|---|---|
| API | FastAPI | Familiar, small, typed through Pydantic, and sufficient for a local service |
| Job metadata | SQLite via Python `sqlite3` | One machine and one render worker do not need Postgres |
| Fact discovery | `ddgs` | Keyless metasearch for candidate URLs; discovery only, never proof |
| Page retrieval | `httpx` + `trafilatura` | Bounded HTTP fetching and main-text extraction |
| Licensed images | Openverse API, then Wikimedia Commons metadata | Search openly licensed work and retain attribution/license data |
| Local model | Ollama with one evaluated local model | Use the smallest candidate that passes the project eval |
| Video composition | HyperFrames | Deterministic HTML/GSAP video rendering and validation |
| Composition templates | Plain HTML/CSS/JS | Avoid React and a second frontend framework |
| Narration | HyperFrames local TTS/Kokoro | No per-render voice API bill |
| Rendering | HyperFrames + Chrome + FFmpeg | Required by the renderer |
| Durable video storage | Local `output/` directory | The simplest inspectable storage for one laptop |
| Temporary working storage | `.work/` | HyperFrames, Chrome, TTS, and FFmpeg need isolated files while rendering |

Do not add Redis, Celery, RabbitMQ, Postgres, React, or a workflow engine for the first version.

Minimum Python runtime dependencies:

```text
fastapi
uvicorn
ollama
httpx
trafilatura
ddgs
```

Pydantic arrives with FastAPI. Use the standard library for SQLite, paths, subprocesses, hashing, URL parsing, timestamps, and UUIDs.

## 4. Local-model evaluation

### Quality-first baseline: `gemma4:12b`

The RTX 5070 Ti Laptop GPU has 12 GB of VRAM. Ollama currently lists `gemma4:12b` at about 7.6 GB with text and image input, leaving practical headroom for the runtime and image-based snapshot review. It is the quality-first baseline, not a permanent requirement.

```bash
ollama pull gemma4:12b
ollama run gemma4:12b
```

Recommended runtime settings:

```text
model: gemma4:12b
context: 16384 initially
temperature: 0.2 for planning
temperature: 0 for visual review
structured output: Pydantic JSON schema
```

Do not start at the advertised maximum context window. The KV cache also consumes memory. Increase context only if real briefs are being truncated.

### Smallest-model-first R&D ladder

Benchmark candidates on the same ten representative briefs and stop at the first model that passes:

1. `qwen3.5:4b` — smallest serious multimodal baseline, about 3.4 GB in Ollama
2. `qwen3.5:9b` — likely cost/performance midpoint, about 6.6 GB
3. `gemma4:12b` — quality-first local baseline, about 7.6 GB

Measure schema-valid response rate, source-association errors, unsupported claims, narration edits, scene-choice edits, retries, elapsed time, and peak memory. Do not add a runtime model router during R&D. Select one default model after the eval and keep `OLLAMA_MODEL` configurable.

`gpt-oss:20b` is about 14 GB in Ollama and therefore exceeds the laptop GPU's 12 GB VRAM before context and runtime overhead. Do not make CPU/system-memory spill the default path.

### Expected capability gap

Gemma 4 12B is not expected to match frontier cloud models such as Claude Opus 5 or GPT-5.6 Sol at open-ended repository work, complex debugging, long agentic tool use, or visual design judgment. Use it only for bounded tasks with schemas and deterministic validators:

- propose focused search queries
- extract candidate facts tied to frozen sources
- draft narration from approved fact IDs
- choose an approved story arc, scene kind, and variant
- fill validated storyboard fields
- suggest possible issues in contact-sheet images for human review

It must not generate or edit scene implementation code during a normal video job. If a new scene type or difficult template repair is genuinely needed, treat that as manual development work. A frontier model may be used occasionally for that development task, but it is not a runtime dependency and cannot approve its own result.

This is a cost-and-control decision, not a claim that the local model is equally capable. Before automating Milestone 2, run the same representative briefs through the local planner and judge schema validity, citation accuracy, narration edits, scene-choice edits, and total runtime. Keep the local model only if it clears the project's acceptance gates.

Current references:

- [NVIDIA RTX Laptop specifications](https://www.nvidia.com/en-us/geforce/laptops/compare/)
- [Ollama Gemma 4 models](https://ollama.com/library/gemma4)
- [Ollama Qwen 3.5 models](https://ollama.com/library/qwen3.5/tags)
- [Ollama gpt-oss models](https://ollama.com/library/gpt-oss)
- [Google Gemma documentation](https://ai.google.dev/gemma/docs)
- [OpenAI latest model guide](https://developers.openai.com/api/docs/guides/latest-model)
- [Anthropic model overview](https://platform.claude.com/docs/en/about-claude/models/overview)
- [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs)

## 5. Repository layout

```text
local-video-creator/
├── handoff/                     # Canonical product and production specification
│   ├── README.md
│   ├── AGENTS.md
│   ├── CLAUDE.md
│   ├── RESEARCH_POLICY.md
│   ├── RUNBOOK.md
│   ├── LOCAL_VIDEO_CREATOR_BLUEPRINT.md
│   └── video/
│       ├── frame.md
│       ├── STORY_RULES.md
│       ├── SCENE_LIBRARY.md
│       └── QUALITY_GATES.md
├── app/
│   ├── main.py                 # FastAPI routes and lifespan
│   ├── models.py               # Pydantic request, storyboard, and status models
│   ├── db.py                   # Small sqlite3 job repository
│   ├── research.py             # Search, fetch, extract, and fact-ledger pipeline
│   ├── assets.py               # Openverse/Commons discovery and asset ledger
│   ├── network.py              # URL validation, SSRF blocking, bounded downloads
│   ├── planner.py              # Ollama call returning Storyboard JSON
│   ├── worker.py               # One local render worker
│   ├── compiler.py             # Storyboard JSON -> HyperFrames project data
│   ├── hyperframes.py          # Safe subprocess wrappers
│   └── settings.py             # Environment-variable settings
├── video/
│   ├── composition/
│   │   ├── frame.md            # Exact working copy of the canonical frame
│   │   ├── index.html          # One generic HyperFrames composition
│   │   ├── styles.css
│   │   └── timeline.js
│   ├── scenes/
│   │   ├── hero.js
│   │   ├── stat.js
│   │   ├── compare.js
│   │   ├── process.js
│   │   └── media.js
│   └── assets/
│       ├── fonts/
│       ├── sfx/
│       └── brand/
├── prompts/
│   ├── research.md
│   ├── storyboard.md
│   └── visual-review.md
├── tests/
│   ├── test_planner.py
│   └── test_compiler.py
├── .work/                      # ignored; temporary job projects
├── output/                     # ignored; completed MP4, credits, and manifest per job
├── data/
│   └── app.db                  # ignored or backed up separately
├── .venv/                       # ignored; local Python virtual environment
├── requirements.txt             # pinned direct Python dependencies
├── .env.example
└── README.md
```

One generic composition is preferable to generating a new program for each video. The backend writes validated data into the composition; the scene modules decide how approved scene types render.

## 6. Online research and image acquisition

### Can the local model research online?

Yes, but **Ollama does not give a local model internet access by magic**. The application must give it narrow tools. Ollama supports function/tool calling, so FastAPI can expose safe functions such as:

```text
search_web(query)
fetch_page(url)
search_open_images(query)
download_approved_asset(asset_id)
```

The Python application executes those functions and returns bounded results to the model. The model never receives a general-purpose browser, shell, filesystem path, or raw HTTP client.

Ollama also offers an official hosted web-search API, but it requires an Ollama account/API key. Keep it as an optional later provider. The zero-credit default in this blueprint is `ddgs` for discovering candidate pages, followed by direct fetching and verification.

References:

- [Ollama tool calling](https://docs.ollama.com/capabilities/tool-calling)
- [Ollama web search](https://docs.ollama.com/capabilities/web-search)
- [`ddgs` Python package](https://pypi.org/project/ddgs/)

### Research is evidence collection, not a truth oracle

No LLM, local or hosted, can guarantee that a fact is true. The system should make unsupported or misquoted claims difficult to publish.

Use this pipeline:

```text
topic
  -> model proposes 3–6 focused search queries
  -> ddgs returns candidate URLs
  -> Python fetches pages with strict network limits
  -> trafilatura extracts readable text
  -> model proposes claims tied to exact source IDs
  -> Python verifies quoted evidence exists in frozen source text
  -> human approves/rejects the fact ledger
  -> script and storyboard may reference approved fact IDs only
```

Research must finish before scriptwriting. Never let the script agent browse until it finds words that support a script it has already written.

### Source priority

Prefer, in order:

1. government agencies, official statistics, legislation, standards, and primary documentation
2. universities, peer-reviewed papers, and recognized research institutions
3. first-party product documentation for claims about that product
4. established nonprofits and professional organizations
5. reputable journalism for events and attributed reporting
6. Wikipedia or general blogs for discovery only, followed by their primary sources

For medical, legal, financial, election, public-safety, or fast-changing claims, require human approval and at least one current primary/official source. Two low-quality pages repeating one another are not independent confirmation.

### Fetching rules

Every model-selected URL crosses a trust boundary. `network.py` must enforce:

- only `http` and `https`
- reject credentials embedded in URLs
- reject loopback, private, link-local, multicast, and cloud-metadata addresses after DNS resolution
- re-check every redirect target
- short connect/read timeouts
- response-size and redirect-count limits
- allow HTML, plain text, PDF, and approved image MIME types only
- identify the application with a real user agent
- respect site access rules; do not bypass authentication, paywalls, CAPTCHAs, or robots controls
- cache successful source documents locally by SHA-256
- never perform network requests during HyperFrames rendering

PDF extraction can be added when the first real source requires it. Do not add a PDF stack speculatively.

### Fact ledger

Each research run writes `.work/JOB_ID/research/facts.json` and a readable `FACTS.md`.

Every claim contains:

- stable fact ID
- publication-ready paraphrase
- short supporting excerpt
- one or more source IDs
- publisher and page title
- published/updated date when available
- retrieval timestamp
- whether the source is primary, secondary, or discovery-only
- approval status and reviewer note

Numbers, dates, named quotations, and rankings must be present in the frozen source material. If the supporting evidence cannot be located, reject the claim rather than asking the model to repair it from memory.

Videos should display a compact source label near the claim when practical. The full URLs and access dates travel in the description or companion credits file.

### Image search and copyright

Do not treat generic image-search results as reusable assets. Being visible online does not grant reuse rights.

Use this order:

1. user-supplied photos, screenshots, and brand assets
2. public-domain or CC0 assets
3. CC BY assets with generated attribution
4. other Creative Commons assets only after their conditions are explicitly supported
5. generated artwork, if a later milestone adds a local image model

Openverse is the default discovery API because it indexes Creative Commons and public-domain media. It still warns that license data must be verified. Follow each result to its original source page before approval. Wikimedia Commons' `imageinfo` API can provide creator and `extmetadata`, including license fields.

Every downloaded asset writes an entry to `.work/JOB_ID/research/assets.json` and `CREDITS.md` containing:

- stable asset ID
- local frozen filename and SHA-256
- original file URL
- original source/detail page
- title and creator
- license name and license URL
- required attribution text
- retrieval timestamp
- crop/color/other modifications
- approval status

Only approved asset IDs may enter a storyboard. Download the file before composition and refer to the local path; renders must never depend on a remote URL.

References:

- [Openverse API](https://api.openverse.org/)
- [Openverse licensing warning](https://docs.openverse.org/api/reference/made_with_ov.html)
- [Wikimedia `imageinfo` metadata](https://www.mediawiki.org/wiki/API:Imageinfo/en)

## 7. Pydantic contracts

The model must return JSON matching a schema. Never parse free-form prose into a production job.

### Video request

```python
class VideoRequest(BaseModel):
    title: str
    topic: str
    audience: str = "general community"
    learning_goal: str
    source_text: str | None = None
    source_urls: list[str] = Field(default_factory=list)
    asset_paths: list[str] = Field(default_factory=list)
    duration_seconds: int = Field(default=45, ge=15, le=90)
    format: Literal["vertical", "landscape"] = "vertical"
    research_mode: Literal["auto", "provided_only", "none"] = "auto"
    image_policy: Literal["supplied_only", "open_license"] = "open_license"
```

Request validation at the API boundary:

- `auto` may start from only a topic and may search beyond supplied material
- `provided_only` requires `source_text` or `source_urls` and may fetch only the supplied URLs
- `none` performs no network research and requires `source_text`
- `supplied_only` requires at least one `asset_path` when a scene needs external imagery

### Research records

```python
class Source(BaseModel):
    id: str
    url: HttpUrl
    title: str
    publisher: str | None = None
    published_at: date | None = None
    retrieved_at: datetime
    kind: Literal["primary", "secondary", "discovery_only"]
    local_path: str
    sha256: str


class Fact(BaseModel):
    id: str
    claim: str
    evidence_excerpt: str
    source_ids: list[str]
    approved: bool = False
    reviewer_note: str | None = None


class Asset(BaseModel):
    id: str
    local_path: str
    source_url: HttpUrl
    detail_url: HttpUrl
    creator: str | None = None
    license: str
    license_url: HttpUrl
    attribution: str
    sha256: str
    approved: bool = False
```

### Storyboard scene

```python
class Scene(BaseModel):
    kind: Literal["hero", "stat", "compare", "process", "media", "outro"]
    variant: str
    narrative_role: str
    persuasion: Literal[
        "comparison",
        "demonstration",
        "enumeration",
        "counterexample",
        "proof",
        "callback",
        "distillation",
    ]
    emotional_beat: Literal[
        "recognition", "concern", "curiosity", "clarity", "confidence", "resolve"
    ]
    narration: str
    on_screen_text: list[str]
    fact_ids: list[str] = Field(default_factory=list)
    asset_ids: list[str] = Field(default_factory=list)
    data: dict[
        str,
        str | int | float | list[str] | list[int] | list[float],
    ] = Field(default_factory=dict)
    focal: str
    supporting: list[str] = Field(default_factory=list, max_length=2)
    background: str | None = None
    motion_purpose: Literal[
        "direct_attention",
        "carry_continuity",
        "show_change",
        "express_character",
    ]
    reveal_cues: list[str] = Field(default_factory=list)
    transition_out: Literal["cut", "primary", "accent"]
    sfx: Literal["none", "soft_click", "pop", "impact", "whoosh"] = "none"
    sfx_reason: str | None = None
```

### Storyboard

```python
class Storyboard(BaseModel):
    message: str
    learning_goal: str
    audience: str
    angle: Literal["concept", "how_to", "listicle", "comparison", "story"]
    arc: Literal[
        "hook_value_explanation_example_takeaway",
        "hook_outcome_steps_check_takeaway",
        "hook_criteria_items_best_takeaway",
        "hook_decision_axis_evidence_recommendation",
        "risk_signs_response_verify",
    ]
    mood: str
    motif: str | None = None
    breather_scene_index: int | None = None
    spectacle_scene_index: int | None = None
    primary_transition: Literal["push", "blur"]
    accent_transition: Literal["none", "iris", "cinematic_zoom"] = "none"
    scenes: list[Scene]
```

Validation rules implemented in Python, not left to the model:

- every factual number must have a supplied source
- 3–7 scenes for a 15–90 second video
- every `kind` and `variant` pair exists in `handoff/video/SCENE_LIBRARY.md`
- every scene has exactly one focal and no more than two supporting elements
- related scenes may reuse a type or visual space when continuity helps comprehension
- one primary transition across most seams
- at most one accent transition and one spectacle scene
- one breather is named for videos longer than 25 seconds
- at most one SFX per scene and roughly one per six seconds
- `sfx != none` requires `sfx_reason`
- narration must fit the requested duration
- on-screen text is substantially shorter than narration
- CTA cannot introduce a new claim

Ollama supports supplying the Pydantic JSON schema through the `format` field. Validate the response again with `Storyboard.model_validate_json(...)`.

### Review action

```python
class ReviewPatch(BaseModel):
    action: Literal[
        "approve_evidence",
        "approve_preview",
        "approve_final",
        "request_changes",
    ]
    revision: int = Field(ge=1)
    approved_fact_ids: list[str] = Field(default_factory=list)
    approved_asset_ids: list[str] = Field(default_factory=list)
    narration_override: str | None = None
    notes: str | None = None
```

Validate allowed fields against the current job stage. `request_changes` requires `notes`; `approve_evidence` requires at least one approved fact when the planned video makes factual claims; and preview/final approval requires the exact current revision.

## 8. API endpoints

Keep the API asynchronous and job-oriented because research and rendering can take time. There are six public endpoints. Research, scripting, TTS, composition, checks, and file movement remain internal worker stages.

### `POST /videos`

Validate input, create a job, and enqueue research. Do not plan or render before evidence approval.

```json
{
  "title": "Three signs of an AI scam",
  "topic": "AI impersonation scams",
  "learning_goal": "Help viewers recognize three warning signs",
  "source_urls": ["https://example.gov/source"],
  "duration_seconds": 45,
  "format": "vertical",
  "research_mode": "auto",
  "image_policy": "open_license"
}
```

Response: `202 Accepted`

```json
{
  "id": "01J...",
  "status": "queued"
}
```

### `GET /videos/{id}`

Return status, current stage, coarse progress, errors, and final output location. Polling this one endpoint is sufficient for a local client.

```json
{
  "id": "01J...",
  "status": "researching",
  "stage": "fetch_sources",
  "progress": {"done": 3, "total": 5},
  "review_url": null,
  "local_video": null,
  "error": null
}
```

Suggested statuses:

```text
queued
  -> researching
  -> awaiting_evidence_review
  -> planning
  -> previewing
  -> awaiting_preview_review
  -> render_queued
  -> rendering
  -> awaiting_final_review
  -> complete

Any worker stage may become failed.
```

### `GET /videos/{id}/review`

Return the current staged review document from one stable endpoint.

At `awaiting_evidence_review`, it contains:

- frozen sources and proposed facts with evidence excerpts
- asset candidates with local previews, creator, license, and attribution

At `awaiting_preview_review`, it also contains:

- narration and on-screen copy
- validated storyboard JSON
- contact-sheet and representative-frame paths
- local HyperFrames preview URL or equivalent timeline player

At `awaiting_final_review`, it also contains the checked candidate MP4 path and verification results.

Every response includes the current revision, stage, prior approvals, and review notes. Keeping one staged review resource avoids extra endpoints while preserving the required order.

### `PATCH /videos/{id}/review`

Save an explicit stage action, approvals, an optional narration override, or revision notes. The worker invalidates and regenerates only affected downstream artifacts. For example, a narration override rebuilds timing and the preview but does not repeat web research.

```json
{
  "action": "approve_evidence",
  "approved_fact_ids": ["fact_1", "fact_2"],
  "approved_asset_ids": ["asset_1"],
  "revision": 1,
  "notes": "Official sources and license records verified."
}
```

Allowed actions:

- `approve_evidence` — available only at `awaiting_evidence_review`
- `approve_preview` — available only at `awaiting_preview_review`
- `approve_final` — available only at `awaiting_final_review`; moves approved deliverables to `output/` and marks the job complete
- `request_changes` — records notes and invalidates only affected downstream artifacts

Return `409 Conflict` for a stale revision or an action that does not match the current stage.

### `POST /videos/{id}/render`

Queue the approved preview revision for the high-quality render. Return `409 Conflict` if any used fact or asset is unapproved, if the preview is stale or unapproved, or if the job is already rendering.

```json
{
  "id": "01J...",
  "status": "render_queued"
}
```

### `GET /videos/{id}/file`

Serve the checked candidate MP4 at `awaiting_final_review` and the approved `output/JOB_ID/video.mp4` after completion. Return `409 Conflict` before a candidate exists and `404 Not Found` if its database record or file does not exist.

No `/trends`, `/search`, `/generate-script`, `/generate-audio`, `/compose`, `/upload`, facts, assets, or storyboard endpoints are needed. Those are internal stages or fields of the staged review document.

## 9. Job execution without Redis or Celery

### What SQLite is

SQLite is a relational SQL database stored primarily in one ordinary file, here `data/app.db`. There is no database server, account, port, container, or daemon. Python opens the file through its built-in `sqlite3` module.

The database stores small structured records:

- job ID, request, status, timestamps, and error
- source, fact, and asset ledger metadata
- storyboard JSON
- paths to generated files

Do **not** store MP4 files, images, page captures, or audio as database blobs. Store those as files and put their paths plus hashes in SQLite.

While the application is running in WAL mode, SQLite can create temporary sibling files such as `app.db-wal` and `app.db-shm`. That is normal. The durable database is still local and self-contained; use SQLite's backup API rather than copying a live database mid-write.

Minimal connection setup:

```sql
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 5000;
```

Create the first schema with `CREATE TABLE IF NOT EXISTS` statements in `db.py`. Do not add an ORM or migration framework yet. Add migrations only when the first incompatible schema change actually occurs.

Suggested initial tables:

```text
jobs
sources
facts
assets
```

`sources`, `facts`, and `assets` carry a `job_id` foreign key. Large structured payloads such as the original request and storyboard can be JSON text columns; their Pydantic models remain the validation authority.

Keep timing and checkpoint metadata in JSON text columns on `jobs` (`stage`, `progress_json`, `stage_metrics_json`, and `artifact_manifest_json`). A separate events or metrics table is unnecessary until the application needs cross-job analytics beyond a simple report.

Use one worker because one laptop should normally render one video at a time.

```text
FastAPI inserts a queued job into data/app.db
    -> worker claims oldest queued job in a transaction
    -> worker updates status after each stage
    -> worker pauses at each human review gate
    -> final approval moves the checked MP4 and credits to output/JOB_ID/
    -> API reads status and file paths from SQLite
```

Run the API and worker in separate terminals. Activate the same environment in each.

API terminal:

```bash
source .venv/bin/activate
python -m uvicorn app.main:app --reload
```

Worker terminal:

```bash
source .venv/bin/activate
python -m app.worker
```

This is more durable than relying only on FastAPI `BackgroundTasks`, while remaining much smaller than Redis plus Celery. Add a real queue only when renders must run on multiple machines.

On startup, inspect stale `researching`, `planning`, `previewing`, or `rendering` jobs and resume from the last valid checkpoint or mark them `failed` with a useful error. Review states remain paused until a human acts.

### Performance and measurement

The pipeline should use substantially fewer paid-model credits because routine planning is local. It should also waste fewer full renders because review happens at the contact-sheet stage. Do not promise a fixed end-to-end time before measuring the actual laptop: network research, TTS, Chrome, and FFmpeg vary by topic and duration, and final rendering will usually remain the slowest stage.

Record `started_at`, `finished_at`, and `duration_ms` for each stage in SQLite. Also record Ollama prompt/evaluation token counts, source count, scene count, and final render duration. After ten representative jobs, those records become the real performance baseline. One worker and one render at a time are intentional; add concurrency only when queue wait time is a measured problem.

## 10. HyperFrames production workflow

The official HyperFrames prompting guide recommends moving from intent to a confirmed brief, then storyboard/design, authoring, preview, validation, and render. Apply that workflow as follows.

HyperFrames is the renderer and authoring contract, not an automatic taste engine. Its polished examples rely on a confirmed route, exact specification, timed beats, named techniques or registry blocks, shared motion grammar, negative constraints, and visual iteration. This handoff supplies those decisions through `frame.md`, `STORY_RULES.md`, `SCENE_LIBRARY.md`, and `QUALITY_GATES.md` rather than expecting one short prompt to produce consistent art direction.

### 10.1 Install once

```bash
npx hyperframes init video/composition --non-interactive --example blank --resolution portrait --skill=faceless-explainer
npx hyperframes skills update faceless-explainer
```

The primary workflow for sourced educational topics is `faceless-explainer`. Use `general-video` only when a request mixes supplied footage, custom edits, or inputs that do not fit the explainer workflow.

Keep the CLI version pinned in the repository. Check before deliberate upgrades:

```bash
npx hyperframes@latest upgrade --project video/composition --check
```

### 10.2 Produce four artifacts before the final render

1. `BRIEF.md`: thesis, audience, arc, exact narration, supplied facts, and sources.
2. `frame.md`: exact brand palette, fonts, scale, safe area, visual rules, and banned patterns.
3. `STORYBOARD.json`: validated machine-readable scenes.
4. Contact sheet: one representative frame per scene for approval.

The storyboard should define one arc, one inherited direction block, and a light specification for every scene. It should not independently redesign every frame.

### 10.3 Compile approved scenes

Each approved scene type maps to reviewed HTML/CSS/GSAP code.

| Scene type | Use | Visual rule |
|---|---|---|
| `hero` | Hook, major lesson, CTA | Display-scale type plus one supporting visual; CTA is a hero variant |
| `stat` | One important number or a small data series | Use a reviewed counter/chart block; labels live on marks |
| `compare` | Before/after, safe/risky, option A/B | Split frame with one shared axis or dividing gesture |
| `process` | Tutorial steps, flow, checklist | Reveal in spoken order; motion is the explanation |
| `media` | Screenshot, photograph, product or real example | Use a real supplied/generated asset; never fake organic art with SVG |
| `outro` | Final takeaway and optional follow CTA | Resolve the motif; introduce no new claim |

Prefer installed HyperFrames catalog blocks such as `data-chart`, map blocks, counters, captions, and known transition components. Adapt their content and styling rather than asking the model to recreate them.

Use hand-authored SVG only for simple geometry, diagram connectors, chart marks, icons already defined by the design system, and logo paths. Characters, landscapes, painterly scenes, and editorial hero art must be supplied or generated as image assets and then animated in layers.

### 10.4 Motion contract

Every movement must do at least one job:

- direct attention
- carry continuity
- show change
- express the nonprofit's calm, helpful character

If the movement cannot finish the sentence “this moves because…”, remove it.

For each scene:

- one focal element at display scale
- one or two supporting elements arriving on their own cues
- background, content, and foreground depth where the scene needs layering
- staggered entrances rather than everything appearing simultaneously
- a quiet hold that remains alive only when the content justifies it
- narration is the clock; visual reveals land on spoken cues

Avoid the slideshow pattern: centered cluster fades in, sits, fades out, repeat. Carry a recurring object, rule, color field, frame, or motion vector across scene boundaries.

### 10.5 Transition contract

- choose one primary transition for most seams
- use one accent transition for the climax
- use a hard cut when a shared shape, object, voice phrase, or beat already supplies continuity
- do not assign a novel transition to every seam
- the transition is the exit; do not fade a scene out and then animate the next scene in

Suggested nonprofit defaults:

```text
primary: clean push or restrained blur, 0.3–0.5s
accent: one cinematic zoom or iris into the key proof/payoff
outro: simple, slower closure
```

### 10.6 Audio contract

- narration leads
- background music is optional and sits beneath narration
- SFX mark specific visible actions, not every cut or caption
- approximately one SFX per six seconds, never two within one second
- no sound is preferable to an unjustified sound
- visual reveals follow the narration; narration never waits for decorative animation

### 10.7 Validate and render

Run `lint` during authoring after the first HTML pass and structural edits. For the final gate, `check` already reruns lint. From the job's HyperFrames project directory:

```bash
npx hyperframes check --snapshots
npx hyperframes preview
```

The preview is the final timeline review surface. After the current revision is approved, render it:

```bash
npx hyperframes render --quality high --output ../video.mp4
test -s ../video.mp4
ffprobe -v error -show_format ../video.mp4
```

`check` proves that a composition is valid, not that it is attractive. Approval requires the contact sheet and final timeline preview. After rendering, the human watches the complete candidate before marking it complete. Change one variable per iteration.

HyperFrames references:

- [Prompt Guide](https://hyperframes.heygen.com/prompting/overview)
- [One-shot prompt anatomy](https://hyperframes.heygen.com/prompting/anatomy)
- [High-fidelity visual specifications](https://hyperframes.heygen.com/prompting/visual-specs)
- [Premium motion](https://hyperframes.heygen.com/prompting/motion)
- [Transitions](https://hyperframes.heygen.com/prompting/transitions)
- [Data and maps](https://hyperframes.heygen.com/prompting/data-and-maps)
- [Generated artwork](https://hyperframes.heygen.com/prompting/generated-artwork)
- [Media and audio](https://hyperframes.heygen.com/prompting/media-and-audio)
- [Storyboards](https://hyperframes.heygen.com/prompting/storyboards)
- [Iterating](https://hyperframes.heygen.com/prompting/iterating)

## 11. Design system rules for educational nonprofit videos

Keep exact values in `handoff/video/frame.md` and copy it unchanged to `video/composition/frame.md` before authoring or rendering. HyperFrames treats that working copy as brand truth for colors and typography while allowing layout to scale for video.

Start with:

- one warm light canvas with an optional teal inverted register
- one ink color
- one primary accent
- one optional warning/highlight color used once per video
- one display family and one readable body family
- at least 2px structural rules at 1080p
- body text large enough to read on a phone
- consistent caption safe area for TikTok/Instagram UI
- no invented logos, statistics, quotes, or sources

Ban common generated-video tells:

- purple/blue gradients without a brand reason
- glass cards everywhere
- identical card grids
- centered text floating in empty space
- emoji standing in for icon design
- illustration-like SVG people or objects
- a new font, palette, or transition in every scene
- motion that does not explain or connect anything
- SFX on routine captions and fades

The frame should remain recognizably from the same organization even when scene layouts vary.

## 12. Local file storage

Use two roots with different lifetimes:

```text
.work/JOB_ID/       temporary research, TTS, snapshots, and HyperFrames project files
output/JOB_ID/      completed video.mp4, FACTS.md, CREDITS.md, and manifest.json
```

The worker writes the render to `.work/`, validates it, then moves only approved deliverables into `output/`. A move on the same filesystem is atomic, so the API never serves a half-written MP4.

Keep completed output until the user deletes it manually. Temporary work directories may be removed after seven days, but never remove a failed job automatically until its logs have been inspected.

Back up `data/app.db` and `output/` together when backup becomes necessary. Remote storage is outside the first version.

### SaaS portability without SaaS complexity now

The application can become a SaaS, but it will not be deployable as a multi-user SaaS unchanged. HyperFrames templates, Pydantic contracts, research rules, and the planner/compiler pipeline are portable. SQLite, local paths, one worker, local Ollama, Chrome, and FFmpeg are deliberate single-machine choices.

Keep the first version migration-friendly with only these rules:

- all SQL stays in `db.py`
- all paths come from settings rather than hard-coded machine paths
- API handlers enqueue work and never perform a render inline
- artifacts are addressed by job ID and manifest, not by guessed filenames
- model and HyperFrames subprocess calls stay behind their existing small modules

Do not create storage providers, repository interfaces, tenant abstractions, or cloud configuration now. When real users need remote access, migrate in this order:

1. Run the existing API and one worker on one persistent machine. SQLite and local disk still work for a small private deployment.
2. Add authentication and an `organization_id` boundary before accepting multiple organizations.
3. Replace SQLite with Postgres when multiple API/worker processes need concurrent writes.
4. Replace `output/` with object storage such as Azure Blob Storage when files must survive machine replacement or be served from multiple instances.
5. Add a queue only when more than one worker or machine is required.
6. Move Ollama and rendering to a GPU worker host; the API itself does not need a GPU.

The expensive migration is operations, not the video format: remote GPU capacity, Chrome/FFmpeg isolation, authentication, secrets, quotas, backups, and observability. The local-first version should prove that the videos are useful before taking on those costs.

### Optional internal social publishing tool

Publishing is a downstream feature, not part of video creation. Only a `complete` video with approved facts, credits, narration, and caption text may enter a publishing queue.

```text
complete video -> posting draft -> human approval -> publish -> published or failed
```

For a nonprofit discussing AI and crypto, require a person to approve every post. The draft should show the exact video, platform-specific caption, source links, image/license credits, disclaimer if needed, and destination account. Never let the model independently publish, delete posts, reply to comments, or change account settings.

When the organization is ready to support its first real platform, add only:

```text
POST /publications             create a draft from a completed video
GET /publications/{id}         inspect status, caption, destination, and errors
PATCH /publications/{id}       edit and approve the draft
POST /publications/{id}/send   publish the approved draft now
```

A later `publications` table needs only `id`, `video_id`, `platform`, `account_id`, `caption`, `status`, timestamps, remote post ID/URL, and error. Store account tokens outside SQLite in environment secrets for a one-machine tool, and use a managed secret store after SaaS migration.

Start with one platform and “publish now.” Add scheduling, cross-platform fan-out, analytics, and platform-specific integration modules only after the nonprofit actually needs them. Platform APIs, permissions, review requirements, and content rules change; verify current official documentation before implementing each integration.

## 13. Environment variables

```dotenv
APP_DB=data/app.db
WORK_DIR=.work
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=gemma4:12b
OLLAMA_CONTEXT=16384
RESEARCH_MAX_QUERIES=6
RESEARCH_MAX_RESULTS_PER_QUERY=5
FETCH_MAX_BYTES=5000000
OPENVERSE_URL=https://api.openverse.org/v1
HYPERFRAMES_PROJECT=video/composition
OUTPUT_DIR=output
WORK_RETENTION_DAYS=7
MAX_CONCURRENT_RENDERS=1
```

No model API key is required for local inference. The optional hosted Ollama search provider would require its own key; the default `ddgs` research path does not.

## 14. First implementation milestones

### Milestone 1 — one excellent template video

- adopt `handoff/video/frame.md`, `handoff/video/STORY_RULES.md`, `handoff/video/SCENE_LIBRARY.md`, and `handoff/video/QUALITY_GATES.md`
- hand-author one sourced 30–45 second gold-standard vertical explainer without Ollama
- use only the scene types that this story genuinely needs
- confirm captions, safe areas, motion, sound, and local output handling
- extract and document only the templates used by the approved gold-standard video

Do not automate an ugly template.

### Milestone 2 — structured planning

- add safe web discovery and bounded page fetching
- write source, fact, and asset ledgers
- require fact/image approval before scripting
- add the Pydantic request and storyboard schemas
- benchmark `qwen3.5:4b`, `qwen3.5:9b`, and `gemma4:12b` on the same briefs
- select the smallest passing model and call it through Ollama structured output
- validate factual sources and duration in Python
- create a contact sheet for human approval

### Milestone 3 — local job API

- add the six job, staged-review, approval, render, and file endpoints
- persist jobs in SQLite
- add one worker
- surface errors and logs through `GET /videos/{id}`
- record per-stage timing so performance decisions use real laptop measurements

### Add only when measured necessary

- a second coding model
- generated illustration
- multiple themes or organizations
- multiple render workers
- Redis/Celery
- remote or shared storage
- a web dashboard
- social publishing endpoints and one platform integration
- authentication, organizations, and SaaS deployment infrastructure

## 15. Definition of done for the first version

- a topic-only request works without trend or niche data
- one request discovers and freezes candidate sources
- factual claims are traceable to approved evidence excerpts
- online images are traceable to approved source and license records
- one request creates a source-grounded storyboard using only approved ledger IDs
- the storyboard is visible before rendering
- only approved scene types can be emitted
- a human can revise or approve it
- HyperFrames `check --snapshots` passes and the final preview is approved
- the result is readable on a phone
- narration, visuals, transitions, and SFX share the same timing logic
- the checked MP4 and its credits are stored under `output/JOB_ID/`
- the system can recover job status after a restart
- SQLite records the duration and outcome of every pipeline stage
- no paid model or voice API is required

## 16. Kickoff prompt for a new coding session

Copy this prompt into a fresh Codex or Claude Code session after placing this document in the new repository:

> Read `handoff/AGENTS.md` first and follow only its Milestone 1 reading list. Treat the repository as blank. Start Milestone 1 only: create the repository-local `.venv`, load the current HyperFrames skills, adopt the Pūpūkahi production rules, and hand-author one sourced 30–45 second gold-standard vertical explainer. Run `check --snapshots`, inspect the frames, open the final HyperFrames preview, and render only after I approve it. Extract only the templates used by the approved video. Do not implement FastAPI, SQLite, automated research, or Ollama yet. Record meaningful assumptions in `DECISIONS.md`.

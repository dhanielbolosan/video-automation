# Video Studio: Greenfield Repository Handoff

This is the starting document for a new repository. It records the product,
architecture, dependencies, data model, local setup, build order, and the
boundary with the existing HyperFrames video pipeline.

It assumes the developer is new to SvelteKit, GrapesJS, FastAPI, and SQLite.

## 1. Goal

Build a local-first application where a user can:

1. Start from a topic, notes, or a source URL.
2. Generate source-backed research and a structured video plan.
3. Select reliable built-in frame designs.
4. Customize text, colors, images, layout, and approved motion presets.
5. Preview scenes and caption styles.
6. Queue a deterministic HyperFrames render.
7. Download the finished social video.

The central product rule is:

> AI researches and writes structured content. Trusted components and
> HyperFrames decide how the video looks and moves.

The MVP is for one local user on one computer. Its boundaries should allow a
later SaaS version, but the MVP does not need SaaS infrastructure.

## 2. Fixed technical decisions

| Concern | MVP choice | Why |
| --- | --- | --- |
| Frontend | SvelteKit + TypeScript + Tailwind CSS | Learn Svelte while reusing a familiar styling system |
| Dashboard components | shadcn-svelte | Copy accessible, editable component source for fast prototyping |
| Frame editor | GrapesJS Core | Provides selection, drag/drop, resizing, layers, and undo |
| HTTP API | FastAPI | The existing pipeline is Python |
| Database | Python `sqlite3` + SQLite | One file, no database server, included with Python |
| Background work | One Python worker polling SQLite | Renders must not run inside HTTP requests |
| Video engine | Existing `video_pipeline` + HyperFrames | Reuse the deterministic renderer that already works |
| Media storage | Local files | Smallest useful local setup |
| Frontend package manager | npm | Installed with Node and supported by SvelteKit |
| Python environment | `venv` + pip | Built into Python; no additional package manager |

SvelteKit replaces React and Next.js. Do not add React to this repository.
Tailwind and shadcn-svelte style the dashboard UI. GrapesJS is
framework-agnostic JavaScript and works inside a Svelte component.

## 3. What is deliberately deferred

Do not add these until real usage requires them:

- PostgreSQL
- Redis, RQ, or Celery
- Authentication and billing
- Object storage
- Multiple render machines
- WebSockets
- Collaborative editing
- A freeform Canva clone
- Arbitrary user HTML, CSS, or JavaScript
- Direct publishing to every social network
- Kubernetes or microservices

The upgrade conditions are listed near the end of this document.

## 4. Runtime shape

Local development runs three processes:

```text
Browser at localhost:5173
          |
          v
SvelteKit web application
          |
          | HTTP/JSON
          v
FastAPI at localhost:8000
          |
          | reads/writes short transactions
          v
SQLite file: data/app.db
          ^
          |
Single Python worker
          |
          v
video_pipeline -> HyperFrames -> FFmpeg -> MP4
```

The API accepts requests and creates jobs. The worker performs slow work. The
API never waits for a video render to finish.

## 5. New repository layout

Use one monorepo with separate frontend, API, and worker entry points:

```text
video-studio/
├── web/                              SvelteKit application
│   ├── src/
│   │   ├── lib/
│   │   │   ├── api.ts                Calls FastAPI
│   │   │   ├── types.ts              Shared frontend types
│   │   │   ├── components/
│   │   │   │   └── FrameEditor.svelte
│   │   │   └── grapes/
│   │   │       └── video-components.ts
│   │   └── routes/
│   │       ├── layout.css              Tailwind import and dashboard theme
│   │       ├── +page.svelte           Project list
│   │       ├── new/+page.svelte       New project form
│   │       └── projects/[id]/+page.svelte
│   ├── static/
│   ├── package.json
│   └── .env.example
├── api/
│   ├── __init__.py
│   ├── app.py                         FastAPI app and routes
│   ├── db.py                          SQLite connection and initialization
│   ├── models.py                      Pydantic request/response models
│   ├── jobs.py                        Job creation and claiming
│   ├── worker.py                      Background worker entry point
│   └── compiler.py                    Editor JSON -> trusted scene data
├── video_pipeline/                    Existing deterministic pipeline
├── brand/                             Existing visual specification
├── .agents/skills/                    Existing required workflow assets/scripts
├── tests/
├── data/
│   ├── uploads/                       User-supplied media
│   └── .gitkeep
├── output/                            Generated projects and MP4 files
├── research/                          Reusable research cache
├── schema.sql                         Initial SQLite schema
├── main.py                            Existing CLI for debugging
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── DASHBOARD.md                       This handoff
```

Do not split the API and worker into separate repositories. They import the
same Python modules and pipeline.

## 6. Bring forward the existing pipeline

The new repository is not a rewrite of the renderer. Copy these items from the
working `video-automation` repository:

```text
video_pipeline/
brand/
.agents/skills/
tests/test_pipeline.py
main.py
skills-lock.json
```

Also bring over the existing pipeline dependencies from `requirements.txt`:

```text
anthropic
kokoro-onnx
soundfile
```

Do not copy:

```text
.env
.venv/
output/
data/app.db
node_modules/
personal research or source files unless intentionally needed
```

Why `.agents/skills/` matters: the current runtime calls JavaScript workflow
scripts from `.agents/skills/faceless-explainer/scripts`, and the composition
code loads the caption skin from the HyperFrames creative skill. Copying only
`video_pipeline/` would leave hidden runtime files missing.

Keep the copied CLI working before connecting the dashboard. It is the fastest
way to distinguish a pipeline problem from a web application problem.

## 7. Machine prerequisites

Install or verify:

```text
Git
Python
Node.js and npm
FFmpeg and ffprobe
```

The existing pipeline also uses:

```text
npx / HyperFrames
Anthropic API access, unless using an existing plan
Optional Claude CLI for subscription mode
Optional local Whisper tooling for caption transcription
```

Verify the core tools:

```bash
python3 --version
node --version
npm --version
ffmpeg -version
ffprobe -version
```

## 8. Create the new repository

From the directory that will contain the project:

```bash
mkdir video-studio
cd video-studio
git init
```

Create the SvelteKit application:

```bash
npx sv create web
```

Choose:

```text
SvelteKit minimal application
TypeScript
npm
```

Add Tailwind using Svelte's official add-on, initialize shadcn-svelte, and then
install GrapesJS:

```bash
cd web
npx sv add tailwindcss
npx shadcn-svelte@latest init
npm install grapesjs
cd ..
```

The Tailwind add-on configures the Vite plugin, updates the application CSS,
and imports that CSS from the root layout. Do not manually repeat those setup
steps after the add-on succeeds. During shadcn-svelte initialization, keep the
default `$lib` aliases and select the global CSS file created by the Tailwind
add-on.

Start with only the dashboard components needed for the first shell:

```bash
cd web
npx shadcn-svelte@latest add button sidebar
cd ..
```

Add `sheet`, `input`, `label`, `badge`, or `progress` later when a screen
actually uses them. shadcn-svelte copies component source into the repository,
so its styling and behavior remain editable.

Create the Python environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
```

The root `requirements.txt` should initially contain:

```text
fastapi[standard]
anthropic
kokoro-onnx
soundfile
pytest
```

Install it:

```bash
.venv/bin/python -m pip install -r requirements.txt
```

Create the empty application directories shown in the repository layout. Copy
the existing pipeline files only after the SvelteKit scaffold succeeds.

## 9. Environment variables

Never commit real keys.

Root `.env.example`:

```dotenv
ANTHROPIC_API_KEY=
VIDEO_MODEL=claude-haiku-4-5
DATABASE_PATH=data/app.db
OUTPUT_DIR=output
UPLOAD_DIR=data/uploads
WEB_ORIGIN=http://localhost:5173
```

Frontend `web/.env.example`:

```dotenv
PUBLIC_API_BASE_URL=http://localhost:8000
```

For local development, copy each example to `.env` and fill in only the values
you need. Add both `.env` files to `.gitignore`.

The existing repository already has a small `load_dotenv()` function. Call it
at the top of both `api/app.py` and `api/worker.py`, before importing modules
that read environment variables:

```python
from video_pipeline.runtime import load_dotenv

load_dotenv()
```

Keep `api/db.py` from depending on import order by resolving the path inside
`connect()` rather than once at module import time.

The new repository's `.gitignore` should include:

```gitignore
.env
.venv/
__pycache__/
*.pyc
web/.env
web/node_modules/
web/.svelte-kit/
web/build/
data/*.db
data/*.db-shm
data/*.db-wal
data/uploads/*
!data/uploads/.gitkeep
output/
```

## 10. SQLite for a first-time user

### What SQLite is

SQLite is a database stored in one file. There is no database server to start,
no username, and no port.

```text
data/app.db
```

Python includes the `sqlite3` module, so no SQLite Python package is required.
Opening a connection creates the file if it does not exist.

```python
import sqlite3

connection = sqlite3.connect("data/app.db")
```

### Vocabulary

| Term | Meaning |
| --- | --- |
| Database | The `app.db` file |
| Table | A named collection such as `projects` |
| Row | One project, scene, or job |
| Column | A field such as `title` or `status` |
| Query | SQL used to read or change rows |
| Transaction | A group of changes committed or rolled back together |
| Primary key | The unique ID for a row |
| Foreign key | A link from one table to another |

### Connection rule

Create a fresh connection for each short API or worker operation. Do not keep a
single global connection shared across request threads.

`api/db.py` should expose one small connection function:

```python
from __future__ import annotations

import os
import sqlite3
from pathlib import Path


def connect() -> sqlite3.Connection:
    path = Path(os.environ.get("DATABASE_PATH", "data/app.db"))
    path.parent.mkdir(parents=True, exist_ok=True)
    database = sqlite3.connect(path, timeout=30)
    database.row_factory = sqlite3.Row
    database.execute("PRAGMA foreign_keys = ON")
    database.execute("PRAGMA busy_timeout = 30000")
    return database
```

`sqlite3.Row` lets code access results by column name:

```python
with connect() as database:
    row = database.execute(
        "SELECT id, title FROM projects WHERE id = ?",
        (project_id,),
    ).fetchone()

if row:
    print(row["title"])
```

Always use `?` placeholders. Never build SQL with user text:

```python
# Correct
database.execute(
    "INSERT INTO projects (id, title) VALUES (?, ?)",
    (project_id, title),
)
```

### Transactions

The connection context manager commits when the block succeeds and rolls back
when an exception occurs:

```python
with connect() as database:
    database.execute(
        "UPDATE jobs SET status = ? WHERE id = ?",
        ("running", job_id),
    )
```

Keep transactions short. Never hold a database transaction open while AI,
HyperFrames, FFmpeg, or a network request is running.

### WAL mode

Write-ahead logging allows reads while another connection writes. SQLite still
has one writer at a time, which is enough for this single-machine MVP.

Enable it during database initialization:

```sql
PRAGMA journal_mode = WAL;
```

The database, `-wal`, and `-shm` files must stay on the same local machine.
Do not place the SQLite database on a network filesystem.

### Inspecting the database

If the `sqlite3` command-line program is installed:

```bash
sqlite3 data/app.db
```

Useful commands inside its prompt:

```sql
.tables
.schema projects
.headers on
.mode column
SELECT id, title, status FROM projects;
SELECT id, kind, status, progress FROM jobs ORDER BY created_at DESC;
.quit
```

The application does not require the command-line program; it is only a
convenient inspection tool.

## 11. Initial database schema

Create `schema.sql`:

```sql
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    topic TEXT NOT NULL,
    source_url TEXT,
    source_notes TEXT,
    research_json TEXT,
    plan_json TEXT,
    status TEXT NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'researching', 'editing', 'rendering', 'ready', 'failed')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS scenes (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    position INTEGER NOT NULL CHECK (position >= 0),
    title TEXT NOT NULL,
    duration_s REAL NOT NULL CHECK (duration_s > 0),
    design_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (project_id, position)
);

CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    kind TEXT NOT NULL CHECK (kind IN ('research', 'preview', 'render')),
    status TEXT NOT NULL DEFAULT 'queued'
        CHECK (status IN ('queued', 'running', 'succeeded', 'failed', 'cancelled')),
    progress INTEGER NOT NULL DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),
    error TEXT,
    result_path TEXT,
    created_at TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT
);

CREATE INDEX IF NOT EXISTS jobs_queue
ON jobs (status, created_at);

CREATE INDEX IF NOT EXISTS scenes_project
ON scenes (project_id, position);
```

`api/db.py` should also provide an initialization entry point:

```python
def initialize() -> None:
    schema = Path("schema.sql").read_text(encoding="utf-8")
    with connect() as database:
        database.executescript(schema)


if __name__ == "__main__":
    initialize()
```

Initialize the database:

```bash
.venv/bin/python -m api.db
```

Commit `schema.sql`. Do not commit `data/app.db`.

## 12. IDs, dates, and JSON

Use Python standard-library UUIDs:

```python
from uuid import uuid4

project_id = str(uuid4())
```

Store timestamps as UTC ISO 8601 strings:

```python
from datetime import datetime, timezone

now = datetime.now(timezone.utc).isoformat()
```

Store dictionaries as JSON text:

```python
import json

encoded = json.dumps(value, ensure_ascii=False)
decoded = json.loads(encoded)
```

Do not add a UUID, date, or ORM dependency for the MVP.

## 13. API contract

Start with these routes:

```text
GET    /health                      Confirm the API and database work
POST   /projects                    Create a project
GET    /projects                    List projects
GET    /projects/{project_id}       Load project and ordered scenes
POST   /projects/{project_id}/research
                                    Queue research and planning
PUT    /scenes/{scene_id}           Save an edited scene design
POST   /projects/{project_id}/preview
                                    Queue snapshots/contact sheet
POST   /projects/{project_id}/render
                                    Queue the final render
GET    /jobs/{job_id}               Read progress, result, or error
GET    /projects/{project_id}/video Download the finished MP4
```

Example project creation request:

```json
{
  "topic": "Affordable AI subscriptions for small businesses",
  "source_url": null,
  "source_notes": null
}
```

Example response:

```json
{
  "id": "93caf919-ff0f-4d62-a514-c5ca55cf4ec8",
  "title": "Affordable AI subscriptions for small businesses",
  "status": "draft"
}
```

Return `202 Accepted` when a research, preview, or render job is queued:

```json
{
  "job_id": "3835dacd-df55-4189-96a5-99a86e56827f",
  "status": "queued"
}
```

The frontend polls `GET /jobs/{job_id}` every two seconds until the status is
`succeeded` or `failed`.

## 14. FastAPI application rules

`api/app.py` owns HTTP concerns only:

- Parse and validate requests with Pydantic.
- Make short SQLite calls.
- Create jobs.
- Return JSON or files.
- Never run `build_video()` in an endpoint.

During local development, allow the SvelteKit origin:

```python
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Video Studio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("WEB_ORIGIN", "http://localhost:5173")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Do not use `allow_origins=["*"]` when credentials are enabled.

Development command:

```bash
.venv/bin/fastapi dev api/app.py
```

Interactive API documentation is available at:

```text
http://localhost:8000/docs
```

## 15. SQLite job queue and worker

The database is also the MVP job queue.

Job lifecycle:

```text
queued -> running -> succeeded
                  -> failed
```

The worker loop:

1. Opens a connection.
2. Begins a short immediate transaction.
3. Finds the oldest queued job.
4. Marks it running.
5. Commits and closes the transaction.
6. Runs the slow job.
7. Opens a new short transaction to save the result.
8. Repeats.

Claim jobs atomically even though only one worker is expected:

```python
def claim_next_job() -> dict | None:
    database = connect()
    try:
        database.execute("BEGIN IMMEDIATE")
        row = database.execute(
            """
            SELECT * FROM jobs
            WHERE status = 'queued'
            ORDER BY created_at
            LIMIT 1
            """
        ).fetchone()

        if row is None:
            database.commit()
            return None

        database.execute(
            """
            UPDATE jobs
            SET status = 'running', started_at = ?
            WHERE id = ? AND status = 'queued'
            """,
            (utc_now(), row["id"]),
        )
        database.commit()
        return dict(row)
    except Exception:
        database.rollback()
        raise
    finally:
        database.close()
```

The long-running pipeline call happens after `claim_next_job()` returns, when
no database transaction is open.

The worker may wait one second when no job is available. This small polling
delay is acceptable for a local MVP.

Run the worker in its own terminal:

```bash
.venv/bin/python -m api.worker
```

On worker startup, change any abandoned `running` jobs back to `queued`, or
mark them failed with a readable interruption message. Never leave them stuck
forever.

## 16. Pipeline integration

Keep three separate job types:

### Research job

```text
topic/source -> sourced research -> plan.json -> editable scenes
```

This calls the existing research and planning path once. Save the resulting
research and plan in the project record and generated files.

The existing pipeline accepts topic-based research or a local notes file; it
does not directly ingest a requested web page. For a source URL, the new API
must first validate and download the page, extract bounded readable text to a
local notes file, and pass that file as `source_path`. Do not pass a live URL
into the render page.

### Preview job

```text
saved scene designs -> trusted HTML -> HyperFrames check/snapshot
```

It must not call the AI model or repeat research.

### Render job

```text
approved plan/designs -> audio/captions -> HyperFrames -> MP4
```

It uses the saved project state, not whatever happens to be open in a browser.

The current `build_video()` performs the entire pipeline synchronously. Keep it
for the first end-to-end job, then expose smaller research, preview, and render
functions at the existing natural boundaries. Do not duplicate its logic in
FastAPI routes.

Before concurrent rendering is ever enabled, replace topic-derived output
allocation with project/job UUID directories. Two jobs for the same topic must
never write to the same folder.

## 17. SvelteKit and Tailwind basics

A `.svelte` file contains script and markup. Use Tailwind utilities for the
dashboard's layout and styling:

```svelte
<script lang="ts">
  let topic = '';

  async function createProject() {
    await fetch('http://localhost:8000/projects', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ topic })
    });
  }
</script>

<label class="grid gap-2 text-sm font-semibold text-slate-700">
  Topic
  <input
    class="rounded-xl border border-slate-300 bg-white px-4 py-3 outline-none focus:border-teal-600"
    bind:value={topic}
  />
</label>

<button
  class="mt-4 rounded-xl bg-teal-700 px-4 py-3 font-bold text-white"
  onclick={createProject}
>
  Create project
</button>
```

Important route files:

```text
+page.svelte       Page UI
+page.ts           Page data that may run in browser or server
+page.server.ts    Server-only page data and actions
+layout.svelte     Shared layout
```

For this MVP, the browser calls FastAPI directly. Do not create duplicate
SvelteKit API routes that merely forward requests.

Put the API base URL in one frontend helper:

```ts
import { PUBLIC_API_BASE_URL } from '$env/static/public';

export async function api(path: string, init?: RequestInit) {
  const response = await fetch(`${PUBLIC_API_BASE_URL}${path}`, init);
  if (!response.ok) throw new Error(await response.text());
  return response;
}
```

Run the frontend:

```bash
cd web
npm run dev
```

Use shadcn-svelte for interaction-heavy dashboard primitives such as the
sidebar, mobile sheet, dialog, dropdown menu, and form controls. Use ordinary
Svelte markup and Tailwind utilities for simple layout. Do not wrap every
`div`, heading, or project row in a library component.

## 18. What GrapesJS does

GrapesJS is an embeddable HTML-like visual editor framework. It is not the
brand and it is not the video renderer.

Your application owns:

```text
Component HTML structure
Brand CSS
Editable fields
Allowed styles
Motion preset names
HyperFrames compilation
```

GrapesJS supplies:

```text
Canvas
Selection
Drag and drop
Resizing
Layers
Undo and redo
Component project JSON
```

Two terms:

- **Block:** an item shown in the Add panel, such as “Statistic card.”
- **Component:** the structured object created when that block is dropped.

Start with five component types:

```text
hf-heading
hf-image
hf-stat-card
hf-quote
hf-cta
```

Do not start from the generic webpage preset. Register only the video
components the renderer understands.

Tailwind's dashboard styles do not automatically style the GrapesJS canvas,
because GrapesJS renders its canvas inside an iframe. Keep frame-component CSS
with the trusted GrapesJS/HyperFrames component definitions. This also keeps
rendered video styling independent from the dashboard build. Do not install
shadcn-svelte components inside the GrapesJS canvas or rendered video frames.

## 19. Mount GrapesJS in SvelteKit

GrapesJS needs the browser DOM. Initialize it inside Svelte's `onMount`:

```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import 'grapesjs/dist/css/grapes.min.css';

  let container: HTMLDivElement;

  onMount(() => {
    let destroyEditor: (() => void) | undefined;

    import('grapesjs').then(({ default: grapesjs }) => {
      const editor = grapesjs.init({
        container,
        height: '100%',
        storageManager: false,
        selectorManager: { componentFirst: true }
      });

      destroyEditor = () => editor.destroy();

      editor.Components.addType('hf-stat-card', {
        model: {
          defaults: {
            tagName: 'article',
            classes: ['stat-card'],
            attributes: {
              'data-hf-component': 'stat-card',
              'data-animation': 'rise'
            },
            components: [
              {
                tagName: 'strong',
                classes: ['stat-card__value'],
                type: 'text',
                content: '73%'
              },
              {
                tagName: 'span',
                classes: ['stat-card__label'],
                type: 'text',
                content: 'of teams save time'
              }
            ],
            traits: [
              {
                type: 'select',
                name: 'data-animation',
                label: 'Motion',
                options: [
                  { id: 'none', name: 'None' },
                  { id: 'rise', name: 'Rise' },
                  { id: 'pop', name: 'Pop' }
                ]
              }
            ]
          }
        }
      });

      editor.Blocks.add('hf-stat-card', {
        label: 'Statistic card',
        category: 'Data',
        content: { type: 'hf-stat-card' }
      });
    });

    return () => destroyEditor?.();
  });
</script>

<div class="frame-editor" bind:this={container}></div>

<style>
  .frame-editor {
    width: 540px;
    height: 960px;
  }
</style>
```

The 540 x 960 canvas is a half-scale editing view of a 1080 x 1920 portrait
composition.

## 20. Saving editor designs

GrapesJS project JSON is the editable source. HTML export is not the saved
project format.

```ts
const projectData = editor.getProjectData();
```

Save that object in `scenes.design_json` through `PUT /scenes/{scene_id}`.

A scene record also stores fields outside GrapesJS:

```json
{
  "id": "scene UUID",
  "position": 0,
  "title": "Opening hook",
  "duration_s": 5,
  "design": {
    "assets": [],
    "styles": [],
    "pages": []
  }
}
```

Autosave after a short debounce, not on every pointer movement. A save every
500–1000 milliseconds after changes stop is sufficient.

## 21. Translate designs to HyperFrames safely

Do not pass arbitrary exported GrapesJS HTML directly to the renderer.

```text
GrapesJS project JSON
        |
        v
Validate known component types and properties
        |
        v
Python component compiler
        |
        v
Trusted HTML/CSS + paused GSAP timeline
        |
        v
HyperFrames check -> snapshot -> render
```

Begin with a plain renderer mapping:

```python
COMPONENT_RENDERERS = {
    "hf-heading": render_heading,
    "hf-image": render_image,
    "hf-stat-card": render_stat_card,
    "hf-quote": render_quote,
    "hf-cta": render_cta,
}
```

Reject unknown component types. For known components, validate:

```text
Text length
HTML escaping
Asset ID/path
Position and dimensions
Allowed colors
Allowed typography tokens
Allowed motion name
Unique element IDs
```

Allow only a short motion list:

```text
none
fade
rise
slide-left
slide-right
pop
```

The compiler converts these names to deterministic, seekable GSAP timelines.
GrapesJS never generates or accepts user animation JavaScript.

Every compiled HyperFrames composition must retain:

- Explicit dimensions and `data-start="0"`.
- Unique composition and element IDs.
- One synchronous paused timeline.
- Framework-owned media playback.
- No network access, clocks, or unseeded randomness during render.
- HyperFrames validation and snapshot review before final render.

## 22. Captions

Captions are a separate timed overlay track, not permanent elements in each
frame design.

Start with caption presets:

```text
Minimal
Active word
Boxed
Large emphasis
```

Each preset controls typography, colors, position, and active-word treatment.
Transcript data controls the words and timing.

Captions overlay the full composition. Do not shift the entire design upward
or reserve an empty bottom band. Avoid placing critical small text directly
under the caption line, but allow imagery and cards to fill the frame.

## 23. Files and paths

Use generated UUIDs for projects and jobs:

```text
data/uploads/{project_id}/{asset_id}.png
output/{project_id}/{job_id}/...
output/{project_id}/{job_id}/renders/video.mp4
```

Store relative file keys in SQLite, such as:

```text
output/93caf919/.../renders/video.mp4
```

Do not store machine-specific absolute paths in database rows. This makes a
later move to object storage less disruptive.

## 24. Source URL and upload safety

Local MVP boundaries:

- Accept only `http` and `https` source URLs.
- Set network timeouts.
- Limit redirects and response size.
- Validate uploaded file extensions, MIME types, and sizes.
- Generate server-side filenames; ignore the user's path.
- Store uploads outside the SvelteKit source tree.
- Escape all user text inserted into HTML.
- Never execute user scripts.
- Freeze remote media locally before rendering.

Before SaaS launch, also block private, loopback, link-local, and cloud metadata
addresses to prevent server-side request forgery.

## 25. Local development loop

Initialize once:

```bash
.venv/bin/python -m api.db
```

Terminal 1 — API:

```bash
.venv/bin/fastapi dev api/app.py
```

Terminal 2 — worker:

```bash
.venv/bin/python -m api.worker
```

Terminal 3 — frontend:

```bash
cd web
npm run dev
```

Useful URLs:

```text
Dashboard: http://localhost:5173
API:       http://localhost:8000
API docs:  http://localhost:8000/docs
```

Keep the existing CLI available for pipeline-only debugging:

```bash
.venv/bin/python main.py --topic "Test topic" --plan plan.json --no-audio
```

## 26. Build order

Do not begin with the visual editor. First prove one complete path.

### Milestone 0: pipeline survives the move

- Copy the existing pipeline and required `.agents` assets.
- Install Python, Node, HyperFrames, and FFmpeg dependencies.
- Run the existing CLI with `--no-audio` first.
- Verify audio separately after the visual path works and local Whisper/Kokoro
  requirements are available.
- Run the existing pipeline tests:

  ```bash
  .venv/bin/python -m pytest
  ```

Done when the new repository produces the same snapshot/render as the old one.

### Milestone 1: project and job shell

- Add `schema.sql` and `api/db.py`.
- Add `GET /health`.
- Create/list/load projects.
- Add one SQLite-backed worker.
- Queue one existing pipeline run.
- Show job status and the finished video in SvelteKit.

Done when a topic can travel from browser to queued job to downloadable MP4.

### Milestone 2: template customization

- Convert the plan into editable scene records.
- Show scene thumbnails.
- Select existing deterministic templates.
- Edit text, colors, images, and one motion preset using normal Svelte forms.
- Queue a preview snapshot without model calls.

Done when changing a scene updates its snapshot without repeating research.

### Milestone 3: constrained GrapesJS editor

- Mount an empty GrapesJS editor.
- Add `hf-heading`, `hf-image`, `hf-stat-card`, `hf-quote`, and `hf-cta`.
- Save and reload GrapesJS JSON.
- Compile only those components through trusted Python renderers.
- Display the real compiled HyperFrames preview.

Done when a saved drag/drop design survives reload and renders identically.

### Milestone 4: product polish

- Caption presets.
- Upload validation.
- Useful error messages and retry button.
- Project duplication.
- Render history.
- Basic responsive dashboard layout.

Done when a non-developer can complete the workflow without using a terminal.

## 27. Minimum checks

Leave one small runnable check for each non-trivial boundary:

```text
Database initialization creates all tables
Foreign-key cascade removes a project's scenes/jobs
Only one worker can claim a queued job
Unknown GrapesJS component types are rejected
User text is HTML-escaped
Preview changes do not call research/planning
HyperFrames check passes for compiled scenes
Failed renders store a readable error
```

Frontend checks for the MVP can remain manual:

```text
Create project
Refresh and still see it
Edit and reload a scene
Watch queued/running/succeeded status
Open snapshot
Download MP4
```

Do not build a large test framework before these boundaries exist.

## 28. Definition of MVP complete

The MVP is complete when one local user can:

1. Start all three processes from documented commands.
2. Create a project from a topic or notes.
3. Generate and inspect source-backed research.
4. Edit the generated scenes.
5. Customize trusted frame components.
6. Select a caption preset.
7. Preview without repeating AI work.
8. Queue a render without blocking the API.
9. See a failure or success status.
10. Download a valid MP4.

## 29. When to replace MVP infrastructure

### Replace SQLite with PostgreSQL when

- API and workers need to run on different machines.
- The application has many simultaneous writers.
- Write-lock waits become measurable.
- User accounts require production backups and operational tooling.

### Add Redis and RQ when

- More than one render host is required.
- Job retries, priorities, monitoring, or scheduling outgrow the jobs table.
- Research and render workers need different scaling policies.

### Add object storage when

- API and render workers do not share one disk.
- Render history is too large for the host volume.
- Users need durable cloud downloads.

### Add authentication when

- Anyone beyond the trusted local operator can reach the application.

These are migrations triggered by real limits, not prerequisites for the MVP.

## 30. First task for the new repository

The first implementation task is only Milestone 0:

```text
Create the repo
Scaffold SvelteKit
Create the Python environment
Copy the existing pipeline and required assets
Run the CLI and existing tests
Commit the working baseline
```

Do not write FastAPI routes, SQLite tables, or GrapesJS components until the
renderer works unchanged in its new home. Installing the declared dependencies
is fine. A green baseline makes every later failure smaller and easier to
diagnose.

## 31. Official learning references

- [Create a SvelteKit project](https://svelte.dev/docs/kit/creating-a-project)
- [SvelteKit introduction](https://svelte.dev/docs/kit/introduction)
- [Svelte lifecycle and `onMount`](https://svelte.dev/docs/svelte/lifecycle-hooks)
- [Svelte Tailwind add-on](https://svelte.dev/docs/cli/tailwind)
- [Tailwind's SvelteKit guide](https://tailwindcss.com/docs/installation/framework-guides/sveltekit)
- [shadcn-svelte SvelteKit installation](https://shadcn-svelte.com/docs/installation/sveltekit)
- [shadcn-svelte sidebar](https://shadcn-svelte.com/docs/components/sidebar)
- [GrapesJS introduction](https://grapesjs.com/docs/)
- [GrapesJS components](https://grapesjs.com/docs/modules/Components.html)
- [GrapesJS blocks](https://grapesjs.com/docs/modules/Blocks)
- [GrapesJS storage](https://grapesjs.com/docs/modules/Storage.html)
- [FastAPI documentation](https://fastapi.tiangolo.com/)
- [Python `sqlite3` documentation](https://docs.python.org/3/library/sqlite3.html)
- [SQLite appropriate uses](https://www.sqlite.org/whentouse.html)
- [SQLite write-ahead logging](https://www.sqlite.org/wal.html)

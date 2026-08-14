# Local Runbook — Topic to Approved Video

This is the target command-line workflow after Milestones 1–3 are implemented. It demonstrates the complete API contract with the topic “affordable AI tools for small business owners.”

Pricing and product capabilities change. The request therefore defines “affordable,” asks for a retrieval date, and requires current official product pages. Do not publish the example by copying model output without reviewing its evidence.

## Prerequisites

- the repository implementation is complete through Milestone 3
- Python dependencies are installed in the repository-local `.venv`
- Node.js 22 or newer, Chrome/Chromium, FFmpeg, HyperFrames, Ollama, `curl`, and `jq` are available
- `video/composition/frame.md` is an exact copy of `handoff/video/frame.md`

The API intentionally has no authentication while it is a local single-user R&D tool. Do not bind it to a public network interface.

## 1. Create the Python virtual environment

From the repository root:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Install the pinned dependencies:

```bash
python -m pip install -r requirements.txt
```

Create the environment once. Activate it again in every new terminal used for the API or worker.

## 2. Start Ollama

In terminal one:

```bash
ollama serve
```

Pull the configured quality-first baseline once:

```bash
ollama pull gemma4:12b
```

The selected model may change after the Milestone 2 evaluation. `OLLAMA_MODEL` remains the runtime source of truth.

## 3. Start FastAPI

In terminal two, from the repository root:

```bash
source .venv/bin/activate
```

```bash
python -m uvicorn app.main:app --reload
```

## 4. Start the single worker

In terminal three, from the repository root:

```bash
source .venv/bin/activate
```

```bash
python -m app.worker
```

The worker performs research, planning, TTS, composition, checks, and rendering. FastAPI only validates requests and records commands in SQLite.

## 5. Create a video job

In terminal four:

```bash
API_URL="http://localhost:8000"
```

```bash
curl --fail-with-body --silent --show-error \
  --request POST "$API_URL/videos" \
  --header "Content-Type: application/json" \
  --data '{
    "title": "Affordable AI tools for small businesses",
    "topic": "Useful AI tools for a small business owner. Cover practical work such as writing, design, meeting notes, customer communication, or simple automation. Treat affordable as having a meaningful free tier or costing no more than $20 per month. Verify current capabilities and pricing with official product pages and preserve the date checked.",
    "audience": "Small business owners with limited technical experience",
    "learning_goal": "Help viewers identify three to five affordable AI tools and understand the practical job each one can perform.",
    "duration_seconds": 45,
    "format": "vertical",
    "research_mode": "auto",
    "image_policy": "open_license"
  }' \
  --output /tmp/video-create.json
```

Inspect the response:

```bash
jq . /tmp/video-create.json
```

Copy the returned ID:

```bash
JOB_ID="REPLACE_WITH_RETURNED_ID"
```

The expected initial response is:

```json
{
  "id": "01K...",
  "status": "queued"
}
```

## 6. Wait for the evidence review

Check status:

```bash
curl --fail-with-body --silent --show-error \
  "$API_URL/videos/$JOB_ID" | jq
```

Repeat until the job reaches:

```text
awaiting_evidence_review
```

The worker has now frozen sources and candidate assets and has stopped before scripting.

Download the current review document:

```bash
curl --fail-with-body --silent --show-error \
  "$API_URL/videos/$JOB_ID/review" \
  --output /tmp/evidence-review.json
```

Inspect proposed facts:

```bash
jq '.facts[] | {
  id,
  claim,
  evidence_excerpt,
  source_ids,
  approved
}' /tmp/evidence-review.json
```

Inspect the underlying sources:

```bash
jq '.sources[] | {
  id,
  publisher,
  title,
  url,
  published_at,
  retrieved_at,
  kind
}' /tmp/evidence-review.json
```

Inspect proposed assets and licenses:

```bash
jq '.assets[] | {
  id,
  creator,
  license,
  license_url,
  detail_url,
  attribution
}' /tmp/evidence-review.json
```

Record the review revision:

```bash
jq '.revision' /tmp/evidence-review.json
```

Manually verify each selected fact against its frozen evidence and each selected asset against its original license page. Never generate the approval list automatically.

Approve only the IDs that passed review, replacing the example IDs and revision:

```bash
curl --fail-with-body --silent --show-error \
  --request PATCH "$API_URL/videos/$JOB_ID/review" \
  --header "Content-Type: application/json" \
  --data '{
    "action": "approve_evidence",
    "approved_fact_ids": ["fact_01", "fact_02", "fact_04"],
    "approved_asset_ids": ["asset_01", "asset_03"],
    "revision": 1,
    "notes": "Claims checked against current official pages; asset rights verified."
  }' | jq
```

The worker may now give the local model only those approved ledger IDs.

## 7. Wait for the preview review

Poll the job again:

```bash
curl --fail-with-body --silent --show-error \
  "$API_URL/videos/$JOB_ID" | jq
```

Expected progression:

```text
planning -> previewing -> awaiting_preview_review
```

Download the expanded review document:

```bash
curl --fail-with-body --silent --show-error \
  "$API_URL/videos/$JOB_ID/review" \
  --output /tmp/preview-review.json
```

Inspect narration:

```bash
jq -r '.storyboard.scenes[].narration' /tmp/preview-review.json
```

Inspect scene decisions:

```bash
jq '.storyboard.scenes[] | {
  kind,
  variant,
  narrative_role,
  focal,
  fact_ids,
  asset_ids,
  transition_out,
  sfx,
  sfx_reason
}' /tmp/preview-review.json
```

Inspect technical results and preview locations:

```bash
jq '{revision, checks, previews}' /tmp/preview-review.json
```

Open the contact sheet and local HyperFrames preview reported under `previews`. Watch the complete timeline, not only the stills. Confirm:

- the hook and promised lesson are clear
- every claim uses an approved fact ID
- current prices retain their retrieval date and conditions
- images are useful rather than decorative
- captions and sources are readable at phone size
- motion directs attention or explains change
- transitions form one system
- every SFX has a visible reason

Approve the current preview revision:

```bash
curl --fail-with-body --silent --show-error \
  --request PATCH "$API_URL/videos/$JOB_ID/review" \
  --header "Content-Type: application/json" \
  --data '{
    "action": "approve_preview",
    "revision": 2,
    "notes": "Storyboard, contact sheet, narration, timing, motion, and sound approved."
  }' | jq
```

If it needs revision, do not approve it:

```bash
curl --fail-with-body --silent --show-error \
  --request PATCH "$API_URL/videos/$JOB_ID/review" \
  --header "Content-Type: application/json" \
  --data '{
    "action": "request_changes",
    "revision": 2,
    "notes": "Scene two is too text-heavy. Remove the sound on the ordinary caption entrance and regenerate the affected preview."
  }' | jq
```

The worker should invalidate only affected downstream artifacts. Repeat this section when the revised preview is ready.

## 8. Authorize the high-quality render

After preview approval:

```bash
curl --fail-with-body --silent --show-error \
  --request POST "$API_URL/videos/$JOB_ID/render" | jq
```

Expected response:

```json
{
  "id": "01K...",
  "status": "render_queued"
}
```

Poll until the candidate is ready:

```bash
curl --fail-with-body --silent --show-error \
  "$API_URL/videos/$JOB_ID" | jq
```

Expected progression:

```text
render_queued -> rendering -> awaiting_final_review
```

## 9. Download and watch the candidate

```bash
curl --fail-with-body --location \
  "$API_URL/videos/$JOB_ID/file" \
  --output /tmp/affordable-ai-tools-candidate.mp4
```

Verify that it is a plausible video file:

```bash
test -s /tmp/affordable-ai-tools-candidate.mp4
```

```bash
ffprobe \
  -v error \
  -show_entries format=duration,size \
  -show_entries stream=width,height,r_frame_rate \
  -of json \
  /tmp/affordable-ai-tools-candidate.mp4
```

Watch the whole candidate without scrubbing:

```bash
xdg-open /tmp/affordable-ai-tools-candidate.mp4
```

Check the final video against `handoff/video/QUALITY_GATES.md`. A valid MP4 is not automatically a good video.

## 10. Give final approval

Read the current final-review revision:

```bash
curl --fail-with-body --silent --show-error \
  "$API_URL/videos/$JOB_ID/review" | jq '{revision, status, candidate}'
```

Approve the watched revision:

```bash
curl --fail-with-body --silent --show-error \
  --request PATCH "$API_URL/videos/$JOB_ID/review" \
  --header "Content-Type: application/json" \
  --data '{
    "action": "approve_final",
    "revision": 3,
    "notes": "Watched completely on headphones and a laptop speaker; approved for local use."
  }' | jq
```

Final approval moves the checked deliverables into:

```text
output/JOB_ID/video.mp4
output/JOB_ID/FACTS.md
output/JOB_ID/CREDITS.md
output/JOB_ID/manifest.json
```

Confirm completion:

```bash
curl --fail-with-body --silent --show-error \
  "$API_URL/videos/$JOB_ID" | jq
```

The final status must be `complete`.

## Status summary

```text
queued
  -> researching
  -> awaiting_evidence_review       human approves facts and assets
  -> planning
  -> previewing
  -> awaiting_preview_review        human approves the assembled preview
  -> render_queued
  -> rendering
  -> awaiting_final_review          human watches the candidate MP4
  -> complete
```

## Common failure responses

- `400 Bad Request` — invalid topic, duration, format, or research-mode combination
- `404 Not Found` — unknown job or missing artifact
- `409 Conflict` — stale revision, wrong approval stage, unapproved evidence, stale preview, or render already running
- `422 Unprocessable Entity` — request JSON does not match the Pydantic contract
- `500 Internal Server Error` — unexpected application failure; inspect the worker error stored on the job

Never bypass a `409` by editing SQLite. Correct the review state or regenerate the affected artifact.

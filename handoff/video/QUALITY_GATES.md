# Video Quality Gates

Automated checks can prove a composition is valid. They cannot prove it is clear, tasteful, truthful, or worth publishing. Every job passes both automated and human gates.

## Gate order

```text
facts/assets
    -> brief/storyboard
    -> representative frames/contact sheet
    -> approved final timing and audio
    -> HyperFrames technical checks
    -> final watched render
    -> completed output
```

Do not skip ahead and promise to fix an earlier gate after rendering.

## Gate 0 — request and evidence

Pass when:

- the topic, audience, learning goal, format, and approximate duration are explicit
- research mode is valid for the supplied material
- every factual claim has approved fact IDs
- every online asset has an approved license/attribution record
- dates, units, versions, and jurisdictions are preserved
- AI, crypto, or other high-stakes content passes `../RESEARCH_POLICY.md`

Fail when the storyboard would need the model's memory to fill an important fact or visual.

## Gate 1 — story proposal

Present the storyboard as a scene table before composition work:

| Scene | Narrative job | Narration | Focal/technique | Facts/assets | Why it belongs |
|---|---|---|---|---|---|

Pass when:

- the message can be stated in one sentence
- value lands by the second scene
- every scene serves the message
- every scene has one idea and one focal
- the arc fits the audience and angle
- one direction block governs palette, transitions, captions, and negative rules
- one recurring motif is planted and resolved when appropriate
- one breather is named for videos longer than 25 seconds
- the optional spectacle beat appears once and serves the central proof/payoff
- narration is conversational and expected to fit the approximate duration
- scene kinds and variants exist in `SCENE_LIBRARY.md`

Fail when the plan is a list of facts, a transcript split into equal chunks, or unrelated visual novelty.

## Gate 2 — contact sheet

Compile approved templates into representative stills before final MP4 rendering.

Capture at least:

- one representative settled frame per scene
- one mid-reveal frame for every stat, process, compare, or annotated media scene
- opening hook at approximately 0.5 seconds
- the main proof/payoff frame
- caption-heavy frame
- outro readable hold

Review at full resolution and at phone-size preview.

### Frame checks

- focal is obvious within one second
- composition fills the frame without resembling a web card layout
- essential content stays inside safe areas
- headline, labels, sources, and captions meet `frame.md` sizes
- data encoding and labels are truthful
- visual hierarchy survives without decorative layers
- no scene appears accidentally unfinished during its reveal
- media crop preserves the evidence and context
- adjacent scenes feel related without being identical
- the recurring motif is recognizably the same element
- no banned pattern from `frame.md` appears

Human approval is required. A vision model may flag possible issues but cannot approve a contact sheet.

## Gate 3 — timing, narration, captions, and sound

Generate or finalize narration after the story and contact sheet are approved, then derive exact scene timing from the audio.

Pass when:

- every visual reveal lands on its narrated phrase
- speech sounds natural at the selected pace
- all names, acronyms, dates, and numbers are pronounced correctly
- captions match narration and stay within two lines
- captions do not obscure the focal, source label, or platform-safe region
- the viewer gets enough time to read every final state
- music remains beneath narration and can be removed without harming comprehension
- each SFX identifies one exact visible event
- no SFX marks a routine cut, fade, or caption
- silence is used where sound has no job

Listen once on headphones and once through a phone or laptop speaker.

## Gate 4 — HyperFrames technical validation

Use the current installed HyperFrames CLI syntax. Run `lint` during authoring as a fast iteration check. For the final technical gate, run from the job's HyperFrames project directory:

```bash
npx hyperframes check --snapshots
npx hyperframes preview
```

For motion-heavy templates, also run current animation/keyframe diagnostics when available.

Pass only when:

- `check` reports no errors
- there are no runtime exceptions
- there are no text collisions, overflows, unsafe contrast, or unexpected blank frames
- all media is local and resolves
- timing is deterministic and seek-safe
- repeated snapshots at the same timestamp match
- no network request occurs during rendering

Passing this gate does not approve aesthetics.

## Gate 5 — final render review

Render only after Gates 0–4 pass and the human approves the current HyperFrames preview:

```bash
npx hyperframes render --quality high --output ../video.mp4
test -s ../video.mp4
ffprobe -v error -show_format ../video.mp4
```

Watch the complete video without scrubbing, then watch again while checking:

- hook is immediately legible
- the promised lesson is delivered
- pacing has contrast instead of constant intensity
- no scene feels like a disconnected slide
- motion has a named job
- transitions form one system and the accent is earned
- numbers never display false intermediate or overshoot values
- source labels remain readable long enough
- captions and narration agree
- SFX and music make sense at their exact frames
- final takeaway and CTA are calm and complete
- no visual, factual, licensing, or rendering artifact remains

The candidate remains `awaiting_final_review` until a human watches it. Only final approval can mark the video `complete` and move it into `output/JOB_ID/`.

## Revision method

Make revisions converge:

1. Name one observed problem.
2. Freeze everything already working.
3. Change one variable or one layer.
4. State an absolute target rather than “more,” “less,” or “better.”
5. Re-capture only the affected frames first.
6. Re-run all downstream gates after approval.

Examples:

- Bad: “Make it more polished.”
- Good: “Keep composition and timing. Increase the stat from 96px to 132px and move the source label to y=1160.”
- Bad: “Make the transition smoother.”
- Good: “Keep the push direction. Change duration from 0.25s to 0.42s with `power2.inOut`.”

When a scene keeps failing, strip it to focal plus primary motion, approve that, then add one supporting layer at a time.

## Gold-standard acceptance test

Milestone 1 is complete only after one manually authored 30–45 second sourced vertical explainer passes all gates.

Score it from 1–5 on:

| Dimension | Passing standard |
|---|---|
| Teaching clarity | Viewer can state the lesson after one watch |
| Visual hierarchy | Focal is obvious in every representative frame |
| Phone readability | Essential copy and data remain readable at phone size |
| Motion meaning | Every major movement has a defensible narrative job |
| Continuity | Scenes feel like one Pūpūkahi film |
| Fact integrity | Every claim traces to approved evidence |
| Audio relevance | Narration, captions, music, and SFX agree |
| Brand fidelity | Frames match `frame.md` without generic AI-design tells |

No dimension may score below 4. The human reviewer writes one sentence explaining each score.

After approval, extract only the templates used by this video. Then render at least two new topics through the same templates and compare them with the gold standard before calling the system automated.

## Output completion

A completed job contains:

```text
output/JOB_ID/video.mp4
output/JOB_ID/FACTS.md
output/JOB_ID/CREDITS.md
output/JOB_ID/manifest.json
```

The manifest records the request revision, approved fact and asset IDs, storyboard revision, template versions, model/tag, HyperFrames version, render settings, hashes, stage durations, and human approval timestamp.

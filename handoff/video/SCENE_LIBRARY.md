# Pūpūkahi Scene Library

This document defines the only scene types the routine planner may emit. It is a contract for reviewed templates, not permission for an LLM to generate new HTML, CSS, SVG, or GSAP on every job.

## Core rule

The model chooses content and an approved scene kind. Deterministic code chooses layout and motion.

```text
validated Storyboard scene
    -> approved scene renderer
    -> Pūpūkahi tokens from frame.md
    -> seek-safe timeline
    -> representative snapshots
```

If none of these types communicates the idea honestly, stop for human direction. Do not silently invent a seventh type.

## Shared input contract

Every scene renderer receives validated data equivalent to:

```json
{
  "kind": "stat",
  "variant": "hero_number",
  "narrative_role": "prove the scale of the problem",
  "persuasion": "proof",
  "emotional_beat": "concern",
  "narration": "Exact spoken line.",
  "on_screen_text": ["Exact visible copy"],
  "fact_ids": ["fact_01"],
  "asset_ids": [],
  "data": {},
  "focal": "what the eye lands on",
  "supporting": ["context label"],
  "motion_purpose": "show_change",
  "reveal_cues": [],
  "transition_out": "primary",
  "sfx": "none",
  "sfx_reason": null
}
```

Renderers reject unknown fields that could become markup, selectors, code, URLs, or shell arguments. All visible text is inserted as text, never trusted HTML.

## Shared composition contract

- Read exact brand tokens from `frame.md`.
- Use one focal element at display scale.
- Add zero to two supporting elements only when they improve comprehension.
- Use structure and depth according to content; do not fill an arbitrary element quota.
- Apply safe areas at the renderer level.
- Use one paused, seek-safe deterministic timeline registered according to current HyperFrames rules.
- Network access is forbidden during rendering.
- Media paths resolve to approved frozen local assets only.
- Captions and source labels are framework-owned shared layers, not reimplemented by every scene.
- Transitions are composition-level handoffs, not custom exit animations inside each scene.
- Keep the final visible state readable long enough to understand.

## `hero`

### Job

Open the story, state a major lesson, or land the payoff with one memorable visual proposition.

### Approved variants

- `opening`: hook plus a planted recurring motif
- `lesson`: central takeaway during the body
- `payoff`: resolved motif plus final lesson

### Required

- 2–8 word focal phrase
- `narrative_role`
- one supporting visual or phrase at most
- exact motif behavior for `opening` or `payoff`

### Composition

- Display phrase occupies 60–80% of usable width.
- Use an edge anchor or intentional declaration center.
- A supporting mark, real object, or motif creates the second visual destination.
- Opening may use the inverted teal register.

### Motion

- One authored text entrance matched to tone.
- Supporting element begins while the focal settles.
- `payoff` may use the single spectacle beat if the storyboard grants it.
- No generic word-by-word kinetic type unless word order is the actual idea.

### Reject when

- the scene contains a data series, multi-step process, or two competing ideas
- the “supporting visual” is merely decorative clip art
- the headline needs to shrink below approved display scale

## `stat`

### Job

Make one approved number or a small related series tangible.

### Approved variants

- `hero_number`: one value and its meaning
- `ranked_bars`: two to four values on one shared scale
- `progress`: one bounded proportion with a meaningful denominator
- `change`: before/after value or a small time series

### Required

- approved fact IDs
- exact values, labels, units, and denominator where relevant
- source label
- statement of what comparison or change the viewer should notice

### Composition

- Use the approved HyperFrames `data-chart` block when it fits.
- Direct-label marks; do not add a legend when labels fit on marks.
- Keep marks large and the chart itself dominant.
- Axes, units, zero baselines, and ordering must remain truthful.
- A single number receives a visible quantity, proportion, or consequence—not just a numeral on an empty canvas.

### Motion

- Marks reveal in narration order.
- Values count only through truthful intermediate states.
- The next mark may start while the prior one settles.
- One restrained emphasis may land on the conclusion.
- Never overshoot a factual number.

### SFX

Optional soft click or pop on the final meaningful landing. No sound for every bar.

### Reject when

- units or denominators are unknown
- values are not directly comparable
- more than four marks are required for the claim
- a number is time-sensitive but has no date

## `compare`

### Job

Help the viewer choose, distinguish, or recognize a before/after, safe/risky, myth/fact, or option A/B relationship.

### Approved variants

- `split`: two states visible together
- `wipe`: one state transforms into another along a shared divider
- `shared_axis`: two options measured against the same criterion

### Required

- two named sides
- one shared comparison criterion
- approved facts or supplied examples supporting both sides
- exact conclusion the comparison earns

### Composition

- Use a clear 50/50 or 60/40 split with one dividing gesture.
- Keep equivalent information in equivalent positions.
- Do not make the preferred side larger before the evidence lands.
- Apply accent only when the narration reaches the conclusion.

### Motion

- Establish both sides quickly.
- Reveal corresponding differences together or in matched sequence.
- A wipe may carry the transition when the subject genuinely changes state.

### SFX

Usually none. One soft confirmation is allowed when a final choice visibly locks.

### Reject when

- the options use different criteria
- one side lacks evidence
- the scene is really a ranked multi-value chart

## `process`

### Job

Teach steps, a decision path, a checklist, a flow, or a sequence.

### Approved variants

- `steps`: two to four ordered actions
- `flow`: two to five connected nodes
- `checklist`: two to five recognizable checks
- `decision`: one branch with a small number of outcomes

### Required

- ordered step or node labels
- narration cue for every reveal
- start and successful end state
- factual or procedural source IDs when the steps are not purely user-provided

### Composition

- Use the approved `flowchart` or appropriate process block when available.
- Make the path itself the dominant structure.
- Keep future steps visible only when previewing them helps orientation.
- Do not turn steps into identical floating cards.

### Motion

- Draw or activate in the order the viewer should follow.
- The active step receives accent; completed steps remain legible but quieter.
- Connections grow toward their destination.
- A cursor, packet, check, or highlight may travel only if it represents a real operation.

### SFX

At most one meaningful confirmation or rule-out event. A click on every step is prohibited.

### Reject when

- the order does not matter
- the sequence needs more than five visible nodes
- branching becomes a dense flowchart that cannot be read on a phone

## `media`

### Job

Show real evidence: a photograph, screenshot, interface state, document excerpt, map, product, person, or local example.

### Approved variants

- `full_bleed`: one strong image with protected text region
- `split_context`: media plus one explanatory side
- `detail_focus`: crop or mask into the exact evidence
- `annotated`: one to three callouts on a frozen image

### Required

- approved asset ID and local path
- attribution/license record when applicable
- reason the asset teaches, proves, locates, demonstrates, or humanizes
- focal crop or annotation target

### Composition

- Preserve the meaningful part of the source.
- Use full-frame, split, or intentional crop; avoid a generic image card.
- Add at most three callouts.
- A screenshot must remain recognizable and must not fabricate UI.
- A quotation excerpt must remain faithful to the frozen source.

### Motion

- Use pan, crop, mask, or callout reveal only to direct attention.
- Do not animate a still photograph as if the depicted subject moved.
- Avoid generic Ken Burns movement unless the crop is traveling toward evidence.

### SFX

Normally none. A callout confirmation may use one soft cue.

### Reject when

- rights or attribution are unresolved
- the asset is a keyword-matched decoration
- the crop obscures evidence or misrepresents context
- the scene would require invented organic SVG artwork

## `outro`

### Job

Close the teaching loop and optionally invite the viewer to follow or learn more.

### Approved variants

- `takeaway`: final lesson only
- `follow`: takeaway plus one short account CTA

### Required

- final takeaway already supported by prior scenes
- exact organization name/handle if used
- recurring motif resolution when the storyboard planted one

### Composition

- Use the inverted register or warm canvas, whichever resolves the prior scene.
- Keep one dominant phrase and one small CTA maximum.
- Do not add a summary list, platform-logo wall, or new information.

### Motion

- Resolve the recurring motif.
- Use the simplest and slowest closure in the piece.
- Final fade is permitted after the readable hold.

### SFX

None by default. A single soft closure is allowed only when tied to the motif resolving.

### Reject when

- it repeats every prior point
- it introduces a new claim or urgent sales language
- it asks for engagement before delivering the takeaway

## Registry blocks and SVG

Use `hyperframes catalog` during template authoring and pin a named block when it matches the technique. Installed blocks are starting points with demo content that must be replaced and restyled.

The planner cannot decide “block or custom” at render time. That choice belongs to the reviewed template implementation.

Hand-authored SVG is limited to:

- chart marks
- diagram nodes and connectors
- paths, routes, masks, and simple geometric icons
- approved logo paths

Do not use SVG to invent people, buildings, landscapes, devices, screenshots, coins, dramatic editorial art, or decorative scenes.

## Adding a scene type or variant

Do not add one because a model requested it.

Add only when:

1. at least two real briefs cannot be communicated well by the existing library
2. the proposed type has a distinct narrative job
3. a human-authored example passes `QUALITY_GATES.md`
4. its inputs can be validated without accepting arbitrary markup or code
5. it is documented here before the planner schema permits it

Milestone 1 implements only the types and variants used by the gold-standard video. The list above is the allowed vocabulary, not a requirement to build every possibility immediately.

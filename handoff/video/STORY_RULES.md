# Pūpūkahi Story Rules

These rules govern what a video teaches, how it is organized, and how narration, visuals, motion, and sound agree. `frame.md` owns appearance. `SCENE_LIBRARY.md` owns approved implementations.

## Editorial promise

Pūpūkahi speaks like a knowledgeable neighbor helping someone make a safer or more informed decision.

- Teach one useful thing.
- Be specific without pretending certainty.
- Explain jargon the first time it matters.
- Prefer demonstration, comparison, and concrete steps over abstract claims.
- Never manufacture urgency, outrage, scarcity, or financial aspiration.
- Do not speak as an investor, attorney, doctor, regulator, or security incident responder.
- Never promise returns, safety, legality, or guaranteed outcomes.

## Required brief

Every video begins with an approved `BRIEF.md` or equivalent validated record containing:

```text
workflow: faceless-explainer
flow: automation
message: one sentence the film must prove
learning_goal: what the viewer can understand or do afterward
audience: one concrete audience
angle: concept | how_to | listicle | comparison | story
arc: named sequence of beats
mood: one energy or music descriptor
duration: approximate, because narration sets the final runtime
primary_transition: one named transition family
accent_transition: optional, with one named seam
motif: one recurring object, line, shape, or phrase
breather_scene: exactly one calmer scene for videos longer than 25 seconds
approved_fact_ids: list
approved_asset_ids: list
```

The brief is the decision artifact. Later stages do not reopen the original request and invent a different goal.

## Story shape

Use the smallest arc that teaches the subject.

Approved arcs:

| Angle | Default arc |
|---|---|
| Concept | Hook → Value → Explanation → Example → Takeaway |
| How-to | Hook → Outcome → Steps → Check → Takeaway |
| Listicle | Hook → Criteria → Items → Best/most important → Takeaway |
| Comparison | Hook → Decision → Shared axis → Evidence → Recommendation |
| Safety warning | Risk → Recognizable signs → Safe response → Where to verify |

The value or practical reason to care must land by the second scene. Evidence supports that value; evidence is not the opening inventory.

Three to seven scenes is the normal range for a 15–90 second piece. Use fewer scenes before shortening every scene into a rush.

## Hook

The first scene answers “why should I care?” in the audience's language.

- Use 2–8 on-screen words.
- Do not repeat the printed hook verbatim in narration.
- Do not open with a product name, file name, API name, definition, source title, or housekeeping.
- A number belongs in the hook only when the number itself carries the stakes and is already approved.
- No false curiosity gap. The video must deliver what the hook promises.

## One idea per scene

Every scene has one teachable focal. A scene may contain supporting evidence, but it cannot ask the viewer to understand two unrelated ideas.

A scene record must declare:

```text
kind: approved scene type
narrative_role: why this scene exists in the arc
persuasion: comparison | demonstration | enumeration | counterexample | proof | callback | distillation
emotional_beat: recognition | concern | curiosity | clarity | confidence | resolve
narration: exact spoken words
on_screen_text: exact visible copy
fact_ids: approved facts used
asset_ids: approved assets used
focal: one primary visual
supporting: zero to two supporting elements
background: optional structural or contextual treatment
motion_purpose: direct_attention | carry_continuity | show_change | express_character
reveal_cues: phrases or timestamps tied to visible events
transition_out: approved primary, approved accent, or cut
sfx: none or one approved effect
sfx_reason: exact visible event, required when sfx is not none
```

If `narrative_role` cannot be traced to the message, cut the scene. If `motion_purpose` cannot be explained in a complete sentence, cut the movement.

## Visual storytelling

- Show relationships instead of restating narration as text.
- A number needs a visible quantity, comparison, progress, or consequence.
- A process reveals in the order the viewer should perform or understand it.
- A comparison uses one shared axis or dividing gesture.
- A tutorial shows the interface, object, or sequence when a licensed/supplied example exists.
- On-screen text is an anchor, not a transcript. Captions carry the spoken wording.
- Do not use a chart where one large number or a direct comparison is clearer.
- Do not use imagery that merely matches a keyword. Every asset must teach, locate, demonstrate, or humanize something specific.

## Continuity

The film should feel like one system, not unrelated slides.

- Plant one recurring motif in the opening and pay it off later.
- Reuse a color field, line, object, framing edge, or motion vector across seams when useful.
- Keep related data in the same visual space and encoding. Change values before changing aesthetics.
- Vary composition when the narrative job changes, not merely to avoid repetition.
- Use one primary transition for most seams and one accent at most.
- Name one breather in videos longer than 25 seconds. Other scenes should continue developing until their idea lands.
- A spectacle beat is optional. If present, use exactly one and attach it to the central proof or payoff.

## Narration

Narration is the clock.

- Write for speech, not an essay.
- Use short sentences and contractions where natural.
- Define uncommon AI, crypto, security, or financial terms in plain language.
- Avoid stacked clauses, throat-clearing, and summary repetition.
- Pronounce abbreviations and numbers explicitly in the script when TTS might guess incorrectly.
- Generate TTS before final timing. Scene duration follows the actual audio plus intentional holds.
- Visual events land on spoken phrases. Narration does not wait for decorative animation.
- End on the useful takeaway, then an optional short nonprofit CTA. Do not insert a redundant recap.

Approximate narration target: 125–155 words per minute, adjusted after listening to the selected voice. Do not force speech to match a hard runtime by making it unnaturally fast.

## Captions and on-screen copy

- Burn in captions for short-form delivery.
- Keep captions inside the safe region defined by `frame.md`.
- Use phrase-level or word-aware timing from the narration track.
- Highlight only the word currently carrying meaning, using the approved accent.
- Keep captions to two lines maximum.
- Do not duplicate a large headline with identical caption text at the same moment; rephrase narration or suppress the duplicate caption segment when comprehension remains intact.
- Quote user-provided or source wording exactly only when explicitly marked as a quotation and approved.

## Motion

Allowed motion jobs:

1. direct attention
2. carry continuity
3. show change
4. express Pūpūkahi's calm, helpful character

Execution rules:

- Focal information arrives first or never waits behind decorative elements.
- Supporting entrances overlap while the focal settles; they do not form a slow queue.
- Use transforms for spatial motion and preserve seek-safe deterministic timelines.
- Overshoot applies to physical transforms, never to factual counters.
- Do not animate every property at once. Position plus opacity is often enough.
- A held frame may be fully still. An idle requires a truthful reason.
- Never use unseeded randomness or time-dependent animation.

## Transitions

- Primary transition appears on most related seams.
- Accent transition appears once at a genuine topic change or climax.
- A hard cut is correct when continuity already comes from a shared visual or spoken phrase.
- The outgoing and incoming scenes hand off at the same time. Do not fade one away, pause, and then start the next.
- Transition duration follows energy: approximately 0.3–0.5s for this calm educational style.
- Do not invent unsupported transition names.

## Sound

- Narration leads the mix.
- Music is optional and must not compete with speech.
- SFX mark one visible event: a count landing, selection confirming, path connecting, or warning being ruled out.
- Cuts, fades, and captions do not earn an SFX by default.
- Use no effect when the reason is weak.
- Keep effect frequency around one per six seconds and never stack two within one second.
- Review with headphones and a phone speaker.

## Facts and safety

- Only approved fact IDs may support factual narration or on-screen copy.
- Preserve conditions, dates, units, uncertainty, and scope from the source.
- Do not convert correlation into causation or advice into a guarantee.
- AI capability, product, law, regulation, price, platform policy, and security guidance are time-sensitive.
- Crypto content is education, not a recommendation to buy, sell, hold, stake, bridge, or connect a wallet.
- High-stakes content requires the additional rules in `../RESEARCH_POLICY.md` and human approval.

## Storyboard approval gate

Before authoring or compiling a final composition, present:

1. the message and arc
2. a scene table with `narrative_role`, focal, narration, fact IDs, and technique
3. the recurring motif and where it returns
4. the primary and optional accent transition
5. the one breather and optional spectacle beat
6. expected duration based on narration

Do not final-render an unapproved storyboard. Follow `QUALITY_GATES.md` after compilation.

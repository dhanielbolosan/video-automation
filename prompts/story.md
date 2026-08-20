Plan a $length-second faceless explainer video.

Topic: $topic
Canvas: $canvas
Frames: exactly $frame_count, about ${per_frame}s each.
Spoken length: about $words words per frame.

## Source notes — the factual boundary

Every claim in the video must come from these notes. Invent no prices, figures,
percentages, dates, or guarantees. If the notes contain no number, the video
contains no number.

$source_material

## Rules

- Frame 1 is the hook: open on the tension, the cost, or the surprising claim.
  Never a greeting, never "in this video", never a title card. Its role is `Hook`.
- The sequence comes from narrative design, not the order of the notes above —
  reorder, merge, omit, compress.
- One idea per frame. The last frame is the CTA ending slide: land the one rule,
  then close with the exact on-screen copy `Follow @pupukahi_tech for more content.`.
  Set its `type` to `cta` and its `role` to `CTA`; do not end on a generic payoff
  with no follow instruction.
- `voiceover` is the spoken line, in plain spoken English, about $words words.
  Punctuate normally so the voice breathes. No em dashes or en dashes.
- `scene` is a one-line caption of what the viewer sees. You are not designing
  the frame here and you write no HTML.
- `type` is the explainer beat enum: `hook`, `pain_point`, `product_intro`,
  `feature_showcase`, `benefit_highlight`, `social_proof`, `branding`, or `cta`.
- `persuasion` names the clarity technique that makes this frame land, and
  `beat` names the viewer's target feeling. Do not use vague labels such as
  "explanation" or "positive".
- `narrative_role` says what this frame changes in the viewer's understanding;
  `key_message` is the one sentence they should remember from it.
- `slug` names what the frame is ABOUT in one or two kebab-case words: `hook`,
  `time-cost`, `one-rule`. It becomes the filename, so `frame1` or `scene-2`
  tells a later reader nothing. Never number it.
- `role` labels the beat so the next step can pick its shot shape.
- `transition_in` is the seam INTO each frame. Frame 1 is always `cut`.
- `music` is a two or three word BGM mood, or exactly `none` for a silent video.
- Keep time-sensitive claims safe: do not put exact prices, plan names, usage
  limits, dates, or guarantees in the voiceover unless the notes explicitly
  verify them. When a fact can change, say to check the current plan.

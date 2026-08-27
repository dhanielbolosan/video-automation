Create one structured plan for a ${length}-second portrait social explainer.

Topic: $topic
Scenes: exactly $frame_count, roughly $seconds seconds each.

Source notes are the factual boundary. Invent no numbers, prices, limits, dates,
or guarantees that are absent from them:

$notes

Design grammar:

- This is dark technical editorial motion, not a website or slide deck.
- Choose exactly one `kind`: `hero`, `stat`, `rank`, `compare`, `process`,
  `interface`, or `media`. The renderer owns every graphic; never describe or
  generate SVG, HTML, CSS, coordinates, or animation code.
- Choose a `variant` from: `headline`, `metric`, `ranked-bars`, `split`,
  `steps`, `screen`, `split-media`, or `default`.
- Choose `catalog_item` only when an allowlisted registry move genuinely fits;
  otherwise use `none`. Catalog IDs are semantic inputs, not permission to
  reproduce their demo content.
- When source notes contain `[F1]`, `[F2]`, and similar research IDs, copy the
  supporting IDs into `fact_ids` for that scene. Never cite an ID that is absent
  from the notes. Use an empty list for human notes without IDs and for the CTA.
- `motion_purpose` must be one of `orient`, `prove`, `compare`, `sequence`,
  `demonstrate`, or `reveal` and describe what the motion explains.
- One dominant headline and one proof object per scene. The proof object must
  gain information in the order the voiceover explains it.
- Headlines are hooks, not summaries: three to six words, 64 characters at
  most. Put supporting context in the subhead.
- Subheads are one short sentence of twelve words or fewer.
- `items`: zero to three concise evidence rows; each label/value should stay under six words.
- Use `rank` only when the numerical ranking itself is the claim. Never use a
  bare list ordinal merely because an item appears first or fifth.
- `compare` uses exactly two items; `process` uses exactly three sequential
  items; `interface` uses two or three UI/status rows.
- The first scene is a hook, never a greeting or title card. Do not repeat one
  kind for more than two consecutive scenes.
- The final scene is forced to the branded CTA by the renderer. Do not put CTA
  copy, logo, platform names, or follow language in earlier scenes.
- If the topic promises a numbered list, every promised item must appear. When
  there are only N+1 scenes for N items, combine the hook with item one rather
  than dropping an item or using an item as the CTA.
- Use `push-slide LEFT` as the normal transition. Reserve `zoom-through` for one major reveal.
- On-screen fields are concise and do not duplicate the full voiceover.
- Spoken copy is plain, useful, and specific. No hype and no em dashes.

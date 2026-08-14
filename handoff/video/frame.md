---
name: "Pūpūkahi Tech"
format:
  primary: "1080x1920"
  aspect_ratio: "9:16"
  fps: 30
colors:
  canvas: "#FCFAF8"
  ink: "#1D2930"
  accent: "#196D76"
  accent_light: "#39A1AC"
  data_secondary: "#D19847"
  highlight_once: "#EE7C2B"
  structure: "#D7D1C8"
  muted_ink: "rgba(29, 41, 48, 0.62)"
typography:
  display_family: "Archivo Black"
  body_family: "IBM Plex Sans"
  data_family: "IBM Plex Mono"
  display_weight: 400
  body_weight: 400
  body_emphasis_weight: 600
spacing:
  safe_left: 120
  safe_right: 120
  safe_top: 140
  safe_bottom: 420
  unit: 16
components:
  structural_rule: "2px solid #D7D1C8"
  micro_rule: "1px solid #1D2930"
  maximum_radius: 8
  shadow: "none"
---

# Pūpūkahi frame system

This is the normative visual source of truth for every Pūpūkahi video. Frontmatter values are exact. Do not round colors, substitute fonts, create a dark theme, or introduce a second brand.

Pūpūkahi Tech is a local Hawaii nonprofit helping the community understand AI, crypto and digital safety, practical technology, and local business tools. The visual voice is a knowledgeable neighbor showing something clearly: warm, grounded, useful, and never hype-driven.

This file defines brand, not scene layout. `STORY_RULES.md` chooses the narrative job and `SCENE_LIBRARY.md` chooses an approved composition.

## Canvas and safe areas

Primary delivery is 1080 × 1920 at 30fps.

- Keep critical content at least 120px from the left and right edges.
- Keep critical content at least 140px from the top.
- Keep all critical content above the bottom 420px reserved for social UI.
- Put embedded captions primarily between y=1260 and y=1450, adjusting upward when a scene's focal occupies that region.
- Never put source labels, captions, or CTA text beneath platform controls.
- Landscape is an explicit alternate composition, not a crop of the vertical frame.

## Color discipline

The default register is warm canvas `#FCFAF8` with ink `#1D2930` and ocean teal `#196D76`.

The inverted register is ocean teal `#196D76` with warm canvas `#FCFAF8`. Use it for the opening, the main payoff, or the outro—but normally no more than two scenes in one video.

Rules:

- Teal is the primary focal accent.
- `#D19847` exists only when data genuinely needs a second series.
- `#EE7C2B` is one exceptional highlight in the entire video: a warning, selected answer, or climax. It is not general decoration.
- Prefer scale, weight, inversion, cropping, or density before adding another color.
- Tint neutrals toward the warm canvas or teal. Avoid dead neutral gray.
- Do not use full-screen linear gradients. Use a solid field or a localized radial wash when depth needs it.
- All meaningful text must meet WCAG AA contrast in the rendered frame.

## Typography

### Display

- Archivo Black, sentence case.
- Typical headline: 88–144px.
- Hero word or short phrase: 140–220px.
- Line height: 0.88–1.02.
- Tracking: approximately `-0.02em`.
- Prefer 2–7 words. Break intentionally; never auto-shrink a paragraph into a hero slot.
- A display headline should occupy roughly 60–80% of the usable width when it is the focal element.

### Body

- IBM Plex Sans, 40–54px.
- Limit a body block to about 2 short lines on a moving frame.
- Use weight 600 for emphasis rather than a new color where possible.

### Data and chrome

- IBM Plex Mono.
- Data values: 44–88px depending on role.
- Labels and metadata: 24–32px.
- Visible source label: 22–26px, never smaller.
- Uppercase chrome may use `0.12em–0.16em` tracking.
- Captions: 44–56px with an opaque or high-contrast treatment that survives busy imagery.

Text below 24px is not allowed unless it is nonessential texture. A source label is essential and therefore cannot be nonessential texture.

## Frame composition

Video frames are not web pages.

Every substantive scene should plan these roles as the content requires:

1. **Focal:** the one thing the viewer must understand now, at display scale.
2. **Supporting:** one or two elements that provide context or proof on their own cues.
3. **Structure:** rules, labels, a source mark, registration details, or a recurring motif that organizes the frame.
4. **Depth:** background, content, and foreground separation when it clarifies hierarchy or continuity.

Use asymmetric 60/40 or edge-anchored compositions by default. Centering is reserved for a deliberate declaration, solemn hold, count landing, or final lockup.

Fill the frame. A tiny centered card surrounded by empty canvas is not minimalism; it is an unfinished web layout.

Structural elements should normally be 2px at 1080p. A 1px rule is allowed only at high contrast and cannot carry essential hierarchy by itself.

Cards are not the default container. If content has no reason to be a card, do not put it in one.

## Background treatment

The warm canvas needs physical presence without becoming ornamental noise.

Allowed treatments:

- fine paper or film grain at 3–6%
- one localized teal radial wash at 15–22%
- a sparse data grid when the subject is genuinely spatial or quantitative
- oversized cropped typography that repeats real content, not arbitrary filler
- one recurring line, dot, frame edge, or route motif used across scenes

Background movement is optional. It must pass the same meaning test as foreground motion. A static educational figure does not become “live” merely because the background breathes.

## Media treatment

- Prefer user-supplied or licensed real photographs and screenshots over fake AI illustration.
- Crop for the narrative focal, not merely to fill a rectangle.
- Preserve faces, product UI, and important evidence from caption or interface overlap.
- Use full-bleed, split-frame, masked reveal, or edge crop; avoid a generic floating-photo card.
- Do not apply a generic dark overlay to every image. Treat each source for readability while keeping it recognizable.
- Never invent a person, place, logo, interface, quotation, or source mark in SVG.

## Information graphics

- Direct-label chart marks instead of using a separate legend where possible.
- Use no more than four marks or three rows in a fast scene unless the visual explicitly reveals them over time.
- A meaningful value must remain readable at the frame where narration states it.
- A visual encoding must match the claim: position/length for comparison, sequence for process, area only when area is truly meaningful, route for travel or transmission.
- Use approved HyperFrames registry blocks when they match the job.
- Hand-authored SVG is allowed for chart marks, connectors, paths, simple icons, masks, and logo geometry.
- Organic illustration, characters, landscapes, and painterly scenes require a supplied or generated image asset.

## Motion character

Pūpūkahi motion is calm, direct, and physically coherent.

- A movement must direct attention, carry continuity, show change, or express the brand's helpful character.
- Reveal information when narration says it.
- Favor decisive `power2`/`power3` entrances and calm `sine` holds over elastic or playful bounce.
- Overshoot is for objects with implied mass, never for factual values.
- Use one camera move only when it preserves spatial continuity or reveals a relationship.
- A held scene may be still. Add an idle only when the content is genuinely ongoing or the movement carries continuity.
- Avoid simultaneous entrances. Supporting information should overlap the focal's settling motion on shorter stagger offsets.

## Transition character

- Primary: clean directional push or restrained blur, normally 0.3–0.5s.
- Accent: at most one iris or cinematic zoom into the central proof or payoff.
- Hard cut: preferred when a shared object, shape, phrase, or motion vector already provides continuity.
- Outro: simple closure, slower than the body.
- The transition is the exit. Do not fade the outgoing scene away before starting the transition.
- Do not use a different transition on every seam.

## Audio character

Narration is primary. Music is optional.

- SFX mark a visible event, never a routine cut or caption.
- One effect per scene maximum and roughly one effect per six seconds across the video.
- No two effects within one second.
- A cue must identify the exact tween and frame it accompanies.
- Silence is preferable to an effect with no narrative job.

## Attribution and brand marks

- Every numerical, ranked, quoted, legal, safety, or time-sensitive claim receives a compact source label in the scene when practical.
- Full sources and asset credits accompany the video manifest and posting draft.
- Use the exact organization name `PŪPŪKAHI TECH` only.
- Do not invent or redraw a logo. Use an approved local logo asset if one exists; otherwise use the organization name typographically.
- The outro may ask viewers to follow or learn more, but it may not introduce a new factual claim.

## Banned patterns

- dark or Night theme
- purple-to-blue AI gradients
- glassmorphism or neon glow
- left-edge accent stripes on generic cards
- grids of identical cards used as filler
- tiny centered content floating in empty space
- ghost numerals unrelated to the actual information
- status pills and colored dots with no real status
- emoji as iconography
- fake browser chrome
- generic stock-photo placeholders
- illustration-like SVG people or scenery
- unsourced statistics or quotes
- a different palette, font, or transition per scene
- motion added merely because a frame feels empty
- SFX on fades, routine captions, or every cut
- the phrases “game-changer,” “seamless,” “unlock,” or “in today’s fast-paced world”

## Frame acceptance

A representative frame passes only when:

- the focal is obvious at phone size
- the frame remains recognizable as Pūpūkahi with the logo removed
- essential text is readable and inside safe areas
- data can be understood within about two seconds
- decoration can be removed without destroying comprehension
- source and license obligations are satisfied
- no banned pattern is present

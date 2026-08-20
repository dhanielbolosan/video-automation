# Your frame packet

$packet

---

# Dispatch

- PROJECT canvas: ${width}x${height}
- frame_id: $frame_id — this frame runs ${duration}s
- Captions are ON. $keepout
- Write this frame only, as a sub-composition. Open with exactly these two lines:

```
<template>
  <div id="root" data-composition-id="$frame_id" data-width="$width" data-height="$height" style="width:${width}px;height:${height}px;position:relative;overflow:hidden">
```

- Register exactly one paused timeline at `window.__timelines["$frame_id"]`.
- Every `id` you write must be prefixed `$id_prefix` — for example
  `${id_prefix}headline`. Ids must be unique across the whole assembled page,
  because every frame is concatenated into one document. The prefix starts with a
  letter on purpose: an id beginning with a digit makes `querySelector("#…")`
  throw a SyntaxError, so never open an id with a number.
- The frame's full-bleed ground is a `class="clip"` layer, never `#root`. A
  background on the root is dropped by the compositor and the frame renders black.
- Put every `<style>` and `<script>` inside the `<template>`.
- **Never set an initial `transform` in CSS on an element you then tween with
  GSAP.** The CSS value and the tween fight, and GSAP overwrites the whole
  transform — a `translateX(-50%)` centering silently disappears. Put the start
  state in the tween: `gsap.fromTo(el, { scale: 0.8 }, { scale: 1 })`.
- **The render must be deterministic.** No `Math.random()`, no `Date.now()`, no
  `new Date()`. When you need scatter or jitter, derive it from the element's
  index — `(i * 37) % 100` and the like — so every render is identical.
- **Never declare `@font-face`.** Both brand families are already bundled by the
  compiler; a declaration pointing at `assets/fonts/…` 404s and the frame falls
  back to a system face, which is the most visible defect there is.
- Only core GSAP is loaded — no plugins. Never tween `text`, `innerText`,
  `scrambleText`, `drawSVG` or `morphSVG`. Never `import` anything, never
  reference a URL. No `repeat: -1` — use a finite count.
- Every selector you tween must match an element you actually wrote. A tween on a
  missing selector leaves its target at `opacity: 0` forever and the frame
  renders blank.
- Simultaneous sibling `.clip` elements must use distinct `data-track-index`
  values; clips on one track may not overlap. Keep a shared track only for
  sequential, non-overlapping clips.
- Give every `.clip` a stable prefixed `id` so the Studio and automated checks
  can target it.
- On-screen text is not the narration: captions already carry every spoken word.
  No text element runs past about eight words.
- Do not use emoji as iconography. Do not build a dashboard of equal cards,
  decorative pills, or tiny filler labels. Give the frame one large focal idea,
  one supporting graphic, and enough contrast to read at 1080x1920.
- For a `cta` frame, end with a centered lockup above the bottom 420px keepout:
  the exact copy `Follow @pupukahi_tech for more content.` and inline SVG icons
  in this order: TikTok, LinkedIn, Instagram. Use no external image or URL.
- Keep embedded text sparse and distinct from captions. Never place a full
  narration sentence in the artwork when the caption rail already says it.

Answer with the complete file and nothing else. Start at `<template` and stop at
`</template>`. No markdown fence, no explanation.

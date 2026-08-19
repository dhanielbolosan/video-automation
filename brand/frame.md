---
version: alpha
name: "Pūpūkahi — Frame"
description: >
  A warm editorial frame system for Pūpūkahi Tech explainers: knowledgeable,
  neighbourly, practical, and never hyped.
unit: "the frame — 1080x1920 primary at 30fps"
principle: "brand atoms are fixed · composition follows the lesson"

colors:
  canvas: "#fcfaf8"
  ink: "#1d2930"
  accent: "#196d76"
  hair: "#e7e2da"
  muted: "rgba(29,41,48,0.55)"

data_colors:
  accent-light: "#39a1ac"
  sand: "#d19847"
  sunset: "#ee7c2b"

typography:
  display: { fontFamily: "Archivo Black", cqw: 10.5, weight: 400, lineHeight: 0.92, tracking: "-0.02em" }
  headline: { fontFamily: "Archivo Black", cqw: 7.2, weight: 400, lineHeight: 0.96, tracking: "-0.02em" }
  body: { fontFamily: "IBM Plex Mono", cqw: 3.1, weight: 400, lineHeight: 1.35 }
  label: { fontFamily: "IBM Plex Mono", cqw: 2.2, weight: 500, tracking: "0.14em", upper: true }
  data: { fontFamily: "IBM Plex Mono", cqw: 2.6, weight: 500, lineHeight: 1.2 }

spacing:
  edge: "120px"
  platform-ui-bottom: "420px"
  caption-height: "240px"
  gap: "32px"

components:
  hairline:
    border: "1px solid #e7e2da"
    rounded: "0"
    shadow: "none"
  declare-register:
    backgroundColor: "#196d76"
    textColor: "#fcfaf8"
    use: "opening and payoff only"
  caption-rail:
    backgroundColor: "#fcfaf8"
    textColor: "#1d2930"
    activeBackground: "#196d76"
    activeText: "#fcfaf8"
    mutedText: "rgba(29,41,48,0.55)"
    border: "1px solid #e7e2da"
    rounded: "0"
    shadow: "none"
    placement: "overlay ending 420px above the portrait canvas bottom"
---

# Pūpūkahi frame system

## Character

Pūpūkahi Tech is a Hawaiʻi nonprofit helping the community use AI and crypto
and supporting local businesses. The visual voice is a knowledgeable neighbour
showing you something: warm, plain, specific, useful, and never hyped.

This file defines the brand's appearance. It does not choose the story, frame
count, layout sequence, teaching device, narration, sources, or sound design.

## Canvas

- The primary canvas is 1080 × 1920 at 30fps.
- Keep important content at least 120px from every edge.
- Keep authored text, marks, and focal graphics out of the bottom 420px, where
  platform UI sits. Background treatments may continue through it.
- Captions overlay the composition immediately above that exclusion. They do
  not create a footer or shift the visual center upward.

## Color

Use the exact frontmatter values. The ground is warm canvas, never pure white;
ink is the text color; ocean teal is the normal accent. `accent-light` and
`sand` are data-series colors only. `sunset` is one decisive highlight per
video at most.

The declare register inverts the frame to teal ground and warm-canvas text. Use
it only for the opening or payoff. A frame commits to one register. Outside a
data comparison, use one accent hue per frame.

## Type

- Archivo Black is the sole display face: sentence case, tight tracking, one
  dominant display element per frame.
- IBM Plex Mono carries body copy, labels, data, metadata, and chrome. Labels
  are uppercase with wide tracking.
- Name the fonts explicitly. Never use Inter, Roboto, or `system-ui`.
- Keep body copy at least 32px and display copy at least 72px on the portrait
  canvas unless a deliberately oversized graphic makes another scale clearer.

## Surface

- Flat editorial plane: no shadows, glass, soft elevation, or radius above 4px.
- Use 1px hairlines for structure. Avoid dashboard-like grids of equal cards.
- A localized radial teal wash is welcome. Never use a full-screen linear
  gradient.
- Add fine film grain at 3–6% opacity using `multiply`.
- Graphics may fill or crop against the frame. Avoid placing the idea inside a
  polite centered panel.
- Motion should reveal or transform the idea. Do not add idle wobble, pulsing,
  or floating merely to keep the frame busy.

## Caption appearance

Use the installed caption rail. Upcoming words are muted ink, the active word
uses a flat teal block with warm-canvas text, and spoken words settle to ink.
Embedded display words should be sparse so they do not duplicate the rail.

## Visual tells to avoid

- left-edge accent stripes on cards
- grids of identical panels
- ghost numerals behind text
- status pills with colored dots
- emoji as iconography
- purple-to-blue gradients, glassmorphism, neon glow
- stock-photo-shaped placeholders
- decorative pseudo-Hawaiian motifs or tourist clichés
- em dashes or en dashes in on-screen text

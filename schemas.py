"""The shapes the model is allowed to answer in.

These go into `output_config.format`, which constrains the response to the
schema at the API level. Two consequences worth knowing:

- `enum` is a guarantee, not a hint. Every field where the workflow has a closed
  vocabulary — blueprint ids, motion rule names, transitions, narrative roles —
  is an enum, so the model cannot name something the downstream Node scripts
  would reject.
- `required` plus `additionalProperties: false` makes a missing field impossible
  rather than caught later. There is no normalizer in this pipeline.

Blueprint ids and rule names are read off disk at import time, so the schema
tracks whatever the installed skills actually ship.
"""

from __future__ import annotations

import docs

# `transitions.mjs` owns the seam vocabulary. Frame 1 is always `cut`.
TRANSITIONS = [
    "cut",
    "crossfade",
    "blur-crossfade",
    "push-slide LEFT",
    "push-slide RIGHT",
    "push-slide UP",
    "push-slide DOWN",
    "zoom-through",
    "squeeze",
]

EXPLAINER_TYPES = [
    "hook",
    "pain_point",
    "product_intro",
    "feature_showcase",
    "benefit_highlight",
    "social_proof",
    "branding",
    "cta",
]

# The blueprint menu is indexed by narrative role, so the story layer naming its
# role is what lets the next step pick a proven shape instead of inventing one.
ROLES = [
    "Hook",
    "Problem",
    "Product_Intro",
    "Key_Feature",
    "Benefits",
    "Social_Proof",
    "CTA",
    "Brand_Outro",
]


def storyboard(frame_count: int) -> dict:
    """The story layer. No visuals, no motion, no HTML."""
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["message", "arc", "audience", "music", "frames"],
        "properties": {
            "message": {"type": "string", "minLength": 8},
            "arc": {"type": "string", "minLength": 8},
            "audience": {"type": "string", "minLength": 4},
            # `none` is the canonical fully-silent marker; anything else is a BGM
            # mood string the audio step looks up.
            "music": {"type": "string"},
            "frames": {
                "type": "array",
                "minItems": frame_count,
                "maxItems": frame_count,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "title",
                        "slug",
                        "role",
                        "type",
                        "persuasion",
                        "beat",
                        "narrative_role",
                        "key_message",
                        "scene",
                        "voiceover",
                        "delivery",
                        "duration_s",
                        "transition_in",
                    ],
                    "properties": {
                        "title": {"type": "string", "minLength": 2},
                        "slug": {"type": "string", "pattern": "^[a-z][a-z0-9-]*$"},
                        "role": {"type": "string", "enum": ROLES},
                        "type": {"type": "string", "enum": EXPLAINER_TYPES},
                        "persuasion": {"type": "string", "minLength": 4},
                        "beat": {"type": "string", "minLength": 3},
                        "narrative_role": {"type": "string", "minLength": 8},
                        "key_message": {"type": "string", "minLength": 8},
                        "scene": {"type": "string", "minLength": 8},
                        "voiceover": {"type": "string", "minLength": 8},
                        "delivery": {"type": "string"},
                        "duration_s": {"type": "number", "minimum": 0.5},
                        "transition_in": {"type": "string", "enum": TRANSITIONS},
                    },
                },
            },
        },
    }


def visual_design(frame_count: int) -> dict:
    """Each frame's blueprint choice and its time-coded shot sequence.

    The model picks a shape and paces it; it still writes no HTML. `scenes` is
    the answer to a frame that finishes arriving and then freezes: every entry is
    a window with something landing in it.
    """
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["direction", "frames"],
        "properties": {
            "direction": {
                "type": "object",
                "additionalProperties": False,
                "required": ["current", "primary_transition", "notes"],
                "properties": {
                    # One dominant direction for the whole film. Other vectors
                    # mean something; they are not variety.
                    "current": {"type": "string", "enum": ["LEFT", "RIGHT", "UP"]},
                    "primary_transition": {"type": "string", "enum": TRANSITIONS},
                    "notes": {"type": "string"},
                },
            },
            "frames": {
                "type": "array",
                "minItems": frame_count,
                "maxItems": frame_count,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": [
                        "frame",
                        "blueprint",
                        "focal",
                        "roles",
                        "rules",
                        "scenes",
                    ],
                    "properties": {
                        "frame": {"type": "integer"},
                        "blueprint": {
                            "type": "string",
                            "enum": docs.blueprint_ids(),
                        },
                        "focal": {"type": "string", "minLength": 3},
                        "roles": {
                            "type": "array",
                            "minItems": 1,
                            "maxItems": 4,
                            "items": {"type": "string"},
                        },
                        # 2-4 rules per scene is the animation skill's guidance;
                        # the packet builder's byte limit trims from here.
                        "rules": {
                            "type": "array",
                            "minItems": 1,
                            "maxItems": 4,
                            "items": {"type": "string", "enum": list(docs.rule_names())},
                        },
                        "scenes": {
                            "type": "array",
                            "minItems": 2,
                            "maxItems": 5,
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": ["at_s", "shows"],
                                "properties": {
                                    "at_s": {"type": "number"},
                                    "shows": {"type": "string", "minLength": 6},
                                },
                            },
                        },
                    },
                },
            },
        },
    }

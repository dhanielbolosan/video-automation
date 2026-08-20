"""The faceless-explainer workflow, driven from Python by cheap cloud models.

This follows `.agents/skills/faceless-explainer/SKILL.md` step for step. The
division of labour is the skill's own, not an invention here:

  Step 0-2  scaffold, brief, design system   `hyperframes init`, `build-frame.mjs`
  Step 3    storyboard + script              MODEL — one schema-constrained call
  Step 3.1  narration, word timings, BGM     `audio.mjs`
  Step 4    visual design                    MODEL — one schema-constrained call
  Step 5    build frames + assemble          MODEL — one call per frame, IN PARALLEL
  Step 6    gate + render                    `hyperframes check` / `render`

Four of the six steps use no model at all — they call the workflow's own
deterministic scripts. Of the three that do, two answer against a JSON schema and
cannot emit a shape the next step would reject; the third writes frame HTML,
which is text by nature and therefore the one place a model can still be wrong in
a way no schema catches.

Step 5 fans out. That is the workflow's own instruction ("dispatch one sub-agent
per frame, in parallel if possible") and it is the reason this runs in minutes.

Run `.venv/bin/python main.py --help` after installing requirements.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import docs
import llm
import schemas

ROOT = Path(__file__).resolve().parent
BRAND = ROOT / "brand" / "frame.md"
DEFAULT_NOTES = ROOT / "notes" / "example.md"

RESOLUTIONS = {
    "instagram-reels": ("portrait", "1080x1920"),
    "tiktok": ("portrait", "1080x1920"),
    "youtube-shorts": ("portrait", "1080x1920"),
    "instagram-feed": ("square", "1080x1080"),
    "youtube": ("landscape", "1920x1080"),
}

# Kokoro lands near 2.6 words a second. The real narration sets the final clock in
# step 5, so this only has to be close enough to plan against.
WORDS_PER_SECOND = 2.6


# ── shell ────────────────────────────────────────────────────────────────────


def run(command: list[str], cwd: Path, timeout: int = 3600) -> str:
    printable = " ".join(command[:4])
    print(f"run: {printable}…", flush=True)
    done = subprocess.run(
        command, cwd=cwd, capture_output=True, text=True, timeout=timeout
    )
    if done.returncode != 0:
        raise RuntimeError(
            f"{printable} failed ({done.returncode}):\n"
            f"{(done.stderr or done.stdout)[-3000:]}"
        )
    return done.stdout


def node(name: str, *args: str, cwd: Path, timeout: int = 3600) -> str:
    return run(["node", docs.script(name), *args], cwd, timeout)


def hyperframes(*args: str, cwd: Path, timeout: int = 3600) -> str:
    return run(["npx", "--yes", "hyperframes", *args], cwd, timeout)


def load_dotenv(path: Path = ROOT / ".env") -> None:
    """Read `.env` so credentials do not have to be exported by hand.

    Empty values are skipped deliberately. `ANTHROPIC_API_KEY=` with nothing
    after it still wins its slot in the SDK's credential precedence and
    authenticates with an empty key — which shadows a perfectly good OAuth
    profile and fails as a 401 that looks like a bad key rather than a missing
    one. A blank line in `.env` should mean "I have not set this", so it does.
    """
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip().strip("'\"")
        if value:
            os.environ.setdefault(key.strip(), value)


def check_tools() -> None:
    for binary, hint in (
        ("node", "install Node.js 22+"),
        ("npx", "install Node.js 22+"),
        ("ffmpeg", "install FFmpeg"),
    ):
        if not shutil.which(binary):
            raise RuntimeError(f"{binary} is not on PATH ({hint}).")
    if not shutil.which("whisper-cli") and not shutil.which("whisper-cpp"):
        print(
            "warning: whisper-cpp is not on PATH — narration gets no word "
            "timings, so captions will be skipped.",
            flush=True,
        )


def slugify(value: str, limit: int = 60) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not slug:
        raise ValueError("topic must contain a letter or number")
    return slug[:limit].rstrip("-")


def next_project_dir(output_dir: Path, topic: str) -> Path:
    """Return the next versioned project directory under the repo output root."""
    output_root = (ROOT / "output").resolve()
    requested = output_dir.resolve()
    if requested != output_root:
        raise ValueError(f"--output must be exactly {output_root}")

    base = slugify(topic)
    # Treat an old unversioned project as v1 while it is being migrated.
    version = 2 if (output_root / base).exists() else 1
    while (output_root / f"{base}-v{version}").exists():
        version += 1
    return output_root / f"{base}-v{version}"


# ── steps 0-2: scaffold, brief, design system ────────────────────────────────


def scaffold(
    project: Path,
    topic: str,
    destination: str,
    length: int,
    preset: str = "biennale-yellow",
    voice: str = "af_heart",
) -> None:
    """`hyperframes init`, BRIEF.md, and the two files the design step reads.

    `init` refuses a non-empty directory, so everything else is written after it.
    The `blank` example is deliberate: every other example carries a look, and
    the look is the design system's job.
    """
    resolution, canvas = RESOLUTIONS[destination]
    project.parent.mkdir(parents=True, exist_ok=True)
    hyperframes(
        "init",
        project.name,
        "--example",
        "blank",
        "--resolution",
        resolution,
        "--skill",
        "faceless-explainer",
        "--non-interactive",
        cwd=project.parent,
        timeout=900,
    )
    (project / "BRIEF.md").write_text(
        f"""# BRIEF — {topic}

- workflow: faceless-explainer
- flow: automation
- storyboard: no
- message: {json.dumps(topic, ensure_ascii=False)}
- destination: {destination}
- aspect: {canvas}
- language: en
- audience: local small businesses and nonprofit teams
- length: {length}s
- angle: listicle
- captions: on
- voice: {voice}
- style_preset: {preset}

## Intent

A faceless explainer. No footage and no capture — every visual is invented per
frame from the design system in `frame.md`.

## Constraints

Pricing, limits, and features change: no exact prices, plan names, or usage
limits unless a human verifies them immediately before publishing. Educational
only — no revenue, savings, or investment promises.
""",
        encoding="utf-8",
    )
    print(f"step 0: scaffolded {project}", flush=True)


def synthetic_capture(
    project: Path, topic: str, source_material: str, use_brand: bool = True
) -> None:
    """A faceless explainer captures nothing, so the two files the design step
    reads are written directly: the brand's tokens and the topic text."""
    extracted = project / "capture" / "extracted"
    extracted.mkdir(parents=True, exist_ok=True)
    # `build-frame.mjs` remixes the chosen preset toward these, which is how the
    # brand palette survives adopting a shipped preset. With --no-brand the
    # synthetic capture must stay neutral or the preset is still remixed.
    tokens = {
        "title": topic,
        "description": "A practical faceless explainer for local learners.",
        "colors": ["#fcfaf8", "#1d2930", "#196d76", "#e7e2da", "#d19847"]
        if use_brand
        else [],
        "fonts": [
            {"family": "Archivo Black", "weights": [400]},
            {"family": "IBM Plex Mono", "weights": [400, 500, 600]},
        ]
        if use_brand
        else [],
        "colorStats": [],
    }
    (extracted / "tokens.json").write_text(
        json.dumps(tokens, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (extracted / "visible-text.txt").write_text(
        f"{topic}\n\n{source_material}\n", encoding="utf-8"
    )
    print("step 1: wrote synthetic tokens.json and visible-text.txt", flush=True)


def design_system(project: Path, preset: str, use_brand: bool) -> None:
    """`build-frame.mjs` adopts a preset and brand-remixes it into `frame.md`.

    With `--brand`, the confirmed spec replaces the generated file afterwards.
    The preset still runs first because it is what writes the caption skin the
    caption step reads.
    """
    node("build-frame", "--hyperframes", ".", "--preset", preset, cwd=project, timeout=600)
    if use_brand:
        if not BRAND.is_file():
            raise RuntimeError(f"--brand needs {BRAND}, which is missing.")
        shutil.copyfile(BRAND, project / "frame.md")
        patch_caption_skin(project)
        print("step 2: installed the confirmed brand spec over the preset", flush=True)


def patch_caption_skin(project: Path) -> None:
    """Dissolve the preset's caption pill into bare text over the film.

    The preset draws captions in a bordered pill. Social captions read better
    with no container at all — one short line, spoken words in ink, the current
    word in the accent, the rest muted — so the box is removed and only the word
    states carry meaning. Portrait also gets the stage lifted clear of the bottom
    420px of platform UI.
    """
    skin_path = project / ".hyperframes" / "caption-skin.html"
    if not skin_path.is_file():
        return
    skin = skin_path.read_text(encoding="utf-8")
    media_rule = "  @media (max-aspect-ratio: 9/16) {\n"
    if media_rule not in skin:
        return
    brand = """  /* Brand overrides: bare text, no caption box. */
  .caption-pill {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    max-width: 100% !important;
  }
  .caption-line {
    font-family: "Archivo Black", sans-serif !important;
    text-shadow: 0 2px 10px rgba(252, 250, 248, 0.85);
  }
  .caption-word { color: rgba(29, 41, 48, 0.45) !important; }
  .caption-word.is-active {
    color: #196d76 !important;
    background: transparent !important;
    box-shadow: none !important;
  }
  .caption-word.is-spoken {
    color: #1d2930 !important;
    background: transparent !important;
    box-shadow: none !important;
  }

"""
    portrait = """    .caption-stage {
      top: auto;
      bottom: 420px;
      height: 240px;
    }
    .caption-pill { max-width: calc(100% - 240px) !important; }
"""
    skin_path.write_text(
        skin.replace(media_rule, brand + media_rule + portrait, 1), encoding="utf-8"
    )
    print("step 2: patched the caption skin to bare brand text", flush=True)


# ── step 3: storyboard and script ────────────────────────────────────────────


def plan_story(
    model: llm.Model,
    project: Path,
    topic: str,
    source_material: str,
    canvas: str,
    length: int,
    frame_count: int,
    voice: str,
) -> dict:
    """One call for the whole story layer. No visuals, no motion, no HTML."""
    per_frame = round(length / frame_count, 1)
    plan = model.plan(
        "step3-story",
        docs.prompt(
            "story",
            length=length,
            topic=topic,
            canvas=canvas,
            frame_count=frame_count,
            per_frame=f"{per_frame:g}",
            words=round(per_frame * WORDS_PER_SECOND),
            source_material=source_material,
        ),
        schemas.storyboard(frame_count),
    )
    plan["frames"] = [
        {**frame, "frame_id": f"{index:02d}-{frame['slug']}"}
        for index, frame in enumerate(plan["frames"], start=1)
    ]
    write_storyboard(project, plan, canvas, length)
    write_script(project, plan, voice)
    print(f"step 3: {len(plan['frames'])} frames planned", flush=True)
    return plan


def write_storyboard(
    project: Path, plan: dict, canvas: str, length: int, design: dict | None = None
) -> None:
    """Render STORYBOARD.md in the documented format.

    Python owns the markdown so the model never has to produce a parseable file.
    Called twice — once for the story layer, again with the visual design merged
    in. Same path, edited in place, never a second storyboard.
    """
    by_frame = {int(entry["frame"]): entry for entry in (design or {}).get("frames", [])}

    def one_line(value: object) -> str:
        return " ".join(str(value).split())

    role_types = {
        "Hook": "hook",
        "Problem": "pain_point",
        "Product_Intro": "product_intro",
        "Key_Feature": "feature_showcase",
        "Benefits": "benefit_highlight",
        "Social_Proof": "social_proof",
        "CTA": "cta",
        "Brand_Outro": "branding",
    }
    lines = [
        "---",
        f"format: {canvas}",
        f"duration: {length}s",
        f"message: {json.dumps(plan['message'])}",
        f"arc: {json.dumps(one_line(plan['arc']), ensure_ascii=False)}",
        f"audience: {json.dumps(one_line(plan['audience']), ensure_ascii=False)}",
        f"music: {json.dumps(one_line(plan['music']), ensure_ascii=False)}",
        "mode: autonomous",
        "---",
        "",
    ]
    for number, frame in enumerate(plan["frames"], start=1):
        lines += [
            f"## Frame {number} — {frame['title']}",
            "",
            f"- scene: {json.dumps(one_line(frame['scene']), ensure_ascii=False)}",
            f"- duration: {frame['duration_s']:g}s",
            f"- transition_in: {frame['transition_in']}",
            f"- status: {frame.get('status', 'outline')}",
            f"- voiceover: {json.dumps(frame['voiceover'])}",
            f"- role: {frame['role']}",
            f"- type: {frame.get('type') or role_types.get(frame['role'], 'feature_showcase')}",
            f"- persuasion: {json.dumps(one_line(frame.get('persuasion', 'Progressive disclosure')), ensure_ascii=False)}",
            f"- beat: {json.dumps(one_line(frame.get('beat', 'comprehension')), ensure_ascii=False)}",
            f"- src: compositions/frames/{frame['frame_id']}.html",
        ]
        narrative_role = frame.get("narrative_role") or frame.get("narrativeRole")
        key_message = frame.get("key_message") or frame.get("keyMessage")
        if narrative_role:
            lines += ["", f"narrativeRole: {one_line(narrative_role)}"]
        if key_message:
            lines.append(f"keyMessage: {one_line(key_message)}")
        shot = by_frame.get(number)
        if shot:
            lines += [
                f"- blueprint: {shot['blueprint']}",
                f"- focal: {json.dumps(one_line(shot['focal']), ensure_ascii=False)}",
                f"- roles: {json.dumps(', '.join(one_line(role) for role in shot['roles']), ensure_ascii=False)}",
                f"- rules: {', '.join(shot['rules'])}",
            ]
        lines += ["", one_line(frame["scene"]), ""]
        if shot:
            lines += ["**Shot sequence**", ""]
            lines += [
                f"- Scene at {scene['at_s']:g}s: {one_line(scene['shows'])}"
                for scene in shot["scenes"]
            ]
            lines.append("")

    if design:
        lines += [
            "## Video direction",
            "",
            f"- current: {design['direction']['current']}",
            f"- primary_transition: {design['direction']['primary_transition']}",
            "",
            design["direction"]["notes"],
            "",
        ]
    (project / "STORYBOARD.md").write_text("\n".join(lines), encoding="utf-8")


def write_script(project: Path, plan: dict, voice: str) -> None:
    """SCRIPT.md — the locked narration. The TTS step reads the indented lines."""
    if plan["music"].strip().lower() == "none" and not any(
        frame["voiceover"].strip() for frame in plan["frames"]
    ):
        return  # the canonical silent marker: `music: none` and no SCRIPT.md
    lines = [
        f"# SCRIPT — {project.name}",
        "",
        f"**Voice:** {voice} (Kokoro, local)",
        "**Voice direction:** Warm, plain, specific. Never hyped.",
        "",
        "---",
        "",
    ]
    clock = 0.0
    for number, frame in enumerate(plan["frames"], start=1):
        end = clock + frame["duration_s"]
        lines += [
            f"## Line {number} — {frame['title']} (Frame {number})",
            "",
            f"**Time:** {clock:.1f} – {end:.1f}s",
            f"**Delivery:** {frame.get('delivery') or 'Plain and unhurried.'}",
            "",
            f"    {frame['voiceover']}",
            "",
        ]
        clock = end
    (project / "SCRIPT.md").write_text("\n".join(lines), encoding="utf-8")


# ── step 3.1: audio ──────────────────────────────────────────────────────────


def make_audio(project: Path, voice: str) -> bool:
    """Narration, word timings, and BGM mood lookup. False if silent."""
    if not (project / "SCRIPT.md").is_file():
        print("step 3.1: no SCRIPT.md — project is silent, skipping", flush=True)
        return False
    whisper_path = os.environ.get("HYPERFRAMES_WHISPER_PATH")
    if not whisper_path or not Path(whisper_path).is_file():
        cached_whisper = (
            Path.home()
            / ".cache"
            / "hyperframes"
            / "whisper"
            / "whisper.cpp"
            / "build"
            / "bin"
            / "whisper-cli"
        )
        whisper_path = str(cached_whisper) if cached_whisper.is_file() else None
    audio_env = {
            # `audio.mjs` runs Kokoro through a Python interpreter it has to
            # locate; without this it cannot import kokoro_onnx and does not
            # treat that as fatal — it writes an empty `voices` list and the run
            # continues to a silent video with no word timings and no captions.
            "HYPERFRAMES_PYTHON": sys.executable,
            "HEYGEN_API_KEY": "",
            "HYPERFRAMES_API_KEY": "",
            "ELEVENLABS_API_KEY": "",
            "HEYGEN_CONFIG_DIR": str((project / ".kokoro-only").resolve()),
    }
    if whisper_path:
        audio_env["HYPERFRAMES_WHISPER_PATH"] = whisper_path
    os.environ.update(audio_env)
    out = node(
        "audio",
        "--script", "./SCRIPT.md",
        "--storyboard", "./STORYBOARD.md",
        "--hyperframes", ".",
        "--out", "./audio_meta.json",
        "--voice", voice,
        cwd=project,
        timeout=3600,
    )
    print(out.strip()[-1500:], flush=True)

    meta = project / "audio_meta.json"
    if not meta.is_file():
        raise RuntimeError("audio.mjs wrote no audio_meta.json.")
    voices = json.loads(meta.read_text(encoding="utf-8")).get("voices") or []
    if not voices:
        raise RuntimeError(
            "audio.mjs produced no narration (empty `voices`), so there would be "
            "no word timings and no captions. Check that "
            f"`{sys.executable} -c 'import kokoro_onnx'` works."
        )
    word_count = sum(len(voice.get("words") or []) for voice in voices)
    if word_count:
        print(
            f"step 3.1: {len(voices)} narration clip(s), {word_count} timed words",
            flush=True,
        )
    else:
        print(
            f"step 3.1: {len(voices)} narration clip(s) without word timings; "
            "captions will be skipped",
            flush=True,
        )
    return True


# ── step 4: visual design ────────────────────────────────────────────────────


def design_frames(
    model: llm.Model, project: Path, plan: dict, canvas: str, length: int
) -> dict:
    """Pick each frame's blueprint and pace its reveals across the full duration.

    Both vocabularies handed over — blueprint ids and motion rule names — are read
    off the installed skills and enforced as schema enums, so the model cannot
    name a shape or a move that does not exist. The skill is explicit about the
    second one: do not invent motion names.
    """
    roster = "\n".join(
        f"- Frame {number} ({frame['role']}, {frame['duration_s']:g}s): "
        f"{frame['title']} — says: {frame['voiceover']}"
        for number, frame in enumerate(plan["frames"], start=1)
    )
    design = model.plan(
        "step4-visual",
        docs.prompt(
            "visual",
            canvas=canvas,
            length=length,
            roster=roster,
            blueprint_menu=docs.blueprint_menu(),
            rule_menu=docs.rule_menu(),
        ),
        schemas.visual_design(len(plan["frames"])),
    )
    write_storyboard(project, plan, canvas, length, design)
    for frame, shot in zip(plan["frames"], design["frames"]):
        print(f"step 4: {frame['frame_id']} → {shot['blueprint']}", flush=True)
    return design


# ── step 5: build frames, in parallel ────────────────────────────────────────


def build_frames(
    model: llm.Model, project: Path, plan: dict, canvas: str, has_audio: bool
) -> list[str]:
    """Sync the real clock, build the packets, then author every frame at once.

    `frame-packets.mjs` is what makes each call tractable: a packet already
    contains that frame's storyboard block, its blueprint's full template, and
    every rule recipe it cited. The model instantiates slots — it is not designing
    from scratch, and it never sees another frame.
    """
    if has_audio:
        node(
            "audio", "sync-durations",
            "--audio-meta", "./audio_meta.json",
            "--storyboard", "./STORYBOARD.md",
            cwd=project, timeout=600,
        )
        node(
            "audio", "fetch-sfx",
            "--storyboard", "./STORYBOARD.md",
            "--hyperframes", ".",
            cwd=project, timeout=900,
        )

    trim_packets(project)
    node(
        "frame-packets",
        "--project", str(project.resolve()),
        "--storyboard", str((project / "STORYBOARD.md").resolve()),
        cwd=project, timeout=600,
    )

    # The role contract and the design system are identical for every frame, so
    # they become one cached system prompt rather than N copies of the same bytes.
    role = f"{docs.worker_role(project)}\n\n## Design system (`frame.md`)\n\n{docs.frame_md(project)}"
    width, height = canvas.split("x")
    keepout = (
        "Keep authored text, marks, and focal graphics out of the bottom 420px."
        if int(height) > int(width)
        else "Keep authored content clear of the caption overlay band."
    )
    durations = frame_durations(project)

    jobs = []
    for frame in plan["frames"]:
        frame_id = frame["frame_id"]
        duration = durations.get(frame_id, frame["duration_s"])
        jobs.append(
            (
                frame_id,
                role,
                docs.prompt(
                    "frame",
                    packet=docs.frame_packet(project, frame_id),
                    width=width,
                    height=height,
                    frame_id=frame_id,
                    duration=f"{duration:g}",
                    keepout=keepout,
                    # The frame id starts with its ordinal, and an id opening with
                    # a digit makes `querySelector("#01-hook-x")` throw.
                    id_prefix=f"f{frame_id}-",
                ),
            )
        )

    print(f"step 5: authoring {len(jobs)} frames in parallel", flush=True)
    answers = model.authored_in_parallel(jobs)

    frames_dir = project / "compositions" / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    failed = []
    for frame_id, answer in sorted(answers.items()):
        if isinstance(answer, Exception):
            print(f"step 5: {frame_id} FAILED — {answer}", flush=True)
            failed.append(frame_id)
            continue
        html = extract_template(answer)
        if html is None:
            print(f"step 5: {frame_id} FAILED — no <template> in the answer", flush=True)
            failed.append(frame_id)
            continue
        html = repair(html, frame_id)
        error = script_syntax_error(html)
        if error is not None:
            print(f"step 5: {frame_id} FAILED — {error}", flush=True)
            failed.append(frame_id)
            continue
        (frames_dir / f"{frame_id}.html").write_text(html, encoding="utf-8")
        mark_frame_status(project, frame_id, "animated")
        print(f"step 5: {frame_id} written ({durations.get(frame_id, 0):g}s)", flush=True)

    if has_audio:
        node(
            "captions", "build",
            "--storyboard", "./STORYBOARD.md",
            "--audio-meta", "./audio_meta.json",
            "--hyperframes", ".",
            "--out", "./caption_groups.json",
            cwd=project, timeout=1200,
        )
    node("assemble-index", "--storyboard", "./STORYBOARD.md", "--hyperframes", ".", cwd=project, timeout=600)
    node("transitions", "inject", "--storyboard", "./STORYBOARD.md", "--hyperframes", ".", cwd=project, timeout=600)
    return failed


def trim_packets(project: Path) -> None:
    """Drop cited rules until every frame's packet will fit.

    The packet builder inlines a frame's whole blueprint body plus every rule
    recipe, and hard-fails over 48,000 bytes. The blueprint is the dominant cost
    and not negotiable — `kinetic-type-beats` alone is 29 KB — so the rules give
    way. Dropping the largest first keeps the most moves.
    """
    path = project / "STORYBOARD.md"
    blocks = re.split(r"(?m)^(?=## Frame )", path.read_text(encoding="utf-8"))
    for index, block in enumerate(blocks):
        cited = re.search(r"(?m)^- rules:[ \t]*(.+)$", block)
        blueprint = re.search(r"(?m)^- blueprint:[ \t]*(\S+)$", block)
        if not cited or not blueprint:
            continue
        rules = [r.strip() for r in cited.group(1).split(",") if r.strip()]
        budget = (
            docs.PACKET_LIMIT
            - len(block.encode())
            - 2_000  # the builder's own header and section scaffolding
            - docs.blueprint_bytes(blueprint.group(1))
        )
        kept = sorted(rules, key=docs.rule_bytes)
        while kept and sum(docs.rule_bytes(r) for r in kept) > budget:
            dropped = kept.pop()
            print(
                f"step 5: {blueprint.group(1)} is large — dropping rule "
                f"`{dropped}` ({docs.rule_bytes(dropped)} bytes) to fit the packet",
                flush=True,
            )
        if kept != rules:
            ordered = [r for r in rules if r in kept]
            blocks[index] = block.replace(
                cited.group(0), f"- rules: {', '.join(ordered) or 'none'}"
            )
    path.write_text("".join(blocks), encoding="utf-8")


def repair(html: str, frame_id: str) -> str:
    """Fix mechanical frame faults before they reach the browser gate.

    Everything else a frame can get wrong is a judgment call the gate reports and
    a human decides on. These repairs are mechanical, so spending a retry on them
    would be paying a model to do arithmetic.
    """
    # `frame.md` documents the brand faces, so an author copies its @font-face
    # declarations faithfully — at paths this project does not have. The result is
    # a 404 per face and the frame rendering in a fallback, which is the most
    # visible defect there is. The compiler bundles both families already.
    html, faces = re.subn(r"\s*@font-face\s*\{[^}]*\}", "", html)
    if faces:
        print(f"step 5: {frame_id} — removed {faces} @font-face block(s)", flush=True)

    # A CSS initial transform on an element GSAP also tweens: `lint` rejects it,
    # and GSAP overwrites the whole transform so the CSS value is discarded. A
    # percentage translate is left alone — that is usually centering.
    scripts = " ".join(re.findall(r"<script[^>]*>(.*?)</script>", html, re.DOTALL))
    dropped: list[str] = []

    def drop(match: re.Match[str], element_id: str) -> str:
        if element_id not in scripts or "%" in match.group("value"):
            return match.group(0)
        dropped.append(element_id)
        return ""

    html = re.sub(
        r"<[^>]*\bid=\"(?P<id>[^\"]+)\"[^>]*\bstyle=\"[^\"]*\btransform:[^\"]*\"[^>]*>",
        lambda tag: re.sub(
            r"\s*transform:\s*(?P<value>[^;\"']+);?",
            lambda m: drop(m, tag.group("id")),
            tag.group(0),
        ),
        html,
    )
    html = re.sub(
        r"#(?P<id>[A-Za-z][\w-]*)\s*\{[^}]*\btransform:[^}]*\}",
        lambda rule: re.sub(
            r"\s*transform:\s*(?P<value>[^;}]+);?",
            lambda m: drop(m, rule.group("id")),
            rule.group(0),
        ),
        html,
    )
    for element_id in dropped:
        print(
            f"step 5: {frame_id} — dropped a CSS transform on #{element_id} "
            "that GSAP also tweens",
            flush=True,
        )

    # Workers often give simultaneous sibling clips the same track. HyperFrames
    # correctly rejects that overlap; move only the later colliding sibling to a
    # fresh lane and preserve the author's original lanes everywhere else.
    lanes: dict[int, list[tuple[float, float]]] = {}
    clip_tags = list(
        re.finditer(
            r"<(?P<tag>[^>]*\bclass=[\"'][^\"']*\bclip\b[^\"']*[\"'][^>]*)>",
            html,
            re.IGNORECASE,
        )
    )
    originals = []
    for tag in clip_tags:
        match = re.search(r'\bdata-track-index=["\'](\d+)["\']', tag.group("tag"))
        if match:
            originals.append(int(match.group(1)))
    next_lane = max(originals, default=-1) + 1
    replacements: list[tuple[int, int, str]] = []
    for tag in clip_tags:
        source = tag.group("tag")
        start = re.search(r'\bdata-start=["\']([\d.]+)["\']', source)
        duration = re.search(r'\bdata-duration=["\']([\d.]+)["\']', source)
        track = re.search(r'\bdata-track-index=["\'](\d+)["\']', source)
        if not (start and duration and track):
            continue
        begin, end = float(start.group(1)), float(start.group(1)) + float(duration.group(1))
        lane = int(track.group(1))
        occupied = lanes.setdefault(lane, [])
        if any(begin < other_end and end > other_begin for other_begin, other_end in occupied):
            lane = next_lane
            next_lane += 1
            source = re.sub(
                r'(\bdata-track-index=["\'])\d+(["\'])',
                rf'\g<1>{lane}\g<2>',
                source,
                count=1,
            )
            replacements.append((tag.start("tag"), tag.end("tag"), source))
        lanes.setdefault(lane, []).append((begin, end))
    for start, end, replacement in reversed(replacements):
        html = html[:start] + replacement + html[end:]
    if replacements:
        print(
            f"step 5: {frame_id} — moved {len(replacements)} overlapping clip(s) "
            "to separate tracks",
            flush=True,
        )
    return html


def extract_template(answer: str) -> str | None:
    match = re.search(r"<template[^>]*>.*</template>", answer, re.DOTALL)
    return match.group(0) if match else None


def script_syntax_error(html: str) -> str | None:
    """Parse every inline script with `node --check` before the file is written.

    A syntax error caught here is one frame to re-run; the same error found by
    the browser gate costs a whole build cycle.
    """
    for body in re.findall(r"<script[^>]*>(.*?)</script>", html, re.DOTALL):
        if not body.strip():
            continue
        done = subprocess.run(
            ["node", "--check", "-"], input=body, capture_output=True, text=True, check=False
        )
        if done.returncode != 0:
            return (done.stderr or "").strip().splitlines()[-1][:200]
    return None


def frame_durations(project: Path) -> dict[str, float]:
    """The real per-frame clock, after `sync-durations` wrote the voice's timing."""
    text = (project / "STORYBOARD.md").read_text(encoding="utf-8")
    durations = {}
    for block in re.split(r"(?m)^(?=## Frame )", text):
        src = re.search(r"(?m)^- src:\s*compositions/frames/([\w.-]+)\.html", block)
        duration = re.search(r"(?m)^- duration:\s*([\d.]+)s", block)
        if src and duration:
            durations[src.group(1)] = float(duration.group(1))
    return durations


def mark_frame_status(project: Path, frame_id: str, status: str) -> None:
    """Advance the storyboard status when the expected frame artifact exists."""
    path = project / "STORYBOARD.md"
    blocks = re.split(r"(?m)^(?=## Frame )", path.read_text(encoding="utf-8"))
    needle = f"compositions/frames/{frame_id}.html"
    for index, block in enumerate(blocks):
        if needle not in block:
            continue
        updated, count = re.subn(
            r"(?m)^- status:\s*\S+",
            f"- status: {status}",
            block,
            count=1,
        )
        if count:
            blocks[index] = updated
            path.write_text("".join(blocks), encoding="utf-8")
        return


def snapshot_times(project: Path) -> str:
    """Return one midpoint per storyboard frame for a useful contact sheet."""
    total = 0.0
    midpoints: list[str] = []
    text = (project / "STORYBOARD.md").read_text(encoding="utf-8")
    for block in re.split(r"(?m)^(?=## Frame )", text):
        match = re.search(r"(?m)^- duration:\s*([\d.]+)s", block)
        if not match:
            continue
        duration = float(match.group(1))
        midpoints.append(f"{total + duration / 2:.2f}")
        total += duration
    return ",".join(midpoints) or "0"


def rendered_duration(path: Path) -> float | None:
    """Read the muxed duration when ffprobe is available."""
    if not shutil.which("ffprobe"):
        return None
    done = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if done.returncode != 0:
        raise RuntimeError(f"ffprobe could not read {path.name}: {done.stderr.strip()}")
    try:
        duration = float(done.stdout.strip())
    except ValueError as exc:
        raise RuntimeError(f"ffprobe returned no duration for {path.name}") from exc
    if duration <= 0:
        raise RuntimeError(f"rendered file has an invalid duration: {duration}")
    return duration


# ── step 6: gate and render ──────────────────────────────────────────────────


def finalize(project: Path, render: bool, force: bool) -> dict:
    """`check` must pass before a render."""
    result: dict[str, object] = {"project": str(project)}
    try:
        print(hyperframes("check", cwd=project, timeout=2400)[-4000:], flush=True)
        result["check"] = "passed"
    except RuntimeError as exc:
        result["check"] = "failed"
        print(f"step 6: check reported findings\n{exc}", flush=True)
        if not force:
            if render:
                # Every model call is already paid for by this point. Stopping
                # here without saying so plainly reads as a crash, and the next
                # thing anyone does is re-run the whole pipeline to find out.
                print(
                    "\nstep 6: NO VIDEO WAS RENDERED — the gate failed and "
                    "--force was not set.\n"
                    "        The project is built and every model call is spent; "
                    "re-render it for free with:\n"
                    f"          cd {project} && npx hyperframes render "
                    "--skill=faceless-explainer --quality high "
                    "--output renders/video.mp4\n",
                    flush=True,
                )
            return result

    hyperframes("snapshot", "--at", snapshot_times(project), cwd=project, timeout=1800)
    if not render:
        return result

    output = project / "renders" / "video.mp4"
    hyperframes(
        "render", "--skill=faceless-explainer", "--quality", "high",
        "--output", "renders/video.mp4", cwd=project, timeout=7200,
    )
    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError(f"render finished without a usable file: {output}")
    result["video"] = str(output)
    if (duration := rendered_duration(output)) is not None:
        result["duration_s"] = f"{duration:.2f}"
    return result


# ── the run ──────────────────────────────────────────────────────────────────


def build_video(
    topic: str,
    source_material: str,
    destination: str = "instagram-reels",
    length: int = 45,
    frame_count: int = 6,
    voice: str = "af_heart",
    preset: str = "biennale-yellow",
    use_brand: bool = True,
    research: bool = False,
    model_name: str = llm.DEFAULT_MODEL,
    frame_model_name: str | None = None,
    subscription: bool = False,
    max_tokens: int = 16000,
    output_dir: Path = ROOT / "output",
    render: bool = False,
    force: bool = False,
) -> dict:
    if destination not in RESOLUTIONS:
        raise ValueError(f"unsupported destination: {destination}")
    if not 3 <= frame_count <= 12:
        raise ValueError("frames must be between 3 and 12")
    if not research and not source_material.strip():
        raise ValueError(
            "source notes cannot be empty — pass --source with notes, or --research "
            "to have the model find its own facts."
        )

    check_tools()
    _, canvas = RESOLUTIONS[destination]
    project = next_project_dir(output_dir, topic)

    # The subscription backend bills a Claude Code plan instead of API credits.
    # Fine for development; the Agent SDK terms forbid it for a shipped product.
    backend = llm.SubscriptionModel if subscription else llm.Model
    planner = backend(model_name, max_tokens)
    frame_author = (
        planner
        if frame_model_name in (None, model_name)
        else backend(frame_model_name, max_tokens)
    )

    scaffold(project, topic, destination, length, preset, voice)
    planner.transcript = frame_author.transcript = project / ".sessions"

    if research:
        # Researched notes REPLACE the fallback file rather than joining it: the
        # example notes are about one specific topic, and handing the planner two
        # subjects is how you get a video about neither. Retrieved pages are not
        # fact-checked — the prompt tells the model to mark prices and limits
        # unverified, and a human still has to confirm them before publishing.
        source_material = planner.research("step2-research", topic)
        (project / "capture" / "extracted").mkdir(parents=True, exist_ok=True)
        (project / "RESEARCH.md").write_text(source_material, encoding="utf-8")

    synthetic_capture(project, topic, source_material, use_brand)
    design_system(project, preset, use_brand)

    plan = plan_story(
        planner, project, topic, source_material, canvas, length, frame_count, voice
    )
    has_audio = make_audio(project, voice)
    design_frames(planner, project, plan, canvas, length)
    failed = build_frames(frame_author, project, plan, canvas, has_audio)

    spend = planner.ledger.total_usd() + (
        frame_author.ledger.total_usd() if frame_author is not planner else 0.0
    )
    print(f"spend: {planner.ledger.summary()}", flush=True)
    if frame_author is not planner:
        print(f"spend: {frame_author.ledger.summary()}", flush=True)

    if failed and not force:
        raise RuntimeError(
            f"these frames were not authored: {', '.join(failed)}. Re-run, or "
            "pass --force to assemble and gate without them."
        )
    result = finalize(project, render, force)
    result["model_cost_usd"] = f"{spend:.4f}"
    if failed:
        result["unauthored_frames"] = ", ".join(failed)
    return result


DEFAULT_TOPIC = "Five cheap AI tools for small business"


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="Render a faceless explainer with the HyperFrames workflow."
    )
    parser.add_argument("--topic", default=DEFAULT_TOPIC)
    parser.add_argument(
        "--source", type=Path, default=DEFAULT_NOTES,
        help=f"Source notes: the factual boundary (default {DEFAULT_NOTES}).",
    )
    parser.add_argument("--destination", default="instagram-reels", choices=sorted(RESOLUTIONS))
    parser.add_argument("--length", type=int, default=45, help="Target seconds")
    parser.add_argument("--frames", type=int, default=6)
    parser.add_argument("--voice", default="af_heart", help="Kokoro voice id")
    parser.add_argument(
        "--preset", default="biennale-yellow",
        help="Frame preset build-frame.mjs adopts and brand-remixes.",
    )
    parser.add_argument(
        "--no-brand", action="store_true",
        help="Keep the preset's own look instead of brand/frame.md.",
    )
    parser.add_argument(
        "--model", default=os.environ.get("VIDEO_MODEL", llm.DEFAULT_MODEL),
        help="Story and visual design. Both answers are schema-constrained.",
    )
    parser.add_argument(
        "--frame-model", default=os.environ.get("FRAME_MODEL"),
        help="Frame HTML (defaults to --model). The one step no schema can guard, "
             "so this is the knob to turn if frames come back weak.",
    )
    parser.add_argument(
        "--research", action="store_true",
        help="Search the web for the topic's facts instead of reading --source. "
             "Costs about $0.01 per search on top of tokens.",
    )
    parser.add_argument(
        "--subscription", action="store_true",
        help="Bill a Claude Code subscription via `claude -p` instead of an API "
             "key. For development only — the Agent SDK terms do not permit "
             "subscription auth in a product you offer to others.",
    )
    parser.add_argument("--max-tokens", type=int, default=16000)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "output",
        help="Output root (fixed to ./output; projects are named <topic>-vN).",
    )
    parser.add_argument("--render", action="store_true", help="Render the MP4 after check passes.")
    parser.add_argument(
        "--force", action="store_true",
        help="Keep going past a failed frame or a failed gate.",
    )
    args = parser.parse_args()

    try:
        result = build_video(
            topic=args.topic,
            source_material=(
                args.source.read_text(encoding="utf-8")
                if args.source.is_file()
                else ""
            ),
            destination=args.destination,
            length=args.length,
            frame_count=args.frames,
            voice=args.voice,
            preset=args.preset,
            use_brand=not args.no_brand,
            research=args.research,
            subscription=args.subscription,
            model_name=args.model,
            frame_model_name=args.frame_model,
            max_tokens=args.max_tokens,
            output_dir=args.output,
            render=args.render,
            force=args.force,
        )
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Model calls, and what they cost.

Three shapes, one per kind of artifact this pipeline needs:

- `plan()`  — a JSON object matching a schema. The API constrains the response
  to the schema, so an unparseable or incomplete answer is not a case to handle.
- `author()` — free text, for the one artifact that *is* text (frame HTML).
- `authored_in_parallel()` — the same call fanned out across frames at once.

The role contract every frame call shares goes in `system` with a cache
breakpoint, so the first frame writes it and the rest read it at a tenth of the
price. That is also just the right shape: the contract is the model's standing
role, and the packet is the task.

Every call reports its own token spend, and `Ledger` totals the run in dollars.
For anything charging per video, the cost of a render is a number you need on
every run, not an estimate you do once.
"""

from __future__ import annotations

import concurrent.futures
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

import anthropic

# Cheap enough to render at volume, and strong enough at the two jobs that
# matter here: picking from a closed vocabulary, and filling a template's slots.
DEFAULT_MODEL = "claude-haiku-4-5"

# $ per million tokens, input / output. Cache reads bill at 0.1x input and cache
# writes at 1.25x, so the ledger prices those separately.
PRICES = {
    "claude-haiku-4-5": (1.00, 5.00),
    "claude-sonnet-5": (2.00, 10.00),  # introductory rate through 2026-08-31
    "claude-opus-5": (5.00, 25.00),
}

# `effort` is rejected on Haiku 4.5, and every 5-series model rejects a
# non-default `temperature`. Sending neither is correct on all of them.
EFFORT_MODELS = ("claude-sonnet-5", "claude-opus-5", "claude-fable-5")


@dataclass
class Ledger:
    """What the run spent, and where."""

    calls: list[dict] = field(default_factory=list)

    def record(self, label: str, model: str, usage: object, seconds: float) -> None:
        self.calls.append(
            {
                "label": label,
                "model": model,
                "input": usage.input_tokens,
                "output": usage.output_tokens,
                "cache_read": getattr(usage, "cache_read_input_tokens", 0) or 0,
                "cache_write": getattr(usage, "cache_creation_input_tokens", 0) or 0,
                "searches": getattr(
                    getattr(usage, "server_tool_use", None), "web_search_requests", 0
                ) or 0,
                "seconds": seconds,
            }
        )

    def total_usd(self) -> float:
        total = 0.0
        for call in self.calls:
            if "measured_usd" in call:
                # The subscription path reports what it actually spent.
                total += call["measured_usd"]
                continue
            price_in, price_out = PRICES.get(call["model"], (0.0, 0.0))
            total += (
                call["input"] * price_in
                + call["cache_read"] * price_in * 0.1
                + call["cache_write"] * price_in * 1.25
                + call["output"] * price_out
            ) / 1_000_000
            # Web search is metered per request, not per token: $10 / 1,000.
            total += call["searches"] * 0.01
        return total

    def summary(self) -> str:
        cached = sum(call["cache_read"] for call in self.calls)
        return (
            f"{len(self.calls)} model call(s), "
            f"{sum(c['input'] + c['cache_read'] + c['cache_write'] for c in self.calls):,} in / "
            f"{sum(c['output'] for c in self.calls):,} out, "
            f"{cached:,} read from cache, "
            f"{sum(c['searches'] for c in self.calls)} web search(es), "
            f"${self.total_usd():.4f}"
        )


class SubscriptionModel:
    """The same three calls, billed to a Claude Code subscription instead of API
    credits — by shelling out to `claude -p`, which is the documented way to drive
    the agent loop from outside Python.

    Use this to develop and test without an API key. **Do not ship it.** The Agent
    SDK docs are explicit: "Anthropic does not allow third party developers to
    offer claude.ai login or rate limits for their products, including agents
    built on the Claude Agent SDK. Use the API key authentication methods
    instead." That makes this a dev-mode backend, not a product one.

    Every invocation reloads the Claude Code harness, so this path is slower and
    less economical than one long-lived API client. The two planning calls also
    pass the CLI's native `--json-schema`; the local validator remains as a cheap
    defense against malformed output or an older Claude Code binary.
    """

    def __init__(
        self,
        name: str = DEFAULT_MODEL,
        max_tokens: int = 16000,
        transcript: Path | None = None,
    ) -> None:
        import shutil

        if not shutil.which("claude"):
            raise RuntimeError(
                "`claude` is not on PATH. Install Claude Code, or drop "
                "--subscription to use an API key instead."
            )
        self.name = name
        self.max_tokens = max_tokens
        self.transcript = transcript
        self.ledger = Ledger()

    def research(self, label: str, topic: str, max_searches: int = 6) -> str:
        """Web search comes from the harness's own WebSearch tool here."""
        return self._call(
            label,
            system=None,
            prompt=(
                f"Research this topic with web search and write source notes I can "
                f"script a video from: {topic}\n\n"
                "Search for current, specific facts. Then write markdown notes: a "
                "short section per finding, each ending with the URL you took it "
                "from. Real figures only where a source states them; mark prices, "
                f"plan names, and limits as unverified. Use no more than {max_searches} "
                "searches. No preamble."
            ),
            tools=["WebSearch", "WebFetch"],
        )

    def plan(self, label: str, prompt: str, schema: dict) -> dict:
        """Ask for JSON and validate it.

        The CLI enforces the schema when supported, and the local validator keeps
        retry behavior stable across Claude Code versions. One retry, then give
        up — a third attempt at the same prompt rarely differs.
        """
        import json

        ask = (
            f"{prompt}\n\n---\n\nAnswer with one JSON object and nothing else — no "
            "markdown fence, no commentary. It must validate against this JSON "
            f"schema:\n\n{json.dumps(schema, indent=2)}"
        )
        note = ""
        for attempt in range(2):
            raw = self._call(
                f"{label}-retry" if attempt else label,
                system=None,
                prompt=ask + note,
                json_schema=schema,
            )
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            try:
                if match is None:
                    raise ValueError("no JSON object in the answer")
                answer = json.loads(match.group(0))
                _check_schema(answer, schema)
                return answer
            except ValueError as exc:
                note = f"\n\nYour last answer was rejected: {exc}. Fix it."
                print(f"model: {label} — {exc}; retrying", flush=True)
        raise RuntimeError(f"{label}: no answer matching the schema after 2 tries.")

    def author(self, label: str, role: str, prompt: str) -> str:
        return self._call(label, system=role, prompt=prompt)

    def _call(
        self,
        label: str,
        system: str | None,
        prompt: str,
        tools: list[str] | None = None,
        json_schema: dict | None = None,
    ) -> str:
        import json
        import subprocess

        command = [
            "claude", "-p", prompt,
            "--model", self.name,
            "--output-format", "json",
            "--no-session-persistence",
            "--permission-mode", "dontAsk",
        ]
        if system is not None:
            command += ["--append-system-prompt", system]
        if json_schema is not None:
            command += ["--json-schema", json.dumps(json_schema, separators=(",", ":"))]
        # Tools are opt-in per call: the JSON and HTML steps need none, and a
        # toolless call cannot read a file it was never asked to read.
        command += ["--allowed-tools", *tools] if tools else ["--tools", ""]

        print(f"model: {label} → {self.name} (subscription)", flush=True)
        started = time.time()
        done = subprocess.run(
            command, capture_output=True, text=True, timeout=1800, stdin=subprocess.DEVNULL
        )
        if done.returncode != 0:
            raise RuntimeError(f"{label}: claude exited {done.returncode}: {done.stderr[-500:]}")

        try:
            payload = json.loads(done.stdout[done.stdout.index("{"):])
        except (ValueError, IndexError) as exc:
            raise RuntimeError(f"{label}: unreadable claude output ({exc})") from exc
        if payload.get("is_error"):
            raise RuntimeError(f"{label}: {payload.get('result', 'claude reported an error')}")

        usage = payload.get("usage", {})
        elapsed = time.time() - started
        # The harness reports what it actually spent, so the ledger records the
        # measured figure rather than re-deriving it from token counts.
        self.ledger.calls.append(
            {
                "label": label,
                "model": self.name,
                "input": usage.get("input_tokens", 0),
                "output": usage.get("output_tokens", 0),
                "cache_read": usage.get("cache_read_input_tokens", 0),
                "cache_write": usage.get("cache_creation_input_tokens", 0),
                "searches": (usage.get("server_tool_use") or {}).get(
                    "web_search_requests", 0
                ),
                "seconds": elapsed,
                "measured_usd": payload.get("total_cost_usd", 0.0),
            }
        )
        answer = (payload.get("result") or "").strip()
        if not answer:
            raise RuntimeError(f"{label}: empty answer.")
        print(
            f"model: {label} done — {usage.get('output_tokens', 0)} out in "
            f"{elapsed:.0f}s, ${payload.get('total_cost_usd', 0):.4f}",
            flush=True,
        )
        if self.transcript is not None:
            self.transcript.mkdir(parents=True, exist_ok=True)
            (self.transcript / f"{label}.md").write_text(
                f"# {label}\n\n## Prompt\n\n{prompt}\n\n## Answer\n\n{answer}\n",
                encoding="utf-8",
            )
        return answer


def _check_schema(value: object, schema: dict, path: str = "root") -> None:
    """Enough of JSON Schema to catch what the model actually gets wrong.

    Only used on the subscription path, where the API is not enforcing the schema
    for us: required keys, types, enum membership, and array bounds. Not a
    conforming validator, and does not need to be — anything subtler than this
    fails loudly in the Node script that reads the field.
    """
    kind = schema.get("type")
    if kind == "object":
        if not isinstance(value, dict):
            raise ValueError(f"{path}: expected an object")
        for key in schema.get("required", []):
            if key not in value:
                raise ValueError(f"{path}: missing required key {key!r}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            unknown = sorted(set(value) - set(properties))
            if unknown:
                raise ValueError(f"{path}: unexpected key(s) {', '.join(unknown)}")
        for key, sub in properties.items():
            if key in value:
                _check_schema(value[key], sub, f"{path}.{key}")
    elif kind == "array":
        if not isinstance(value, list):
            raise ValueError(f"{path}: expected an array")
        low, high = schema.get("minItems"), schema.get("maxItems")
        if low is not None and len(value) < low:
            raise ValueError(f"{path}: needs at least {low} items, got {len(value)}")
        if high is not None and len(value) > high:
            raise ValueError(f"{path}: allows at most {high} items, got {len(value)}")
        for index, item in enumerate(value):
            _check_schema(item, schema.get("items", {}), f"{path}[{index}]")
    elif kind == "string":
        if not isinstance(value, str):
            raise ValueError(f"{path}: expected a string")
        if len(value) < schema.get("minLength", 0):
            raise ValueError(f"{path}: needs at least {schema['minLength']} characters")
        if (allowed := schema.get("enum")) and value not in allowed:
            raise ValueError(f"{path}: {value!r} is not one of the allowed values")
        if (pattern := schema.get("pattern")) and not re.search(pattern, value):
            raise ValueError(f"{path}: does not match {pattern!r}")
    elif kind in ("number", "integer"):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{path}: expected a {kind}")
        if kind == "integer" and not isinstance(value, int):
            raise ValueError(f"{path}: expected an integer")
        if "minimum" in schema and value < schema["minimum"]:
            raise ValueError(f"{path}: must be at least {schema['minimum']}")


class Model:
    """One model, one ledger. Safe to share across threads."""

    def __init__(
        self,
        name: str = DEFAULT_MODEL,
        max_tokens: int = 16000,
        transcript: Path | None = None,
    ) -> None:
        self.name = name
        self.max_tokens = max_tokens
        self.transcript = transcript
        self.ledger = Ledger()
        try:
            self.client = anthropic.Anthropic()
        except anthropic.AnthropicError as exc:  # no credential resolved
            raise RuntimeError(
                "No Anthropic credential found. Export ANTHROPIC_API_KEY, or put "
                "it in .env, then retry."
            ) from exc

    def research(self, label: str, topic: str, max_searches: int = 6) -> str:
        """Search the web and return sourced notes for a topic.

        Web search is a server-side tool: it is declared, and Anthropic runs the
        queries and returns the results as content blocks in the same response —
        there is no client-side search loop and no second API key. Haiku 4.5 takes
        the basic tool version; the dynamic-filtering variant is 5-series only.

        The one thing that does need handling is `pause_turn`: the server's own
        tool loop stops after ten iterations and asks to be resumed. Re-sending the
        conversation continues it — with no extra "keep going" user message, which
        the server neither needs nor expects.
        """
        tool = {
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": max_searches,
        }
        messages: list[dict] = [
            {
                "role": "user",
                "content": (
                    f"Research this topic and write source notes I can script a "
                    f"video from: {topic}\n\n"
                    "Search for current, specific facts. Then write markdown notes: "
                    "a short section per finding, each ending with the URL you took "
                    "it from. Include real figures only where a source states them, "
                    "and mark anything time-sensitive (prices, plan names, limits) as "
                    "unverified. No preamble — start with the first heading."
                ),
            }
        ]

        print(f"model: {label} → {self.name} (web search)", flush=True)
        started = time.time()
        searches = 0
        for _ in range(4):  # resume at most three times past a pause
            try:
                response = self.client.messages.create(
                    model=self.name,
                    max_tokens=self.max_tokens,
                    tools=[tool],
                    messages=messages,
                )
            except anthropic.APIError as exc:
                raise RuntimeError(f"{label}: {type(exc).__name__}: {exc}") from exc

            self.ledger.record(label, self.name, response.usage, time.time() - started)
            searches += sum(
                1 for block in response.content if block.type == "server_tool_use"
            )
            if response.stop_reason != "pause_turn":
                break
            messages.append({"role": "assistant", "content": response.content})
        else:
            raise RuntimeError(f"{label}: still paused after three resumes.")

        notes = "".join(
            block.text for block in response.content if block.type == "text"
        ).strip()
        if not notes:
            raise RuntimeError(
                f"{label}: the search returned nothing usable for {topic!r}."
            )
        print(
            f"model: {label} done — {searches} search(es), {len(notes.split())} "
            f"words of notes in {time.time() - started:.0f}s",
            flush=True,
        )
        if self.transcript is not None:
            self.transcript.mkdir(parents=True, exist_ok=True)
            (self.transcript / f"{label}.md").write_text(notes, encoding="utf-8")
        return notes

    def plan(self, label: str, prompt: str, schema: dict) -> dict:
        """Answer as an object matching `schema`.

        The schema is enforced by the API, so the first text block is valid JSON
        against it — there is no parse-and-repair step in this pipeline.
        """
        import json

        text = self._call(
            label,
            system=None,
            prompt=prompt,
            output_config={"format": {"type": "json_schema", "schema": schema}},
        )
        return json.loads(text)

    def author(self, label: str, role: str, prompt: str) -> str:
        """Answer as free text, with `role` as a cached system prompt."""
        return self._call(label, system=role, prompt=prompt)

    def authored_in_parallel(
        self, jobs: list[tuple[str, str, str]], workers: int = 6
    ) -> dict[str, str | Exception]:
        """Run several `author` calls at once, keyed by label.

        The workflow's own instruction for building frames is to dispatch one
        worker per frame, in parallel where possible. A single local GPU cannot;
        the API can, which turns the longest step of the run into its shortest.
        An exception is returned in place of a result so one bad frame does not
        discard the other five.

        A cache entry only becomes readable once the response that writes it has
        started coming back, so firing all N at once means every one of them pays
        full price for the shared prefix and none reads it. The first job goes
        alone to warm the cache; the rest then fan out and read it. That costs one
        frame of extra latency and takes ~17% off the step's bill.
        """
        results: dict[str, str | Exception] = {}

        def collect(label: str, future: concurrent.futures.Future) -> None:
            try:
                results[label] = future.result()
            except Exception as exc:  # reported per frame by the caller
                results[label] = exc

        first, rest = jobs[0], jobs[1:]
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            warm = pool.submit(self.author, *first)
            collect(first[0], warm)  # blocks: the prefix has to land first
            futures = {
                pool.submit(self.author, label, role, prompt): label
                for label, role, prompt in rest
            }
            for future in concurrent.futures.as_completed(futures):
                collect(futures[future], future)
        return results

    def _call(
        self,
        label: str,
        system: str | None,
        prompt: str,
        output_config: dict | None = None,
    ) -> str:
        request: dict = {
            "model": self.name,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system is not None:
            # The cache breakpoint goes on the shared contract. Anything that
            # differs per call has to stay in the user turn or the prefix
            # changes and nothing is ever read back.
            request["system"] = [
                {
                    "type": "text",
                    "text": system,
                    "cache_control": {"type": "ephemeral"},
                }
            ]
        if output_config is not None:
            request["output_config"] = output_config
        if self.name in EFFORT_MODELS:
            request["output_config"] = {
                **request.get("output_config", {}),
                "effort": "medium",
            }

        print(f"model: {label} → {self.name}", flush=True)
        started = time.time()
        try:
            response = self.client.messages.create(**request)
        except anthropic.APIError as exc:
            raise RuntimeError(f"{label}: {type(exc).__name__}: {exc}") from exc
        elapsed = time.time() - started

        self.ledger.record(label, self.name, response.usage, elapsed)

        if response.stop_reason == "refusal":
            raise RuntimeError(
                f"{label}: the model declined this request "
                f"({getattr(response.stop_details, 'category', 'no category')})."
            )
        if response.stop_reason == "max_tokens":
            raise RuntimeError(
                f"{label}: hit the {self.max_tokens}-token output cap, so the "
                "answer is truncated. Raise --max-tokens."
            )

        answer = "".join(
            block.text for block in response.content if block.type == "text"
        ).strip()
        if not answer:
            raise RuntimeError(f"{label}: empty answer.")

        cached = getattr(response.usage, "cache_read_input_tokens", 0) or 0
        print(
            f"model: {label} done — {response.usage.output_tokens} out in "
            f"{elapsed:.0f}s" + (f", {cached:,} cached" if cached else ""),
            flush=True,
        )
        if self.transcript is not None:
            self.transcript.mkdir(parents=True, exist_ok=True)
            (self.transcript / f"{label}.md").write_text(
                f"# {label}\n\n## Prompt\n\n{prompt}\n\n## Answer\n\n{answer}\n",
                encoding="utf-8",
            )
        return answer


# Both backends author frames identically once `author` exists, so the fan-out is
# defined once and attached to the subscription path rather than duplicated.
SubscriptionModel.authored_in_parallel = Model.authored_in_parallel

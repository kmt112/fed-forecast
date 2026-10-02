"""LLM backends behind one interface, so the runtime is a one-line swap.

  ClaudeCodeBackend  shells out to `claude -p` (the Claude Code CLI, subscription auth). Tools are disabled,
                     so the model can read nothing but the prompt: the snapshot-only rule is enforced by the
                     runtime, not by politeness. Output is constrained with --json-schema.
  ReplayBackend      serves recorded completions keyed by a hash of (system, prompt, schema); records new ones
                     from an inner backend. Deterministic tests and zero-cost reruns.
  FakeBackend        canned answers for unit tests.
  (AnthropicAPIBackend is the planned drop-in once an API key is in use: same interface, temperature control.)
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


@dataclass
class Completion:
    output: dict
    backend: str
    model: str = ""
    duration_s: float = 0.0
    prompt_hash: str = ""
    raw: str = ""
    meta: dict = field(default_factory=dict)


def prompt_hash(system: str, prompt: str, schema: dict) -> str:
    payload = json.dumps({"system": system, "prompt": prompt, "schema": schema}, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


class LLMBackend(Protocol):
    name: str

    def complete(self, system: str, prompt: str, schema: dict) -> Completion: ...


_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.S)


def parse_json_text(text: str) -> dict:
    text = _FENCE.sub("", text.strip())
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < 0:
        raise ValueError("no JSON object in model output")
    return json.loads(text[start:end + 1])


class ClaudeCodeBackend:
    name = "claude-code"

    def __init__(self, model: str | None = None, timeout_s: int = 600):
        self.model = model
        self.timeout_s = timeout_s

    def complete(self, system: str, prompt: str, schema: dict) -> Completion:
        cmd = ["claude", "-p", "--output-format", "json", "--json-schema", json.dumps(schema),
               "--tools", "", "--no-session-persistence", "--system-prompt", system]
        if self.model:
            cmd += ["--model", self.model]
        t0 = time.time()
        # the prompt goes through stdin: it can be far longer than a Windows command line allows
        proc = subprocess.run(cmd, input=prompt, capture_output=True, text=True, encoding="utf-8",
                              timeout=self.timeout_s, shell=True)
        if proc.returncode != 0 and not proc.stdout.strip():
            raise RuntimeError(f"claude -p failed ({proc.returncode}): {proc.stderr.strip()[:500]}")
        env = json.loads(proc.stdout)
        if env.get("is_error"):
            raise RuntimeError("claude -p error: " + str(env.get("result"))[:500])
        output = env.get("structured_output") or parse_json_text(env.get("result", ""))
        model = next(iter(env.get("modelUsage") or {}), self.model or "")
        return Completion(output=output, backend=self.name, model=model, duration_s=round(time.time() - t0, 1),
                          prompt_hash=prompt_hash(system, prompt, schema), raw=env.get("result", ""),
                          meta={"session_id": env.get("session_id"), "cost_usd": env.get("total_cost_usd"),
                                "num_turns": env.get("num_turns"), "usage": env.get("usage")})


class ReplayBackend:
    name = "replay"

    def __init__(self, folder: Path, inner: LLMBackend | None = None):
        self.folder = folder
        self.inner = inner

    def complete(self, system: str, prompt: str, schema: dict) -> Completion:
        key = prompt_hash(system, prompt, schema)
        path = self.folder / f"{key}.json"
        if path.exists():
            rec = json.loads(path.read_text(encoding="utf-8"))
            return Completion(output=rec["output"], backend=f"replay:{rec['backend']}", model=rec.get("model", ""),
                              duration_s=0.0, prompt_hash=key, raw=rec.get("raw", ""), meta=rec.get("meta", {}))
        if self.inner is None:
            raise LookupError(f"no recorded completion for {key} and no inner backend to call")
        c = self.inner.complete(system, prompt, schema)
        self.folder.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"output": c.output, "backend": c.backend, "model": c.model, "raw": c.raw,
                                    "meta": c.meta, "system": system, "prompt": prompt, "schema": schema},
                                   indent=1, ensure_ascii=False), encoding="utf-8")
        return c


class FakeBackend:
    name = "fake"

    def __init__(self, answers: list[dict] | dict):
        self.answers = answers if isinstance(answers, list) else [answers]
        self.calls: list[tuple[str, str, dict]] = []

    def complete(self, system: str, prompt: str, schema: dict) -> Completion:
        self.calls.append((system, prompt, schema))
        output = self.answers[min(len(self.calls) - 1, len(self.answers) - 1)]
        return Completion(output=json.loads(json.dumps(output)), backend=self.name, model="fake",
                          prompt_hash=prompt_hash(system, prompt, schema))

"""Anthropic API backend: the same LLMBackend interface as the Claude Code CLI backend, for environments
where the CLI is not signed in (a cloud session, a laptop, CI). Needs `pip install anthropic` and
ANTHROPIC_API_KEY in the environment. Structured output is enforced by the API's JSON-schema format,
so the analyst schema is honoured the same way the CLI's --json-schema honours it.

`make_backend()` picks the runtime: FEDCAST_LLM_BACKEND=api|claude-code, otherwise the API when a key is
set, otherwise the CLI.
"""

from __future__ import annotations

import json
import os
import shutil
import time

from fedcast.llm.backend import ClaudeCodeBackend, Completion, LLMBackend, prompt_hash

DEFAULT_MODEL = "claude-opus-5-5"


def _strict(schema: dict) -> dict:
    """The API's structured-output format wants every object to forbid unknown keys."""
    if isinstance(schema, dict):
        out = {k: _strict(v) for k, v in schema.items()}
        if out.get("type") == "object" and "properties" in out:
            out.setdefault("additionalProperties", False)
        return out
    if isinstance(schema, list):
        return [_strict(x) for x in schema]
    return schema


class AnthropicAPIBackend:
    name = "anthropic-api"

    def __init__(self, model: str = DEFAULT_MODEL, effort: str = "medium", client=None):
        if client is None:
            import anthropic  # imported here so the CLI backend works without the package installed

            client = anthropic.Anthropic()
        self.client = client
        self.model = model
        self.effort = effort

    def complete(self, system: str, prompt: str, schema: dict, run: int = 0) -> Completion:
        t0 = time.time()
        # Server-side refusal fallback is on by default (routes a safety decline to another model inside the call).
        response = self.client.beta.messages.create(
            model=self.model,
            max_tokens=16000,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            output_config={"format": {"type": "json_schema", "schema": _strict(schema)}, "effort": self.effort},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
        if response.stop_reason == "refusal":
            details = getattr(response, "stop_details", None)
            raise RuntimeError(f"model declined the request: {getattr(details, 'category', None)}")
        if response.stop_reason == "max_tokens":
            raise RuntimeError("model output was cut off at max_tokens")
        text = next(b.text for b in response.content if b.type == "text")
        usage = response.usage
        return Completion(output=json.loads(text), backend=self.name, model=response.model,
                          duration_s=round(time.time() - t0, 1), prompt_hash=prompt_hash(system, prompt, schema, run),
                          raw=text, meta={"request_id": getattr(response, "_request_id", None),
                                          "usage": {"input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens},
                                          "stop_reason": response.stop_reason})


def make_backend(model: str | None = None) -> LLMBackend:
    choice = os.environ.get("FEDCAST_LLM_BACKEND", "").lower()
    if choice == "api" or (not choice and os.environ.get("ANTHROPIC_API_KEY")):
        return AnthropicAPIBackend(model=model or DEFAULT_MODEL)
    if choice == "claude-code" or shutil.which("claude"):
        return ClaudeCodeBackend(model=model)
    if os.environ.get("ANTHROPIC_API_KEY"):
        return AnthropicAPIBackend(model=model or DEFAULT_MODEL)
    raise RuntimeError("no LLM runtime: sign in the claude CLI, or set ANTHROPIC_API_KEY (and pip install anthropic)")

import json
from types import SimpleNamespace

import pytest

from fedcast.llm import api_backend
from fedcast.llm.analyst import SCHEMA


class FakeMessages:
    def __init__(self, text, stop_reason="end_turn"):
        self.text, self.stop_reason, self.calls = text, stop_reason, []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(stop_reason=self.stop_reason, model="claude-opus-5-5",
                               content=[SimpleNamespace(type="text", text=self.text)],
                               usage=SimpleNamespace(input_tokens=10, output_tokens=5), _request_id="req_1")


def fake_client(text, stop_reason="end_turn"):
    m = FakeMessages(text, stop_reason)
    return SimpleNamespace(beta=SimpleNamespace(messages=m)), m


def test_api_backend_sends_schema_and_parses_json():
    client, m = fake_client(json.dumps({"claims": [], "watchouts": [], "tilt_bp": 2, "confidence": "low", "summary": "x"}))
    b = api_backend.AnthropicAPIBackend(client=client)
    c = b.complete("sys", "prompt", SCHEMA, run=3)
    assert c.output["tilt_bp"] == 2 and c.backend == "anthropic-api" and c.model == "claude-opus-5-5"
    sent = m.calls[0]
    assert sent["model"] == "claude-opus-5-5" and sent["system"] == "sys"
    assert sent["output_config"]["format"]["type"] == "json_schema"
    assert sent["output_config"]["format"]["schema"]["additionalProperties"] is False
    assert sent["fallbacks"] == "default"
    assert c.prompt_hash == api_backend.prompt_hash("sys", "prompt", SCHEMA, 3)


def test_api_backend_raises_on_refusal_and_truncation():
    client, _ = fake_client("{}", stop_reason="refusal")
    with pytest.raises(RuntimeError):
        api_backend.AnthropicAPIBackend(client=client).complete("s", "p", SCHEMA)
    client, _ = fake_client("{", stop_reason="max_tokens")
    with pytest.raises(RuntimeError):
        api_backend.AnthropicAPIBackend(client=client).complete("s", "p", SCHEMA)


def test_strict_adds_additional_properties_everywhere():
    s = api_backend._strict(SCHEMA)
    assert s["additionalProperties"] is False
    assert s["properties"]["claims"]["items"]["additionalProperties"] is False


def test_make_backend_honours_env(monkeypatch):
    monkeypatch.setenv("FEDCAST_LLM_BACKEND", "claude-code")
    assert api_backend.make_backend().name == "claude-code"
    monkeypatch.setenv("FEDCAST_LLM_BACKEND", "")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(api_backend.shutil, "which", lambda name: None)
    with pytest.raises(RuntimeError):
        api_backend.make_backend()

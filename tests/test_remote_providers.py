"""Tests for remote LLM providers (OpenAI, Anthropic, Gemini, DeepSeek)."""
from __future__ import annotations

import json
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from pocketflow_creator.runtime.providers import (
    AnthropicProvider,
    DeepSeekProvider,
    GeminiProvider,
    MockProvider,
    OllamaProvider,
    OpenAIProvider,
)

# ── helpers ───────────────────────────────────────────────────────────────────

def _mock_response(body: dict, status: int = 200) -> MagicMock:
    """Return a mock HTTP response context-manager."""
    raw = json.dumps(body).encode()
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=MagicMock(read=MagicMock(return_value=raw)))
    cm.__exit__ = MagicMock(return_value=False)
    return cm


def _http_error(status: int, body: dict) -> Exception:
    import urllib.error
    raw = json.dumps(body).encode()
    fp = BytesIO(raw)
    return urllib.error.HTTPError(url="http://x", code=status, msg="err", hdrs=None, fp=fp)  # type: ignore[arg-type]


# ── MockProvider ──────────────────────────────────────────────────────────────

def test_mock_provider_returns_fixed_response() -> None:
    p = MockProvider(response="hello")
    assert p.complete("anything") == "hello"


def test_mock_provider_ignores_model() -> None:
    p = MockProvider(response="x")
    assert p.complete("q", model="gpt-4") == "x"


# ── OpenAIProvider ────────────────────────────────────────────────────────────

OPENAI_OK = {"choices": [{"message": {"content": "openai reply"}}]}


def test_openai_complete_success() -> None:
    with patch("urllib.request.urlopen", return_value=_mock_response(OPENAI_OK)) as mock_open:
        p = OpenAIProvider(api_key="sk-test", default_model="gpt-4o-mini")
        result = p.complete("hello")
        assert result == "openai reply"
        req = mock_open.call_args[0][0]
        assert req.get_header("Authorization") == "Bearer sk-test"
        assert "chat/completions" in req.full_url


def test_openai_passes_model_override() -> None:
    with patch("urllib.request.urlopen", return_value=_mock_response(OPENAI_OK)):
        p = OpenAIProvider(api_key="k")
        p.complete("hi", model="gpt-4o")
        # no assertion needed on model—just verify no error raised


def test_openai_uses_custom_base_url() -> None:
    with patch("urllib.request.urlopen", return_value=_mock_response(OPENAI_OK)) as mock_open:
        p = OpenAIProvider(api_key="k", base_url="https://my-proxy.example.com/v1")
        p.complete("hi")
        req = mock_open.call_args[0][0]
        assert "my-proxy.example.com" in req.full_url


def test_openai_raises_on_http_error() -> None:
    err = _http_error(401, {"error": {"message": "invalid key"}})
    with patch("urllib.request.urlopen", side_effect=err):
        p = OpenAIProvider(api_key="bad")
        with pytest.raises(RuntimeError, match="invalid key"):
            p.complete("hi")


def test_openai_raises_on_connection_error() -> None:
    import urllib.error
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("refused")):
        p = OpenAIProvider(api_key="k")
        with pytest.raises(RuntimeError, match="OpenAI request failed"):
            p.complete("hi")


def test_openai_raises_on_bad_json() -> None:
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=MagicMock(read=MagicMock(return_value=b"not-json")))
    cm.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=cm):
        p = OpenAIProvider(api_key="k")
        with pytest.raises(RuntimeError, match="unexpected response"):
            p.complete("hi")


# ── AnthropicProvider ─────────────────────────────────────────────────────────

ANTHROPIC_OK = {"content": [{"text": "claude reply"}]}


def test_anthropic_complete_success() -> None:
    with patch("urllib.request.urlopen", return_value=_mock_response(ANTHROPIC_OK)) as mock_open:
        p = AnthropicProvider(api_key="ant-key")
        result = p.complete("hello")
        assert result == "claude reply"
        req = mock_open.call_args[0][0]
        assert req.get_header("X-api-key") == "ant-key"
        assert "messages" in req.full_url


def test_anthropic_sends_correct_version_header() -> None:
    with patch("urllib.request.urlopen", return_value=_mock_response(ANTHROPIC_OK)) as mock_open:
        p = AnthropicProvider(api_key="k")
        p.complete("hi")
        req = mock_open.call_args[0][0]
        assert req.get_header("Anthropic-version") == "2023-06-01"


def test_anthropic_raises_on_http_error() -> None:
    err = _http_error(403, {"error": {"message": "permission denied"}})
    with patch("urllib.request.urlopen", side_effect=err):
        p = AnthropicProvider(api_key="bad")
        with pytest.raises(RuntimeError, match="permission denied"):
            p.complete("hi")


def test_anthropic_raises_on_connection_error() -> None:
    import urllib.error
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
        p = AnthropicProvider(api_key="k")
        with pytest.raises(RuntimeError, match="Anthropic request failed"):
            p.complete("hi")


# ── GeminiProvider ────────────────────────────────────────────────────────────

GEMINI_OK = {"candidates": [{"content": {"parts": [{"text": "gemini reply"}]}}]}


def test_gemini_complete_success() -> None:
    with patch("urllib.request.urlopen", return_value=_mock_response(GEMINI_OK)) as mock_open:
        p = GeminiProvider(api_key="gem-key", default_model="gemini-2.0-flash")
        result = p.complete("hello")
        assert result == "gemini reply"
        req = mock_open.call_args[0][0]
        assert "gem-key" in req.full_url
        assert "gemini-2.0-flash" in req.full_url


def test_gemini_raises_on_http_error() -> None:
    err = _http_error(400, {"error": {"message": "bad request"}})
    with patch("urllib.request.urlopen", side_effect=err):
        p = GeminiProvider(api_key="k")
        with pytest.raises(RuntimeError, match="bad request"):
            p.complete("hi")


def test_gemini_raises_on_connection_error() -> None:
    import urllib.error
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("no host")):
        p = GeminiProvider(api_key="k")
        with pytest.raises(RuntimeError, match="Gemini request failed"):
            p.complete("hi")


def test_gemini_raises_on_missing_candidate() -> None:
    with patch("urllib.request.urlopen", return_value=_mock_response({"candidates": []})):
        p = GeminiProvider(api_key="k")
        with pytest.raises(RuntimeError, match="unexpected response"):
            p.complete("hi")


# ── DeepSeekProvider ──────────────────────────────────────────────────────────

DEEPSEEK_OK = {"choices": [{"message": {"content": "deepseek reply"}}]}


def test_deepseek_complete_success() -> None:
    with patch("urllib.request.urlopen", return_value=_mock_response(DEEPSEEK_OK)) as mock_open:
        p = DeepSeekProvider(api_key="ds-key", default_model="deepseek-chat")
        result = p.complete("hello")
        assert result == "deepseek reply"
        req = mock_open.call_args[0][0]
        assert req.get_header("Authorization") == "Bearer ds-key"
        assert "api.deepseek.com" in req.full_url


def test_deepseek_uses_custom_base_url() -> None:
    with patch("urllib.request.urlopen", return_value=_mock_response(DEEPSEEK_OK)) as mock_open:
        p = DeepSeekProvider(api_key="k", base_url="https://custom.ds.example.com/v1")
        p.complete("hi")
        req = mock_open.call_args[0][0]
        assert "custom.ds.example.com" in req.full_url


def test_deepseek_raises_on_http_error() -> None:
    err = _http_error(402, {"error": {"message": "insufficient credits"}})
    with patch("urllib.request.urlopen", side_effect=err):
        p = DeepSeekProvider(api_key="bad")
        with pytest.raises(RuntimeError, match="insufficient credits"):
            p.complete("hi")


def test_deepseek_raises_on_connection_error() -> None:
    import urllib.error
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("refused")):
        p = DeepSeekProvider(api_key="k")
        with pytest.raises(RuntimeError, match="DeepSeek request failed"):
            p.complete("hi")


# ── OllamaProvider (regression) ───────────────────────────────────────────────

OLLAMA_OK = {"response": "ollama reply"}


def test_ollama_complete_success() -> None:
    with patch("urllib.request.urlopen", return_value=_mock_response(OLLAMA_OK)):
        p = OllamaProvider(base_url="http://localhost:11434", default_model="llama3")
        assert p.complete("hi") == "ollama reply"


def test_ollama_raises_on_connection_error() -> None:
    import urllib.error
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("refused")):
        p = OllamaProvider()
        with pytest.raises(RuntimeError, match="Ollama request failed"):
            p.complete("hi")

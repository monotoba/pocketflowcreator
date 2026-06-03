from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pocketflow_creator.model.provider_profile import ProviderProfile


class LLMProvider(Protocol):
    def complete(self, prompt: str, *, model: str | None = None) -> str:
        """Send *prompt* to the LLM and return the text response."""
        ...


@dataclass(slots=True)
class MockProvider:
    response: str = "mock response"

    def complete(self, prompt: str, *, model: str | None = None) -> str:
        return self.response


@dataclass(slots=True)
class OllamaProvider:
    """Ollama native API — /api/generate endpoint."""

    base_url: str = "http://localhost:11434"
    default_model: str = "qwen2.5-coder:14b"
    timeout: int = 120

    def complete(self, prompt: str, *, model: str | None = None) -> str:
        import sys
        url = f"{self.base_url.rstrip('/')}/api/generate"
        model_name = model or self.default_model
        payload = json.dumps(
            {"model": model_name, "prompt": prompt, "stream": False}
        ).encode()
        req = urllib.request.Request(
            url, data=payload, headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read())
                return str(body.get("response", ""))
        except urllib.error.HTTPError as exc:
            print(f"[OllamaProvider] HTTPError: {exc.code} {exc.reason}", file=sys.stderr)
            # Try to extract error details from response
            detail = f"{exc.code} {exc.reason}"  # fallback to HTTP status
            try:
                resp_body = exc.read().decode("utf-8", errors="replace")
                print(f"[OllamaProvider] Response body: {resp_body[:500]}", file=sys.stderr)
                if resp_body:
                    try:
                        error_data = json.loads(resp_body)
                        detail = error_data.get("error", resp_body[:200])
                    except json.JSONDecodeError:
                        detail = resp_body[:200]
            except Exception as e:
                print(f"[OllamaProvider] Error reading response: {e}", file=sys.stderr)
                pass  # keep the HTTP status fallback
            # Ensure we have something to report
            detail = detail or f"{exc.code} {exc.reason}"
            # Provide context about the model if it's likely the issue
            if "not found" in detail.lower() or "unknown" in detail.lower():
                detail = f"{detail}. Make sure '{model_name}' is installed in Ollama (ollama pull {model_name})"
            raise RuntimeError(f"Ollama request failed: {detail}") from exc
        except urllib.error.URLError as exc:
            reason = str(exc.reason) if exc.reason else str(exc)
            print(f"[OllamaProvider] URLError: {reason}", file=sys.stderr)
            raise RuntimeError(f"Ollama request failed: {reason}") from exc
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            print(f"[OllamaProvider] Response parsing error: {exc}", file=sys.stderr)
            raise RuntimeError(f"Ollama returned unexpected response: {exc}") from exc


@dataclass(slots=True)
class OpenAIProvider:
    """OpenAI chat completions — also works with any OpenAI-compatible endpoint."""

    api_key: str
    base_url: str = "https://api.openai.com/v1"
    default_model: str = "gpt-4o-mini"
    timeout: int = 120

    def complete(self, prompt: str, *, model: str | None = None) -> str:
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        payload = json.dumps(
            {
                "model": model or self.default_model,
                "messages": [{"role": "user", "content": prompt}],
            }
        ).encode()
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:  # omit Authorization when key is empty (e.g. local Ollama)
            headers["Authorization"] = f"Bearer {self.api_key}"
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read())
                return str(body["choices"][0]["message"]["content"])
        except urllib.error.HTTPError as exc:
            try:
                detail = json.loads(exc.read()).get("error", {}).get("message", str(exc))
            except Exception:
                detail = str(exc)
            raise RuntimeError(f"OpenAI request failed: {detail}") from exc
        except urllib.error.URLError as exc:
            reason = str(exc.reason) if exc.reason else str(exc)
            raise RuntimeError(f"OpenAI request failed: {reason}") from exc
        except (json.JSONDecodeError, KeyError, IndexError, ValueError) as exc:
            raise RuntimeError(f"OpenAI returned unexpected response: {exc}") from exc


@dataclass(slots=True)
class AnthropicProvider:
    """Anthropic Messages API."""

    api_key: str
    default_model: str = "claude-haiku-4-5"
    timeout: int = 120

    def complete(self, prompt: str, *, model: str | None = None) -> str:
        url = "https://api.anthropic.com/v1/messages"
        payload = json.dumps(
            {
                "model": model or self.default_model,
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": prompt}],
            }
        ).encode()
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read())
                return str(body["content"][0]["text"])
        except urllib.error.HTTPError as exc:
            try:
                detail = json.loads(exc.read()).get("error", {}).get("message", str(exc))
            except Exception:
                detail = str(exc)
            raise RuntimeError(f"Anthropic request failed: {detail}") from exc
        except urllib.error.URLError as exc:
            reason = str(exc.reason) if exc.reason else str(exc)
            raise RuntimeError(f"Anthropic request failed: {reason}") from exc
        except (json.JSONDecodeError, KeyError, IndexError) as exc:
            raise RuntimeError(f"Anthropic returned unexpected response: {exc}") from exc


@dataclass(slots=True)
class GeminiProvider:
    """Google Gemini generateContent API."""

    api_key: str
    default_model: str = "gemini-2.0-flash"
    timeout: int = 120

    def complete(self, prompt: str, *, model: str | None = None) -> str:
        mdl = model or self.default_model
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{mdl}"
            f":generateContent?key={self.api_key}"
        )
        payload = json.dumps(
            {"contents": [{"parts": [{"text": prompt}]}]}
        ).encode()
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read())
                return str(body["candidates"][0]["content"]["parts"][0]["text"])
        except urllib.error.HTTPError as exc:
            try:
                detail = json.loads(exc.read()).get("error", {}).get("message", str(exc))
            except Exception:
                detail = str(exc)
            raise RuntimeError(f"Gemini request failed: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Gemini request failed: {exc}") from exc
        except (json.JSONDecodeError, KeyError, IndexError) as exc:
            raise RuntimeError(f"Gemini returned unexpected response: {exc}") from exc


@dataclass(slots=True)
class DeepSeekProvider:
    """DeepSeek API (OpenAI-compatible)."""

    api_key: str
    base_url: str = "https://api.deepseek.com/v1"
    default_model: str = "deepseek-chat"
    timeout: int = 120

    def complete(self, prompt: str, *, model: str | None = None) -> str:
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        payload = json.dumps(
            {
                "model": model or self.default_model,
                "messages": [{"role": "user", "content": prompt}],
            }
        ).encode()
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read())
                return str(body["choices"][0]["message"]["content"])
        except urllib.error.HTTPError as exc:
            try:
                detail = json.loads(exc.read()).get("error", {}).get("message", str(exc))
            except Exception:
                detail = str(exc)
            raise RuntimeError(f"DeepSeek request failed: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"DeepSeek request failed: {exc}") from exc
        except (json.JSONDecodeError, KeyError, IndexError, ValueError) as exc:
            raise RuntimeError(f"DeepSeek returned unexpected response: {exc}") from exc


# ── profile factory ───────────────────────────────────────────────────────────

def build_provider_from_profile(
    profile: ProviderProfile,
    api_key: str = "",
) -> OpenAIProvider | AnthropicProvider | GeminiProvider | OllamaProvider:
    """Construct the right provider from a ProviderProfile.

    *api_key* overrides the profile's own api_key (used when the key is
    stored in QSettings rather than the project file).
    """
    key = api_key or profile.api_key
    if profile.type == "anthropic":
        return AnthropicProvider(
            api_key=key,
            default_model=profile.model,
            timeout=profile.timeout,
        )
    if profile.type == "gemini":
        return GeminiProvider(
            api_key=key,
            default_model=profile.model,
            timeout=profile.timeout,
        )
    if profile.type == "ollama":
        return OllamaProvider(
            base_url=profile.base_url or "http://localhost:11434",
            default_model=profile.model,
            timeout=profile.timeout,
        )
    if profile.type == "lm_studio":
        return OpenAIProvider(
            api_key=key,
            base_url=profile.base_url or "http://localhost:1234/v1",
            default_model=profile.model,
            timeout=profile.timeout,
        )
    # Default: openai_compat covers OpenAI, DeepSeek, Azure, Groq, etc.
    return OpenAIProvider(
        api_key=key,
        base_url=profile.base_url or "https://api.openai.com/v1",
        default_model=profile.model,
        timeout=profile.timeout,
    )

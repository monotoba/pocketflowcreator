from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pocketflow_creator.model.provider_profile import ProviderProfile


# Error taxonomy for provider failures
class ProviderError(RuntimeError):
    """Base class for typed provider errors. All inherit from RuntimeError for backwards compatibility."""

    pass


class ProviderTimeoutError(ProviderError):
    """Provider took too long to respond."""

    pass


class ProviderNetworkError(ProviderError):
    """Network-level failure: DNS, connection refused, etc."""

    pass


class ProviderRateLimitError(ProviderError):
    """Provider rate limit (HTTP 429). May include Retry-After header."""

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class SessionExpiredError(ProviderError):
    """Provider session/token expired (HTTP 401/403 with expired/invalid/unauthorized in body)."""

    def __init__(self, message: str, reinstatement_at: datetime | None = None):
        super().__init__(message)
        self.reinstatement_at = reinstatement_at


class UnknownProviderError(ProviderError):
    """Unexpected provider error (response parsing, unknown HTTP code, etc.)."""

    pass


class AllProvidersFailedError(ProviderError):
    """All providers in the failover pool exhausted their retries."""

    pass


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
        import socket
        import sys

        url = f"{self.base_url.rstrip('/')}/api/generate"
        model_name = model or self.default_model
        payload = json.dumps({"model": model_name, "prompt": prompt, "stream": False}).encode()
        print(f"[OllamaProvider] URL: {url}", file=sys.stderr)
        print(f"[OllamaProvider] Request: {payload.decode()}", file=sys.stderr)
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read())
                return str(body.get("response", ""))
        except urllib.error.HTTPError as exc:
            print(f"[OllamaProvider] HTTPError: {exc.code} {exc.reason}", file=sys.stderr)
            print(f"[OllamaProvider] URL was: {url}", file=sys.stderr)
            print(f"[OllamaProvider] Request was: {payload.decode()}", file=sys.stderr)
            detail = f"{exc.code} {exc.reason}"
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
                pass
            detail = detail or f"{exc.code} {exc.reason}"
            if "not found" in detail.lower() or "unknown" in detail.lower():
                detail = f"{detail}. Make sure '{model_name}' is installed in Ollama (ollama pull {model_name})"
            if exc.code == 429:
                retry_after = exc.headers.get("Retry-After")
                retry_after_float = float(retry_after) if retry_after else None
                raise ProviderRateLimitError(f"Ollama request failed: {detail}", retry_after=retry_after_float) from exc
            elif exc.code in (401, 403) and any(k in detail.lower() for k in ("expired", "invalid", "unauthorized")):
                raise SessionExpiredError(f"Ollama request failed: {detail}") from exc
            else:
                raise UnknownProviderError(f"Ollama request failed: {detail}") from exc
        except urllib.error.URLError as exc:
            reason = str(exc.reason) if exc.reason else str(exc)
            print(f"[OllamaProvider] URLError: {reason}", file=sys.stderr)
            if isinstance(exc.reason, socket.timeout):
                raise ProviderTimeoutError(f"Ollama request failed: {reason}") from exc
            elif isinstance(exc.reason, (socket.gaierror, ConnectionRefusedError, BrokenPipeError)):
                raise ProviderNetworkError(f"Ollama request failed: {reason}") from exc
            else:
                raise ProviderNetworkError(f"Ollama request failed: {reason}") from exc
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            print(f"[OllamaProvider] Response parsing error: {exc}", file=sys.stderr)
            raise UnknownProviderError(f"Ollama returned unexpected response: {exc}") from exc


@dataclass(slots=True)
class OpenAIProvider:
    """OpenAI chat completions — also works with any OpenAI-compatible endpoint."""

    api_key: str
    base_url: str = "https://api.openai.com/v1"
    default_model: str = "gpt-4o-mini"
    timeout: int = 120

    def complete(self, prompt: str, *, model: str | None = None) -> str:
        import socket

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
            if exc.code == 429:
                retry_after = exc.headers.get("Retry-After")
                retry_after_float = float(retry_after) if retry_after else None
                raise ProviderRateLimitError(f"OpenAI request failed: {detail}", retry_after=retry_after_float) from exc
            elif exc.code in (401, 403) and any(k in detail.lower() for k in ("expired", "invalid", "unauthorized")):
                raise SessionExpiredError(f"OpenAI request failed: {detail}") from exc
            else:
                raise UnknownProviderError(f"OpenAI request failed: {detail}") from exc
        except urllib.error.URLError as exc:
            reason = str(exc.reason) if exc.reason else str(exc)
            if isinstance(exc.reason, socket.timeout):
                raise ProviderTimeoutError(f"OpenAI request failed: {reason}") from exc
            elif isinstance(exc.reason, (socket.gaierror, ConnectionRefusedError, BrokenPipeError)):
                raise ProviderNetworkError(f"OpenAI request failed: {reason}") from exc
            else:
                raise ProviderNetworkError(f"OpenAI request failed: {reason}") from exc
        except (json.JSONDecodeError, KeyError, IndexError, ValueError) as exc:
            raise UnknownProviderError(f"OpenAI returned unexpected response: {exc}") from exc


@dataclass(slots=True)
class AnthropicProvider:
    """Anthropic Messages API."""

    api_key: str
    default_model: str = "claude-haiku-4-5"
    timeout: int = 120

    def complete(self, prompt: str, *, model: str | None = None) -> str:
        import socket

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
            if exc.code == 429:
                retry_after = exc.headers.get("Retry-After")
                retry_after_float = float(retry_after) if retry_after else None
                raise ProviderRateLimitError(f"Anthropic request failed: {detail}", retry_after=retry_after_float) from exc
            elif exc.code in (401, 403) and any(k in detail.lower() for k in ("expired", "invalid", "unauthorized")):
                raise SessionExpiredError(f"Anthropic request failed: {detail}") from exc
            else:
                raise UnknownProviderError(f"Anthropic request failed: {detail}") from exc
        except urllib.error.URLError as exc:
            reason = str(exc.reason) if exc.reason else str(exc)
            if isinstance(exc.reason, socket.timeout):
                raise ProviderTimeoutError(f"Anthropic request failed: {reason}") from exc
            elif isinstance(exc.reason, (socket.gaierror, ConnectionRefusedError, BrokenPipeError)):
                raise ProviderNetworkError(f"Anthropic request failed: {reason}") from exc
            else:
                raise ProviderNetworkError(f"Anthropic request failed: {reason}") from exc
        except (json.JSONDecodeError, KeyError, IndexError) as exc:
            raise UnknownProviderError(f"Anthropic returned unexpected response: {exc}") from exc


@dataclass(slots=True)
class GeminiProvider:
    """Google Gemini generateContent API."""

    api_key: str
    default_model: str = "gemini-2.0-flash"
    timeout: int = 120

    def complete(self, prompt: str, *, model: str | None = None) -> str:
        import socket

        mdl = model or self.default_model
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{mdl}:generateContent?key={self.api_key}"
        payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
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
            if exc.code == 429:
                retry_after = exc.headers.get("Retry-After")
                retry_after_float = float(retry_after) if retry_after else None
                raise ProviderRateLimitError(f"Gemini request failed: {detail}", retry_after=retry_after_float) from exc
            elif exc.code in (401, 403) and any(k in detail.lower() for k in ("expired", "invalid", "unauthorized")):
                raise SessionExpiredError(f"Gemini request failed: {detail}") from exc
            else:
                raise UnknownProviderError(f"Gemini request failed: {detail}") from exc
        except urllib.error.URLError as exc:
            reason = str(exc.reason) if exc.reason else str(exc)
            if isinstance(exc.reason, socket.timeout):
                raise ProviderTimeoutError(f"Gemini request failed: {reason}") from exc
            elif isinstance(exc.reason, (socket.gaierror, ConnectionRefusedError, BrokenPipeError)):
                raise ProviderNetworkError(f"Gemini request failed: {reason}") from exc
            else:
                raise ProviderNetworkError(f"Gemini request failed: {reason}") from exc
        except (json.JSONDecodeError, KeyError, IndexError) as exc:
            raise UnknownProviderError(f"Gemini returned unexpected response: {exc}") from exc


@dataclass(slots=True)
class DeepSeekProvider:
    """DeepSeek API (OpenAI-compatible)."""

    api_key: str
    base_url: str = "https://api.deepseek.com/v1"
    default_model: str = "deepseek-chat"
    timeout: int = 120

    def complete(self, prompt: str, *, model: str | None = None) -> str:
        import socket

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
            if exc.code == 429:
                retry_after = exc.headers.get("Retry-After")
                retry_after_float = float(retry_after) if retry_after else None
                raise ProviderRateLimitError(f"DeepSeek request failed: {detail}", retry_after=retry_after_float) from exc
            elif exc.code in (401, 403) and any(k in detail.lower() for k in ("expired", "invalid", "unauthorized")):
                raise SessionExpiredError(f"DeepSeek request failed: {detail}") from exc
            else:
                raise UnknownProviderError(f"DeepSeek request failed: {detail}") from exc
        except urllib.error.URLError as exc:
            reason = str(exc.reason) if exc.reason else str(exc)
            if isinstance(exc.reason, socket.timeout):
                raise ProviderTimeoutError(f"DeepSeek request failed: {reason}") from exc
            elif isinstance(exc.reason, (socket.gaierror, ConnectionRefusedError, BrokenPipeError)):
                raise ProviderNetworkError(f"DeepSeek request failed: {reason}") from exc
            else:
                raise ProviderNetworkError(f"DeepSeek request failed: {reason}") from exc
        except (json.JSONDecodeError, KeyError, IndexError, ValueError) as exc:
            raise UnknownProviderError(f"DeepSeek returned unexpected response: {exc}") from exc


# ── failover provider ────────────────────────────────────────────────────────


@dataclass(slots=True)
class ProviderEntry:
    """Configuration for a single provider in a failover pool."""

    priority: int
    provider: LLMProvider
    model: str | None = None
    timeout_retries: int = 3
    network_retries: int = 3
    ratelimit_retries: int = 2
    expired_retries: int = 1
    unknown_retries: int = 1
    retry_delay: float = 2.0
    session_offset_seconds: int = 60


class FailoverProvider:
    """Composite provider that retries across multiple providers on failure."""

    def __init__(self, entries: list[ProviderEntry], cooldowns: dict[str, float] | None = None):
        """Initialize with a list of provider entries and optional cooldown state.

        *entries* is a list of ProviderEntry, sorted by priority (lowest first).
        *cooldowns* is a dict (e.g. from shared_store) that maps provider keys to
        Unix timestamps; entries are skipped if now < cooldowns[key].
        """
        import time

        self.entries = sorted(entries, key=lambda e: e.priority)
        self._cooldowns = cooldowns or {}
        self._time = time

    def complete(self, prompt: str, *, model: str | None = None) -> str:
        """Try each provider in priority order with per-error-type retries.

        On SessionExpiredError, mark provider as unavailable until reinstatement_at + offset.
        On all providers exhausted, raise AllProvidersFailedError.
        """
        now = self._time.time()
        last_error: Exception | None = None

        for entry in self.entries:
            provider_key = str(id(entry.provider))

            # Skip if on cooldown
            if provider_key in self._cooldowns and now < self._cooldowns[provider_key]:
                continue

            # Attempt to call this provider with retries
            last_error = self._try_provider_with_retries(entry, provider_key, now, prompt, model)
            if last_error is None:
                # Success on this provider
                return ""  # This line should never be reached (see _try_provider_with_retries)

        # All providers exhausted
        if last_error:
            raise AllProvidersFailedError(f"All providers failed; last error: {last_error}") from last_error
        raise AllProvidersFailedError("All providers in failover pool exhausted retries")

    def _try_provider_with_retries(
        self,
        entry: ProviderEntry,
        provider_key: str,
        now: float,
        prompt: str,
        model: str | None,
    ) -> Exception | None:
        """Try a single provider with typed retries. Returns error if all retries fail."""
        error_retry_counts = {
            ProviderTimeoutError: entry.timeout_retries,
            ProviderNetworkError: entry.network_retries,
            ProviderRateLimitError: entry.ratelimit_retries,
            SessionExpiredError: entry.expired_retries,
            UnknownProviderError: entry.unknown_retries,
        }

        for attempt in range(max(error_retry_counts.values()) + 1):
            try:
                result = entry.provider.complete(prompt, model=entry.model or model)
                return None  # Success
            except ProviderTimeoutError as exc:
                if attempt < entry.timeout_retries:
                    self._time.sleep(entry.retry_delay)
                    continue
                return exc
            except ProviderNetworkError as exc:
                if attempt < entry.network_retries:
                    self._time.sleep(entry.retry_delay)
                    continue
                return exc
            except ProviderRateLimitError as exc:
                if attempt < entry.ratelimit_retries:
                    delay = exc.retry_after if exc.retry_after else entry.retry_delay
                    self._time.sleep(delay)
                    continue
                return exc
            except SessionExpiredError as exc:
                if attempt < entry.expired_retries:
                    self._time.sleep(entry.retry_delay)
                    continue
                # Mark provider as unavailable
                if exc.reinstatement_at:
                    cooldown_until = exc.reinstatement_at.timestamp() + entry.session_offset_seconds
                    self._cooldowns[provider_key] = cooldown_until
                return exc
            except UnknownProviderError as exc:
                if attempt < entry.unknown_retries:
                    self._time.sleep(entry.retry_delay)
                    continue
                return exc
            except Exception as exc:
                return UnknownProviderError(f"Unexpected error: {exc}")

        return None


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

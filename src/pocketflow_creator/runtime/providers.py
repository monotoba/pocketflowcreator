from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol


class LLMProvider(Protocol):
    def complete(self, prompt: str, *, model: str | None = None) -> str:
        ...


@dataclass(slots=True)
class MockProvider:
    response: str = "mock response"

    def complete(self, prompt: str, *, model: str | None = None) -> str:
        return self.response


@dataclass(slots=True)
class OllamaProvider:
    base_url: str = "http://localhost:11434"
    default_model: str = "qwen2.5-coder:14b"
    timeout: int = 120

    def complete(self, prompt: str, *, model: str | None = None) -> str:
        url = f"{self.base_url.rstrip('/')}/api/generate"
        payload = json.dumps(
            {"model": model or self.default_model, "prompt": prompt, "stream": False}
        ).encode()
        req = urllib.request.Request(
            url, data=payload, headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read())
                return str(body.get("response", ""))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Ollama request failed: {exc}") from exc

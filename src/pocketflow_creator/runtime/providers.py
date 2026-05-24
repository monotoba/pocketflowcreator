from __future__ import annotations

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

    def complete(self, prompt: str, *, model: str | None = None) -> str:
        raise NotImplementedError(
            "OllamaProvider is a design stub in this scaffold. "
            "Implement HTTP integration before using real models."
        )

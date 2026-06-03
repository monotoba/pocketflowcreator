"""Provider profile model — persisted in the project file (API keys optionally)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

# Supported API protocol types.
PROVIDER_TYPES = ("openai_compat", "anthropic", "gemini", "ollama", "lm_studio")

# Human-readable labels shown in the dialog dropdown.
PROVIDER_TYPE_LABELS = {
    "openai_compat": "OpenAI-compatible (OpenAI, DeepSeek, Azure, Groq, …)",
    "anthropic":     "Anthropic (Claude)",
    "gemini":        "Google Gemini",
    "ollama":        "Ollama (local)",
    "lm_studio":     "LM Studio (local)",
}

# Default base URLs per type.
DEFAULT_BASE_URLS = {
    "openai_compat": "https://api.openai.com/v1",
    "ollama":        "http://localhost:11434",
    "lm_studio":     "http://localhost:1234/v1",
}

# Default model per type.
DEFAULT_MODELS = {
    "openai_compat": "gpt-4o-mini",
    "anthropic":     "claude-haiku-4-5",
    "gemini":        "gemini-2.0-flash",
    "ollama":        "qwen2.5",
    "lm_studio":     "meta-llama-3.1-8b",
}


@dataclass
class ProviderProfile:
    """A named, reusable LLM provider configuration.

    api_key is *not* persisted in the project YAML by default; it is stored
    separately in QSettings (keyed by profile id).  When the project's
    ``include_api_keys`` flag is True the key is also written into the
    project file so the project is fully portable.
    """

    id: str              # stable UUID — never displayed
    name: str            # user-visible name ("Fast Claude", "Local Ollama", …)
    type: str            # one of PROVIDER_TYPES
    model: str           # default model string
    base_url: str = ""   # used for openai_compat; ignored for others
    timeout: int = 120   # request timeout in seconds

    # Not persisted in the project unless include_api_keys is True.
    # Populated at runtime from QSettings or project YAML.
    api_key: str = ""

    @staticmethod
    def new(name: str, ptype: str = "openai_compat") -> ProviderProfile:
        """Create a new profile with a fresh UUID and sensible defaults."""
        return ProviderProfile(
            id=str(uuid.uuid4()),
            name=name,
            type=ptype,
            model=DEFAULT_MODELS.get(ptype, ""),
            base_url=DEFAULT_BASE_URLS.get(ptype, ""),
        )

    def to_dict(self, *, include_api_key: bool = False) -> dict[str, Any]:
        d: dict[str, Any] = {
            "id":       self.id,
            "name":     self.name,
            "type":     self.type,
            "model":    self.model,
            "timeout":  self.timeout,
        }
        if self.base_url:
            d["base_url"] = self.base_url
        if include_api_key:
            d["api_key"] = self.api_key
        return d

    @staticmethod
    def from_dict(data: dict[str, Any]) -> ProviderProfile:
        return ProviderProfile(
            id=str(data["id"]),
            name=str(data["name"]),
            type=str(data.get("type", "openai_compat")),
            model=str(data.get("model", "")),
            base_url=str(data.get("base_url", "")),
            timeout=int(data.get("timeout", 120)),
            api_key=str(data.get("api_key", "")),
        )


@dataclass
class ProjectProviders:
    """Collection of provider profiles attached to a project."""

    profiles: list[ProviderProfile] = field(default_factory=list)
    default_profile_id: str = ""
    include_api_keys: bool = False

    @property
    def default_profile(self) -> ProviderProfile | None:
        for p in self.profiles:
            if p.id == self.default_profile_id:
                return p
        return self.profiles[0] if self.profiles else None

    def by_id(self, profile_id: str) -> ProviderProfile | None:
        return next((p for p in self.profiles if p.id == profile_id), None)

    def to_dict(self) -> dict[str, Any]:
        return {
            "include_api_keys":   self.include_api_keys,
            "default_profile_id": self.default_profile_id,
            "profiles": [p.to_dict(include_api_key=self.include_api_keys) for p in self.profiles],
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> ProjectProviders:
        include = bool(data.get("include_api_keys", False))
        profiles = [ProviderProfile.from_dict(pd) for pd in data.get("profiles", [])]
        return ProjectProviders(
            profiles=profiles,
            default_profile_id=str(data.get("default_profile_id", "")),
            include_api_keys=include,
        )

    @staticmethod
    def default_empty() -> ProjectProviders:
        """Return a sane default when a project has no provider config yet."""
        return ProjectProviders()

"""Centralised QSettings organisation, application, and key-string constants.

All modules that read or write ``QSettings("Monotoba", "PocketFlowCreator")``
should import from here so that renaming a key requires a single-file change.
"""

# ── QSettings identity ────────────────────────────────────────────────────────
_ORG = "Monotoba"
_APP = "PocketFlowCreator"

# ── Provider / LLM ────────────────────────────────────────────────────────────
_SKEY_PROVIDER = "run/provider"

# Ollama (local)
_SKEY_OLLAMA_URL = "ollama/base_url"
_SKEY_OLLAMA_MODEL = "ollama/default_model"
_SKEY_OLLAMA_TIMEOUT = "ollama/timeout"

# Mock
_SKEY_MOCK_RESPONSE = "mock/response"

# OpenAI
_SKEY_OPENAI_API_KEY = "openai/api_key"
_SKEY_OPENAI_BASE_URL = "openai/base_url"
_SKEY_OPENAI_MODEL = "openai/default_model"
_SKEY_OPENAI_TIMEOUT = "openai/timeout"

# Anthropic
_SKEY_ANTHROPIC_API_KEY = "anthropic/api_key"
_SKEY_ANTHROPIC_MODEL = "anthropic/default_model"
_SKEY_ANTHROPIC_TIMEOUT = "anthropic/timeout"

# Gemini
_SKEY_GEMINI_API_KEY = "gemini/api_key"
_SKEY_GEMINI_MODEL = "gemini/default_model"
_SKEY_GEMINI_TIMEOUT = "gemini/timeout"

# DeepSeek
_SKEY_DEEPSEEK_API_KEY = "deepseek/api_key"
_SKEY_DEEPSEEK_BASE_URL = "deepseek/base_url"
_SKEY_DEEPSEEK_MODEL = "deepseek/default_model"
_SKEY_DEEPSEEK_TIMEOUT = "deepseek/timeout"


def provider_profile_api_key_skey(profile_id: str) -> str:
    """Return the QSettings key for a provider profile's API key."""
    return f"provider_profiles/{profile_id}/api_key"


_SKEY_GLOBAL_PROVIDER_PROFILES = "provider_profiles/global_profiles"


# ── UI state ──────────────────────────────────────────────────────────────────
_SKEY_RECENT = "recent_projects"
_SKEY_THEME = "ui/theme"
_SKEY_DARK_MODE = "ui/dark_mode"  # legacy key — read-once migration only
_SKEY_LOCALE = "ui/locale"

# ── Window layout ─────────────────────────────────────────────────────────────
_SKEY_LAYOUT_GEOMETRY = "ui/layout/geometry"
_SKEY_LAYOUT_STATE = "ui/layout/window_state"
_SKEY_LAYOUT_SPLITTER = "ui/layout/md_splitter"

# ── Toolbar ───────────────────────────────────────────────────────────────────
_SKEY_TOOLBAR_ORDER = "ui/toolbar/node_palette_order"

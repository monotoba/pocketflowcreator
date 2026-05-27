"""Centralised QSettings organisation, application, and key-string constants.

All modules that read or write ``QSettings("Monotoba", "PocketFlowCreator")``
should import from here so that renaming a key requires a single-file change.
"""

# ── QSettings identity ────────────────────────────────────────────────────────
_ORG = "Monotoba"
_APP = "PocketFlowCreator"

# ── Provider / LLM ────────────────────────────────────────────────────────────
_SKEY_PROVIDER = "run/provider"
_SKEY_OLLAMA_URL = "ollama/base_url"
_SKEY_OLLAMA_MODEL = "ollama/default_model"
_SKEY_OLLAMA_TIMEOUT = "ollama/timeout"
_SKEY_MOCK_RESPONSE = "mock/response"

# ── UI state ──────────────────────────────────────────────────────────────────
_SKEY_RECENT = "recent_projects"
_SKEY_THEME = "ui/theme"
_SKEY_DARK_MODE = "ui/dark_mode"       # legacy key — read-once migration only
_SKEY_LOCALE = "ui/locale"

# ── Window layout ─────────────────────────────────────────────────────────────
_SKEY_LAYOUT_GEOMETRY = "ui/layout/geometry"
_SKEY_LAYOUT_STATE = "ui/layout/window_state"
_SKEY_LAYOUT_SPLITTER = "ui/layout/md_splitter"

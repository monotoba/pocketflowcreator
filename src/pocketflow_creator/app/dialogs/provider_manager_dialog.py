"""ProviderManagerDialog — configure the active LLM provider and its settings."""
from __future__ import annotations

import json
import threading
import urllib.request
from collections.abc import Callable
from typing import TYPE_CHECKING

from pocketflow_creator.app.settings_keys import (
    _APP,
    _ORG,
    _SKEY_ANTHROPIC_API_KEY,
    _SKEY_ANTHROPIC_MODEL,
    _SKEY_ANTHROPIC_TIMEOUT,
    _SKEY_DEEPSEEK_API_KEY,
    _SKEY_DEEPSEEK_BASE_URL,
    _SKEY_DEEPSEEK_MODEL,
    _SKEY_DEEPSEEK_TIMEOUT,
    _SKEY_GEMINI_API_KEY,
    _SKEY_GEMINI_MODEL,
    _SKEY_GEMINI_TIMEOUT,
    _SKEY_MOCK_RESPONSE,
    _SKEY_OLLAMA_MODEL,
    _SKEY_OLLAMA_TIMEOUT,
    _SKEY_OLLAMA_URL,
    _SKEY_OPENAI_API_KEY,
    _SKEY_OPENAI_BASE_URL,
    _SKEY_OPENAI_MODEL,
    _SKEY_OPENAI_TIMEOUT,
    _SKEY_PROVIDER,
)

if TYPE_CHECKING:
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import (
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QPushButton,
        QRadioButton,
        QSpinBox,
        QVBoxLayout,
        QWidget,
    )
else:
    try:
        from PySide6.QtCore import QSettings
        from PySide6.QtWidgets import (
            QComboBox,
            QDialog,
            QDialogButtonBox,
            QFormLayout,
            QGroupBox,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QMainWindow,
            QPushButton,
            QRadioButton,
            QSpinBox,
            QVBoxLayout,
            QWidget,
        )
    except ImportError:  # pragma: no cover
        QDialog = object  # type: ignore[assignment,misc]


# ── helpers ──────────────────────────────────────────────────────────────────

def _api_key_field(placeholder: str = "sk-…") -> QLineEdit:
    """Return a password-mode QLineEdit for an API key."""
    field: QLineEdit = QLineEdit()
    field.setEchoMode(QLineEdit.EchoMode.Password)
    field.setPlaceholderText(placeholder)
    return field


def _spin(lo: int, hi: int, step: int, suffix: str, value: int) -> QSpinBox:
    s: QSpinBox = QSpinBox()
    s.setRange(lo, hi)
    s.setSingleStep(step)
    s.setSuffix(suffix)
    s.setValue(value)
    return s


def fetch_ollama_models(base_url: str) -> list[str]:
    """Return a sorted list of model names from the Ollama /api/tags endpoint."""
    try:
        url = f"{base_url.rstrip('/')}/api/tags"
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read())
        return sorted(m["name"] for m in data.get("models", []))
    except Exception:
        return []


def _test_provider(prov_type: str, fields: dict[str, QLineEdit | QSpinBox | QComboBox],
                   status_label: QLabel) -> None:
    """Fire a cheap test call in a background thread and update status_label."""
    status_label.setText("Testing…")

    def _run() -> None:
        try:
            from pocketflow_creator.runtime.providers import (
                AnthropicProvider,
                DeepSeekProvider,
                GeminiProvider,
                OllamaProvider,
                OpenAIProvider,
            )
            prompt = "Reply with the single word: ok"

            def _str(key: str) -> str:
                w = fields[key]
                if isinstance(w, QLineEdit):
                    return w.text().strip()
                if isinstance(w, QComboBox):
                    return w.currentText().strip()
                return ""

            def _int(key: str, default: int) -> int:
                w = fields.get(key)
                if isinstance(w, QSpinBox):
                    return w.value()
                return default

            if prov_type == "ollama":
                p = OllamaProvider(
                    base_url=_str("base_url"),
                    default_model=_str("model"),
                    timeout=_int("timeout", 30),
                )
            elif prov_type == "openai":
                p = OpenAIProvider(
                    api_key=_str("api_key"),
                    base_url=_str("base_url"),
                    default_model=_str("model"),
                    timeout=_int("timeout", 30),
                )
            elif prov_type == "anthropic":
                p = AnthropicProvider(
                    api_key=_str("api_key"),
                    default_model=_str("model"),
                    timeout=_int("timeout", 30),
                )
            elif prov_type == "gemini":
                p = GeminiProvider(
                    api_key=_str("api_key"),
                    default_model=_str("model"),
                    timeout=_int("timeout", 30),
                )
            elif prov_type == "deepseek":
                p = DeepSeekProvider(
                    api_key=_str("api_key"),
                    base_url=_str("base_url"),
                    default_model=_str("model"),
                    timeout=_int("timeout", 30),
                )
            else:
                status_label.setText("⚠ Unknown provider")
                return

            p.complete(prompt)
            status_label.setText("✓ Connection successful")
        except Exception as exc:
            short = str(exc)[:120]
            status_label.setText(f"✗ {short}")

    threading.Thread(target=_run, daemon=True).start()


# ── group builders ────────────────────────────────────────────────────────────

def _ollama_group(settings: QSettings) -> tuple[QGroupBox, dict]:
    saved_url = str(settings.value(_SKEY_OLLAMA_URL, "http://localhost:11434"))
    saved_model = str(settings.value(_SKEY_OLLAMA_MODEL, "qwen2.5-coder:14b"))
    saved_timeout = int(str(settings.value(_SKEY_OLLAMA_TIMEOUT, 120)))

    grp: QGroupBox = QGroupBox("Ollama Settings")
    form: QFormLayout = QFormLayout(grp)

    url_field: QLineEdit = QLineEdit(saved_url)
    form.addRow("Base URL:", url_field)

    model_row: QHBoxLayout = QHBoxLayout()
    model_combo: QComboBox = QComboBox()
    model_combo.setEditable(True)
    model_combo.setMinimumWidth(220)
    refresh_btn: QPushButton = QPushButton("Refresh")
    model_row.addWidget(model_combo)
    model_row.addWidget(refresh_btn)
    form.addRow("Default model:", model_row)

    timeout_spin = _spin(5, 3600, 15, " s", saved_timeout)
    timeout_spin.setToolTip("Maximum seconds to wait for a response.")
    form.addRow("Timeout:", timeout_spin)

    status: QLabel = QLabel()
    test_btn: QPushButton = QPushButton("Test Connection")
    test_row: QHBoxLayout = QHBoxLayout()
    test_row.addWidget(test_btn)
    test_row.addWidget(status)
    test_row.addStretch()
    form.addRow("", test_row)

    fields = {"base_url": url_field, "model": model_combo, "timeout": timeout_spin}

    def _populate(select: str = "") -> None:
        models = fetch_ollama_models(url_field.text().strip())
        model_combo.clear()
        if models:
            model_combo.addItems(models)
            idx = model_combo.findText(select or saved_model)
            model_combo.setCurrentIndex(max(idx, 0))
        else:
            model_combo.addItem(select or saved_model)
            model_combo.setCurrentIndex(0)

    _populate(saved_model)
    refresh_btn.clicked.connect(lambda: _populate(model_combo.currentText()))
    test_btn.clicked.connect(lambda: _test_provider("ollama", fields, status))

    return grp, fields


def _openai_group(settings: QSettings) -> tuple[QGroupBox, dict]:
    grp: QGroupBox = QGroupBox("OpenAI Settings")
    form: QFormLayout = QFormLayout(grp)

    key_field = _api_key_field()
    key_field.setText(str(settings.value(_SKEY_OPENAI_API_KEY, "")))
    form.addRow("API Key:", key_field)

    base_url: QLineEdit = QLineEdit(str(settings.value(_SKEY_OPENAI_BASE_URL, "https://api.openai.com/v1")))
    base_url.setToolTip("Change for Azure OpenAI or other OpenAI-compatible endpoints.")
    form.addRow("Base URL:", base_url)

    model_field: QLineEdit = QLineEdit(str(settings.value(_SKEY_OPENAI_MODEL, "gpt-4o-mini")))
    form.addRow("Default model:", model_field)

    timeout_spin = _spin(5, 3600, 15, " s", int(str(settings.value(_SKEY_OPENAI_TIMEOUT, 120))))
    form.addRow("Timeout:", timeout_spin)

    status: QLabel = QLabel()
    test_btn: QPushButton = QPushButton("Test Connection")
    test_row: QHBoxLayout = QHBoxLayout()
    test_row.addWidget(test_btn)
    test_row.addWidget(status)
    test_row.addStretch()
    form.addRow("", test_row)

    fields = {"api_key": key_field, "base_url": base_url, "model": model_field, "timeout": timeout_spin}
    test_btn.clicked.connect(lambda: _test_provider("openai", fields, status))
    return grp, fields


def _anthropic_group(settings: QSettings) -> tuple[QGroupBox, dict]:
    grp: QGroupBox = QGroupBox("Anthropic Settings")
    form: QFormLayout = QFormLayout(grp)

    key_field = _api_key_field()
    key_field.setText(str(settings.value(_SKEY_ANTHROPIC_API_KEY, "")))
    form.addRow("API Key:", key_field)

    model_field: QLineEdit = QLineEdit(str(settings.value(_SKEY_ANTHROPIC_MODEL, "claude-haiku-4-5")))
    model_field.setToolTip("e.g. claude-haiku-4-5, claude-sonnet-4-6, claude-opus-4-8")
    form.addRow("Default model:", model_field)

    timeout_spin = _spin(5, 3600, 15, " s", int(str(settings.value(_SKEY_ANTHROPIC_TIMEOUT, 120))))
    form.addRow("Timeout:", timeout_spin)

    status: QLabel = QLabel()
    test_btn: QPushButton = QPushButton("Test Connection")
    test_row: QHBoxLayout = QHBoxLayout()
    test_row.addWidget(test_btn)
    test_row.addWidget(status)
    test_row.addStretch()
    form.addRow("", test_row)

    fields = {"api_key": key_field, "model": model_field, "timeout": timeout_spin}
    test_btn.clicked.connect(lambda: _test_provider("anthropic", fields, status))
    return grp, fields


def _gemini_group(settings: QSettings) -> tuple[QGroupBox, dict]:
    grp: QGroupBox = QGroupBox("Gemini Settings")
    form: QFormLayout = QFormLayout(grp)

    key_field = _api_key_field("AIza…")
    key_field.setText(str(settings.value(_SKEY_GEMINI_API_KEY, "")))
    form.addRow("API Key:", key_field)

    model_field: QLineEdit = QLineEdit(str(settings.value(_SKEY_GEMINI_MODEL, "gemini-2.0-flash")))
    model_field.setToolTip("e.g. gemini-2.0-flash, gemini-1.5-pro")
    form.addRow("Default model:", model_field)

    timeout_spin = _spin(5, 3600, 15, " s", int(str(settings.value(_SKEY_GEMINI_TIMEOUT, 120))))
    form.addRow("Timeout:", timeout_spin)

    status: QLabel = QLabel()
    test_btn: QPushButton = QPushButton("Test Connection")
    test_row: QHBoxLayout = QHBoxLayout()
    test_row.addWidget(test_btn)
    test_row.addWidget(status)
    test_row.addStretch()
    form.addRow("", test_row)

    fields = {"api_key": key_field, "model": model_field, "timeout": timeout_spin}
    test_btn.clicked.connect(lambda: _test_provider("gemini", fields, status))
    return grp, fields


def _deepseek_group(settings: QSettings) -> tuple[QGroupBox, dict]:
    grp: QGroupBox = QGroupBox("DeepSeek Settings")
    form: QFormLayout = QFormLayout(grp)

    key_field = _api_key_field()
    key_field.setText(str(settings.value(_SKEY_DEEPSEEK_API_KEY, "")))
    form.addRow("API Key:", key_field)

    base_url: QLineEdit = QLineEdit(str(settings.value(_SKEY_DEEPSEEK_BASE_URL, "https://api.deepseek.com/v1")))
    form.addRow("Base URL:", base_url)

    model_field: QLineEdit = QLineEdit(str(settings.value(_SKEY_DEEPSEEK_MODEL, "deepseek-chat")))
    model_field.setToolTip("e.g. deepseek-chat, deepseek-reasoner")
    form.addRow("Default model:", model_field)

    timeout_spin = _spin(5, 3600, 15, " s", int(str(settings.value(_SKEY_DEEPSEEK_TIMEOUT, 120))))
    form.addRow("Timeout:", timeout_spin)

    status: QLabel = QLabel()
    test_btn: QPushButton = QPushButton("Test Connection")
    test_row: QHBoxLayout = QHBoxLayout()
    test_row.addWidget(test_btn)
    test_row.addWidget(status)
    test_row.addStretch()
    form.addRow("", test_row)

    fields = {"api_key": key_field, "base_url": base_url, "model": model_field, "timeout": timeout_spin}
    test_btn.clicked.connect(lambda: _test_provider("deepseek", fields, status))
    return grp, fields


def _mock_group(settings: QSettings) -> tuple[QGroupBox, dict]:
    grp: QGroupBox = QGroupBox("Mock Settings")
    form: QFormLayout = QFormLayout(grp)
    resp_field: QLineEdit = QLineEdit(str(settings.value(_SKEY_MOCK_RESPONSE, "mock response")))
    form.addRow("Fixed response:", resp_field)
    return grp, {"response": resp_field}


# ── public entry point ────────────────────────────────────────────────────────

def exec_provider_manager(
    parent: QMainWindow,
    open_help: Callable[[str], None],
) -> bool:
    """Show the Provider Manager dialog.

    Reads and writes QSettings directly.  Returns True if accepted.
    """
    settings = QSettings(_ORG, _APP)
    dlg: QDialog = QDialog(parent)
    dlg.setWindowTitle("Provider Manager")
    dlg.setMinimumWidth(480)
    root: QVBoxLayout = QVBoxLayout(dlg)

    # ── active provider radio group ──────────────────────────────────────────
    active_grp: QGroupBox = QGroupBox("Active Provider")
    active_layout: QVBoxLayout = QVBoxLayout(active_grp)

    providers = [
        ("mock",      "Mock (for testing)"),
        ("ollama",    "Ollama  (local)"),
        ("openai",    "OpenAI"),
        ("anthropic", "Anthropic (Claude)"),
        ("gemini",    "Google Gemini"),
        ("deepseek",  "DeepSeek"),
    ]

    radios: dict[str, QRadioButton] = {}
    for key, label in providers:
        rb: QRadioButton = QRadioButton(label)
        active_layout.addWidget(rb)
        radios[key] = rb

    current_prov = str(settings.value(_SKEY_PROVIDER, "mock"))
    if current_prov not in radios:
        current_prov = "mock"
    radios[current_prov].setChecked(True)
    root.addWidget(active_grp)

    # ── per-provider settings groups (show/hide) ─────────────────────────────
    ollama_grp, ollama_fields = _ollama_group(settings)
    openai_grp, openai_fields = _openai_group(settings)
    anthropic_grp, anthropic_fields = _anthropic_group(settings)
    gemini_grp, gemini_fields = _gemini_group(settings)
    deepseek_grp, deepseek_fields = _deepseek_group(settings)
    mock_grp, mock_fields = _mock_group(settings)

    grp_map: dict[str, QWidget] = {
        "mock":      mock_grp,
        "ollama":    ollama_grp,
        "openai":    openai_grp,
        "anthropic": anthropic_grp,
        "gemini":    gemini_grp,
        "deepseek":  deepseek_grp,
    }

    for grp in grp_map.values():
        root.addWidget(grp)

    def _update_visibility() -> None:
        chosen = next((k for k, rb in radios.items() if rb.isChecked()), "mock")
        for key, grp in grp_map.items():
            grp.setVisible(key == chosen)
        dlg.adjustSize()

    for rb in radios.values():
        rb.toggled.connect(lambda _checked: _update_visibility())

    _update_visibility()

    # ── buttons ──────────────────────────────────────────────────────────────
    buttons: QDialogButtonBox = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    help_btn = buttons.addButton("?", QDialogButtonBox.ButtonRole.HelpRole)
    help_btn.clicked.connect(lambda: open_help("context/provider_manager.md"))
    buttons.accepted.connect(dlg.accept)
    buttons.rejected.connect(dlg.reject)
    root.addWidget(buttons)

    if dlg.exec() != QDialog.DialogCode.Accepted:
        return False

    # ── persist ──────────────────────────────────────────────────────────────
    chosen = next((k for k, rb in radios.items() if rb.isChecked()), "mock")
    settings.setValue(_SKEY_PROVIDER, chosen)

    def _text(fields: dict, key: str, default: str = "") -> str:
        w = fields.get(key)
        if isinstance(w, QLineEdit):
            return w.text().strip()
        if isinstance(w, QComboBox):
            return w.currentText().strip()
        return default

    def _int_val(fields: dict, key: str, default: int = 120) -> int:
        w = fields.get(key)
        if isinstance(w, QSpinBox):
            return w.value()
        return default

    settings.setValue(_SKEY_OLLAMA_URL,        _text(ollama_fields, "base_url"))
    settings.setValue(_SKEY_OLLAMA_MODEL,      _text(ollama_fields, "model"))
    settings.setValue(_SKEY_OLLAMA_TIMEOUT,    _int_val(ollama_fields, "timeout"))

    settings.setValue(_SKEY_OPENAI_API_KEY,    _text(openai_fields, "api_key"))
    settings.setValue(_SKEY_OPENAI_BASE_URL,   _text(openai_fields, "base_url"))
    settings.setValue(_SKEY_OPENAI_MODEL,      _text(openai_fields, "model"))
    settings.setValue(_SKEY_OPENAI_TIMEOUT,    _int_val(openai_fields, "timeout"))

    settings.setValue(_SKEY_ANTHROPIC_API_KEY, _text(anthropic_fields, "api_key"))
    settings.setValue(_SKEY_ANTHROPIC_MODEL,   _text(anthropic_fields, "model"))
    settings.setValue(_SKEY_ANTHROPIC_TIMEOUT, _int_val(anthropic_fields, "timeout"))

    settings.setValue(_SKEY_GEMINI_API_KEY,    _text(gemini_fields, "api_key"))
    settings.setValue(_SKEY_GEMINI_MODEL,      _text(gemini_fields, "model"))
    settings.setValue(_SKEY_GEMINI_TIMEOUT,    _int_val(gemini_fields, "timeout"))

    settings.setValue(_SKEY_DEEPSEEK_API_KEY,  _text(deepseek_fields, "api_key"))
    settings.setValue(_SKEY_DEEPSEEK_BASE_URL, _text(deepseek_fields, "base_url"))
    settings.setValue(_SKEY_DEEPSEEK_MODEL,    _text(deepseek_fields, "model"))
    settings.setValue(_SKEY_DEEPSEEK_TIMEOUT,  _int_val(deepseek_fields, "timeout"))

    settings.setValue(_SKEY_MOCK_RESPONSE,     _text(mock_fields, "response"))
    return True

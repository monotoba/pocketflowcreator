"""ProviderManagerDialog — configure the active LLM provider and its settings."""
from __future__ import annotations

import json
import urllib.request
from collections.abc import Callable
from typing import TYPE_CHECKING

from pocketflow_creator.app.settings_keys import (
    _APP,
    _ORG,
    _SKEY_MOCK_RESPONSE,
    _SKEY_OLLAMA_MODEL,
    _SKEY_OLLAMA_TIMEOUT,
    _SKEY_OLLAMA_URL,
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
        QLineEdit,
        QMainWindow,
        QPushButton,
        QRadioButton,
        QSpinBox,
        QVBoxLayout,
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
            QLineEdit,
            QMainWindow,
            QPushButton,
            QRadioButton,
            QSpinBox,
            QVBoxLayout,
        )
    except ImportError:  # pragma: no cover
        QDialog = object  # type: ignore[assignment,misc]


def fetch_ollama_models(base_url: str) -> list[str]:
    """Return a sorted list of model names from the Ollama /api/tags endpoint."""
    try:
        url = f"{base_url.rstrip('/')}/api/tags"
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read())
        return sorted(m["name"] for m in data.get("models", []))
    except Exception:
        return []


def exec_provider_manager(
    parent: QMainWindow,
    open_help: Callable[[str], None],
) -> bool:
    """Show the Provider Manager dialog.

    Reads and writes QSettings directly.  Returns True if the user accepted
    (settings were saved), False if cancelled.
    """
    settings = QSettings(_ORG, _APP)
    dlg = QDialog(parent)
    dlg.setWindowTitle("Provider Manager")
    dlg.resize(440, 0)
    layout = QVBoxLayout(dlg)

    active_group = QGroupBox("Active Provider")
    active_layout = QVBoxLayout(active_group)
    rb_ollama = QRadioButton("Ollama")
    rb_mock = QRadioButton("Mock (for testing)")
    active_layout.addWidget(rb_ollama)
    active_layout.addWidget(rb_mock)
    current_prov = str(settings.value(_SKEY_PROVIDER, "mock"))
    if current_prov == "ollama":
        rb_ollama.setChecked(True)
    else:
        rb_mock.setChecked(True)
    layout.addWidget(active_group)

    ollama_group = QGroupBox("Ollama Provider Settings")
    ollama_form = QFormLayout(ollama_group)
    saved_url = str(settings.value(_SKEY_OLLAMA_URL, "http://localhost:11434"))
    saved_model = str(settings.value(_SKEY_OLLAMA_MODEL, "qwen2.5-coder:14b"))
    saved_timeout = int(settings.value(_SKEY_OLLAMA_TIMEOUT, 120))  # type: ignore[arg-type]
    ollama_url = QLineEdit(saved_url)
    ollama_form.addRow("Base URL:", ollama_url)

    model_row = QHBoxLayout()
    ollama_model_combo = QComboBox()
    ollama_model_combo.setEditable(True)
    ollama_model_combo.setMinimumWidth(220)
    refresh_btn = QPushButton("Refresh")
    model_row.addWidget(ollama_model_combo)
    model_row.addWidget(refresh_btn)
    ollama_form.addRow("Default model:", model_row)

    timeout_spin = QSpinBox()
    timeout_spin.setRange(5, 3600)
    timeout_spin.setSingleStep(15)
    timeout_spin.setSuffix(" s")
    timeout_spin.setValue(saved_timeout)
    timeout_spin.setToolTip(
        "Maximum seconds to wait for an Ollama response before raising a timeout error."
    )
    ollama_form.addRow("Request timeout:", timeout_spin)
    layout.addWidget(ollama_group)

    def _populate_models(select: str = "") -> None:
        models = fetch_ollama_models(ollama_url.text().strip())
        ollama_model_combo.clear()
        if models:
            ollama_model_combo.addItems(models)
            target = select or ollama_model_combo.currentText()
            idx = ollama_model_combo.findText(target)
            ollama_model_combo.setCurrentIndex(max(idx, 0))
        else:
            ollama_model_combo.addItem(select or saved_model)
            ollama_model_combo.setCurrentIndex(0)

    _populate_models(saved_model)
    refresh_btn.clicked.connect(lambda: _populate_models(ollama_model_combo.currentText()))

    mock_group = QGroupBox("Mock Provider Settings")
    mock_form = QFormLayout(mock_group)
    mock_response = QLineEdit(str(settings.value(_SKEY_MOCK_RESPONSE, "mock response")))
    mock_form.addRow("Fixed response:", mock_response)
    layout.addWidget(mock_group)

    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    help_btn = buttons.addButton("?", QDialogButtonBox.ButtonRole.HelpRole)
    help_btn.clicked.connect(lambda: open_help("context/provider_manager.md"))
    buttons.accepted.connect(dlg.accept)
    buttons.rejected.connect(dlg.reject)
    layout.addWidget(buttons)

    if dlg.exec() != QDialog.DialogCode.Accepted:
        return False

    settings.setValue(_SKEY_PROVIDER, "ollama" if rb_ollama.isChecked() else "mock")
    settings.setValue(_SKEY_OLLAMA_URL, ollama_url.text().strip())
    settings.setValue(_SKEY_OLLAMA_MODEL, ollama_model_combo.currentText().strip())
    settings.setValue(_SKEY_OLLAMA_TIMEOUT, timeout_spin.value())
    settings.setValue(_SKEY_MOCK_RESPONSE, mock_response.text())
    return True

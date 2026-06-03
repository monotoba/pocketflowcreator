"""ProviderManagerDialog — manage named LLM provider profiles for a project."""
from __future__ import annotations

import copy
import json
import threading
import urllib.request
from collections.abc import Callable
from typing import TYPE_CHECKING

from pocketflow_creator.app.settings_keys import (
    _APP,
    _ORG,
    provider_profile_api_key_skey,
)
from pocketflow_creator.model.provider_profile import (
    DEFAULT_BASE_URLS,
    DEFAULT_MODELS,
    PROVIDER_TYPE_LABELS,
    PROVIDER_TYPES,
    ProjectProviders,
    ProviderProfile,
)

if TYPE_CHECKING:
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import (
        QCheckBox,
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMainWindow,
        QPushButton,
        QSpinBox,
        QVBoxLayout,
        QWidget,
    )
else:
    try:
        from PySide6.QtCore import QSettings
        from PySide6.QtWidgets import (
            QCheckBox,
            QComboBox,
            QDialog,
            QDialogButtonBox,
            QFormLayout,
            QGroupBox,
            QHBoxLayout,
            QLabel,
            QLineEdit,
            QListWidget,
            QListWidgetItem,
            QMainWindow,
            QPushButton,
            QSpinBox,
            QVBoxLayout,
            QWidget,
        )
    except ImportError:  # pragma: no cover
        QDialog = object  # type: ignore[assignment,misc]


# ── small helpers ─────────────────────────────────────────────────────────────

def _key_field(placeholder: str = "sk-…") -> QLineEdit:
    f: QLineEdit = QLineEdit()
    f.setEchoMode(QLineEdit.EchoMode.Password)
    f.setPlaceholderText(placeholder)
    return f


def _spin(lo: int, hi: int, step: int, suffix: str, val: int) -> QSpinBox:
    s: QSpinBox = QSpinBox()
    s.setRange(lo, hi)
    s.setSingleStep(step)
    s.setSuffix(suffix)
    s.setValue(val)
    return s


def _load_key(profile_id: str) -> str:
    try:
        settings = QSettings(_ORG, _APP)
        return str(settings.value(provider_profile_api_key_skey(profile_id), ""))
    except Exception:
        return ""


def _save_key(profile_id: str, key: str) -> None:
    try:
        settings = QSettings(_ORG, _APP)
        settings.setValue(provider_profile_api_key_skey(profile_id), key)
    except Exception:
        pass


def fetch_ollama_models(base_url: str) -> list[str]:
    try:
        url = f"{base_url.rstrip('/')}/api/tags"
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read())
        return sorted(m["name"] for m in data.get("models", []))
    except Exception:
        return []


def _test_profile(profile: ProviderProfile, api_key: str, status: QLabel) -> None:
    """Fire a cheap probe request in a background thread."""
    status.setText("Testing…")

    def _run() -> None:
        try:
            from pocketflow_creator.runtime.providers import build_provider_from_profile
            p = build_provider_from_profile(profile, api_key)
            p.complete("Reply with the single word: ok")
            status.setText("✓ Connection successful")
        except Exception as exc:
            status.setText(f"✗ {str(exc)[:120]}")

    threading.Thread(target=_run, daemon=True).start()


# ── profile edit panel ────────────────────────────────────────────────────────

class _ProfileEditPanel(QWidget):
    """Right-hand panel for editing one provider profile."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._profile: ProviderProfile | None = None
        # api_key is kept separately so it never leaks into the profile object
        # until the user explicitly saves with include_api_keys=True
        self._current_api_key: str = ""

        form_grp: QGroupBox = QGroupBox("Profile Settings")
        self._form: QFormLayout = QFormLayout(form_grp)

        # Name
        self._name_field: QLineEdit = QLineEdit()
        self._name_field.setPlaceholderText("e.g. My OpenAI Account")
        self._form.addRow("Name:", self._name_field)

        # Type
        self._type_combo: QComboBox = QComboBox()
        for t in PROVIDER_TYPES:
            self._type_combo.addItem(PROVIDER_TYPE_LABELS[t], t)
        self._form.addRow("API type:", self._type_combo)

        # Base URL (openai_compat only)
        self._base_url_label: QLabel = QLabel("Base URL:")
        self._base_url_field: QLineEdit = QLineEdit()
        self._base_url_field.setPlaceholderText("https://api.openai.com/v1")
        self._form.addRow(self._base_url_label, self._base_url_field)

        # Model
        self._model_field: QLineEdit = QLineEdit()
        self._model_field.setPlaceholderText("e.g. gpt-4o-mini")
        self._form.addRow("Default model:", self._model_field)

        # Timeout
        self._timeout_spin = _spin(5, 3600, 15, " s", 120)
        self._form.addRow("Timeout:", self._timeout_spin)

        # API key
        self._key_field = _key_field()
        self._form.addRow("API key:", self._key_field)

        # Test
        self._test_btn: QPushButton = QPushButton("Test Connection")
        self._status_label: QLabel = QLabel()
        test_row: QHBoxLayout = QHBoxLayout()
        test_row.addWidget(self._test_btn)
        test_row.addWidget(self._status_label, 1)
        self._form.addRow("", test_row)

        # Outer layout
        outer: QVBoxLayout = QVBoxLayout(self)
        outer.addWidget(form_grp)
        outer.addStretch()

        self._type_combo.currentIndexChanged.connect(self._on_type_changed)
        self._test_btn.clicked.connect(self._on_test)

        self.setEnabled(False)

    # ── public API ────────────────────────────────────────────────────────────

    def load(self, profile: ProviderProfile, api_key: str) -> None:
        """Populate fields from *profile*. *api_key* comes from the caller's dict."""
        self._profile = profile
        self._current_api_key = api_key
        self.setEnabled(True)

        self._name_field.setText(profile.name)

        idx = self._type_combo.findData(profile.type)
        self._type_combo.setCurrentIndex(max(idx, 0))

        self._base_url_field.setText(profile.base_url)
        self._model_field.setText(profile.model)
        self._timeout_spin.setValue(profile.timeout)
        self._key_field.setText(api_key)
        self._status_label.setText("")
        self._on_type_changed()

    def flush(self) -> str:
        """Write widget values back to self._profile. Returns the current api_key."""
        if self._profile is None:
            return ""
        name = self._name_field.text().strip()
        if name:
            self._profile.name = name
        self._profile.type = self._type_combo.currentData() or "openai_compat"
        self._profile.base_url = self._base_url_field.text().strip()
        self._profile.model = self._model_field.text().strip()
        self._profile.timeout = self._timeout_spin.value()
        self._current_api_key = self._key_field.text().strip()
        return self._current_api_key

    def current_profile_id(self) -> str:
        return self._profile.id if self._profile else ""

    # ── private ───────────────────────────────────────────────────────────────

    def _on_type_changed(self) -> None:
        ptype = self._type_combo.currentData()
        is_compat = ptype == "openai_compat"
        self._base_url_label.setVisible(is_compat)
        self._base_url_field.setVisible(is_compat)
        if is_compat and not self._base_url_field.text().strip():
            self._base_url_field.setText(DEFAULT_BASE_URLS.get("openai_compat", ""))
        if self._profile is not None and not self._model_field.text().strip():
            self._model_field.setText(DEFAULT_MODELS.get(ptype, ""))

    def _on_test(self) -> None:
        if self._profile is None:
            return
        api_key = self.flush()
        _test_profile(self._profile, api_key, self._status_label)


# ── public entry point ────────────────────────────────────────────────────────

def exec_provider_manager(
    parent: QMainWindow,
    open_help: Callable[[str], None],
    providers: ProjectProviders | None = None,
) -> ProjectProviders | None:
    """Show the Provider Manager dialog.

    *providers* is the current project's provider config.
    Returns an updated ``ProjectProviders`` on accept, or ``None`` on cancel.
    """
    working = copy.deepcopy(providers) if providers else ProjectProviders()

    # api_keys tracks the key for each profile id separately from the profile object.
    # Keys come from QSettings, or from the profile if include_api_keys was True.
    api_keys: dict[str, str] = {
        p.id: (p.api_key or _load_key(p.id))
        for p in working.profiles
    }

    dlg: QDialog = QDialog(parent)
    dlg.setWindowTitle("Provider Manager")
    dlg.setMinimumSize(680, 400)
    dlg.resize(760, 500)

    # ── single layout hierarchy ───────────────────────────────────────────────
    main_layout: QVBoxLayout = QVBoxLayout(dlg)

    content_row: QHBoxLayout = QHBoxLayout()
    main_layout.addLayout(content_row, 1)

    # Left panel
    left_layout: QVBoxLayout = QVBoxLayout()
    content_row.addLayout(left_layout, 1)

    list_grp: QGroupBox = QGroupBox("Profiles")
    list_vbox: QVBoxLayout = QVBoxLayout(list_grp)

    profile_list: QListWidget = QListWidget()
    profile_list.setMinimumWidth(180)
    list_vbox.addWidget(profile_list)

    btn_row: QHBoxLayout = QHBoxLayout()
    add_btn: QPushButton = QPushButton("+ Add")
    del_btn: QPushButton = QPushButton("Delete")
    default_btn: QPushButton = QPushButton("Set Default ★")
    btn_row.addWidget(add_btn)
    btn_row.addWidget(del_btn)
    btn_row.addWidget(default_btn)
    list_vbox.addLayout(btn_row)

    left_layout.addWidget(list_grp)

    include_key_chk: QCheckBox = QCheckBox("Include API keys in project file")
    include_key_chk.setChecked(working.include_api_keys)
    include_key_chk.setToolTip(
        "When checked, API keys are saved in plain text in the .pfcproj.yaml.\n"
        "Leave unchecked to keep keys on this machine only (in app settings)."
    )
    left_layout.addWidget(include_key_chk)

    # Right panel
    edit_panel = _ProfileEditPanel()
    content_row.addWidget(edit_panel, 2)

    # Bottom buttons
    buttons: QDialogButtonBox = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    help_btn = buttons.addButton("?", QDialogButtonBox.ButtonRole.HelpRole)
    help_btn.clicked.connect(lambda: open_help("context/provider_manager.md"))
    buttons.accepted.connect(dlg.accept)
    buttons.rejected.connect(dlg.reject)
    main_layout.addWidget(buttons)

    # ── list helpers ──────────────────────────────────────────────────────────

    def _item_text(p: ProviderProfile) -> str:
        star = " ★" if p.id == working.default_profile_id else ""
        return f"{p.name}{star}"

    def _flush_panel() -> None:
        """Save panel state to profile and api_keys dict."""
        pid = edit_panel.current_profile_id()
        if pid:
            key = edit_panel.flush()
            api_keys[pid] = key

    def _repopulate(select_id: str = "") -> None:
        profile_list.blockSignals(True)
        profile_list.clear()
        for p in working.profiles:
            item: QListWidgetItem = QListWidgetItem(_item_text(p))
            item.setData(256, p.id)
            profile_list.addItem(item)
        target_row = 0
        if select_id:
            for i in range(profile_list.count()):
                if profile_list.item(i).data(256) == select_id:
                    target_row = i
                    break
        if profile_list.count():
            profile_list.setCurrentRow(target_row)
        profile_list.blockSignals(False)
        _on_selection_changed()

    def _on_selection_changed() -> None:
        item = profile_list.currentItem()
        if item is None:
            edit_panel.setEnabled(False)
            return
        pid = item.data(256)
        profile = working.by_id(pid)
        if profile is None:
            return
        _flush_panel()  # save previous panel before switching
        edit_panel.load(profile, api_keys.get(pid, ""))

    def _on_add() -> None:
        _flush_panel()
        p = ProviderProfile.new("New Profile")
        api_keys[p.id] = ""
        working.profiles.append(p)
        if not working.default_profile_id:
            working.default_profile_id = p.id
        _repopulate(p.id)

    def _on_delete() -> None:
        item = profile_list.currentItem()
        if item is None:
            return
        pid = item.data(256)
        working.profiles = [p for p in working.profiles if p.id != pid]
        api_keys.pop(pid, None)
        if working.default_profile_id == pid:
            working.default_profile_id = working.profiles[0].id if working.profiles else ""
        _repopulate(working.default_profile_id)

    def _on_set_default() -> None:
        item = profile_list.currentItem()
        if item is None:
            return
        working.default_profile_id = item.data(256)
        for i in range(profile_list.count()):
            it = profile_list.item(i)
            p = working.by_id(it.data(256))
            if p:
                it.setText(_item_text(p))

    profile_list.currentItemChanged.connect(lambda *_: _on_selection_changed())
    add_btn.clicked.connect(_on_add)
    del_btn.clicked.connect(_on_delete)
    default_btn.clicked.connect(_on_set_default)

    _repopulate(working.default_profile_id)

    if dlg.exec() != QDialog.DialogCode.Accepted:
        return None

    # Flush the currently-displayed panel one last time
    _flush_panel()

    # Persist all api_keys to QSettings
    working.include_api_keys = include_key_chk.isChecked()
    for p in working.profiles:
        key = api_keys.get(p.id, "")
        _save_key(p.id, key)
        p.api_key = key if working.include_api_keys else ""

    return working

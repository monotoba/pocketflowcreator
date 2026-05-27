"""SharedStoreDesignerDialog — visual editor for a shared-store YAML schema file."""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from PySide6.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QHBoxLayout,
        QLabel,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
    )
else:
    try:
        from PySide6.QtWidgets import (
            QDialog,
            QDialogButtonBox,
            QHBoxLayout,
            QLabel,
            QMainWindow,
            QMessageBox,
            QPushButton,
            QTableWidget,
            QTableWidgetItem,
            QVBoxLayout,
        )
    except ImportError:  # pragma: no cover
        QDialog = object  # type: ignore[assignment,misc]


def open_shared_store_designer(
    path: Path,
    parent: QMainWindow,
    open_help: Callable[[str], None],
    on_saved: Callable[[str], None],
) -> None:
    """Open the Shared Store Designer dialog for *path*.

    *on_saved* is called with a status-bar message string when the schema is
    successfully written.  Nothing is called on cancel or validation errors
    (caller receives a QMessageBox for errors).
    """
    raw: dict = {}
    if path.exists():
        try:
            loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                raw = loaded
        except yaml.YAMLError:
            pass

    flat: list[tuple[str, str, str, str]] = []
    for ns, keys in raw.items():
        if not isinstance(keys, dict):
            continue
        for key, props in keys.items():
            if not isinstance(props, dict):
                continue
            type_str = str(props.get("type", ""))
            default_str = str(props["default"]) if "default" in props else ""
            flat.append((str(ns), str(key), type_str, default_str))

    dlg = QDialog(parent)
    dlg.setWindowTitle(f"Shared Store Designer — {path.name}")
    dlg.resize(640, 400)
    main_layout = QVBoxLayout(dlg)

    table = QTableWidget(len(flat), 4)
    table.setHorizontalHeaderLabels(["Namespace", "Key", "Type", "Default"])
    table.horizontalHeader().setStretchLastSection(True)
    for r, (ns, key, type_str, default_str) in enumerate(flat):
        table.setItem(r, 0, QTableWidgetItem(ns))
        table.setItem(r, 1, QTableWidgetItem(key))
        table.setItem(r, 2, QTableWidgetItem(type_str))
        table.setItem(r, 3, QTableWidgetItem(default_str))
    main_layout.addWidget(table)

    btn_row = QHBoxLayout()
    add_btn = QPushButton("Add Row")
    remove_btn = QPushButton("Remove Row")
    btn_row.addWidget(add_btn)
    btn_row.addWidget(remove_btn)
    btn_row.addStretch()
    main_layout.addLayout(btn_row)

    def _add_row() -> None:
        r = table.rowCount()
        table.insertRow(r)
        for c in range(4):
            table.setItem(r, c, QTableWidgetItem(""))

    def _remove_row() -> None:
        row = table.currentRow()
        if row >= 0:
            table.removeRow(row)

    add_btn.clicked.connect(_add_row)
    remove_btn.clicked.connect(_remove_row)

    _VALID_TYPES = frozenset(
        {"string", "integer", "number", "boolean", "array", "object", "null"}
    )

    validation_label = QLabel("")
    validation_label.setWordWrap(True)
    main_layout.addWidget(validation_label)

    def _collect_schema() -> dict[str, dict[str, dict[str, object]]]:
        result: dict[str, dict[str, dict[str, object]]] = {}
        for r in range(table.rowCount()):
            ns_item = table.item(r, 0)
            key_item = table.item(r, 1)
            type_item = table.item(r, 2)
            default_item = table.item(r, 3)
            ns = ns_item.text().strip() if ns_item else ""
            key = key_item.text().strip() if key_item else ""
            type_str = type_item.text().strip() if type_item else ""
            default_str = default_item.text().strip() if default_item else ""
            if not ns or not key or not type_str:
                continue
            if ns not in result:
                result[ns] = {}
            entry: dict[str, object] = {"type": type_str}
            if default_str:
                entry["default"] = default_str
            result[ns][key] = entry
        return result

    def _validate_schema() -> list[str]:
        errors: list[str] = []
        for r in range(table.rowCount()):
            ns_item = table.item(r, 0)
            key_item = table.item(r, 1)
            type_item = table.item(r, 2)
            ns = ns_item.text().strip() if ns_item else ""
            key = key_item.text().strip() if key_item else ""
            type_str = type_item.text().strip() if type_item else ""
            if not ns and not key and not type_str:
                continue
            if not ns:
                errors.append(f"Row {r + 1}: Namespace is required.")
            if not key:
                errors.append(f"Row {r + 1}: Key is required.")
            if type_str and type_str not in _VALID_TYPES:
                errors.append(
                    f"Row {r + 1}: '{type_str}' is not a valid JSON Schema type. "
                    f"Valid types: {', '.join(sorted(_VALID_TYPES))}"
                )
        return errors

    def _on_validate() -> None:
        errs = _validate_schema()
        if errs:
            validation_label.setText("Validation errors:\n" + "\n".join(errs))
        else:
            validation_label.setText("Schema is valid.")

    validate_btn = QPushButton("Validate")
    validate_btn.clicked.connect(_on_validate)
    btn_row.addWidget(validate_btn)

    dialog_btns = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    help_btn = dialog_btns.addButton("?", QDialogButtonBox.ButtonRole.HelpRole)
    help_btn.clicked.connect(lambda: open_help("context/shared_store.md"))
    dialog_btns.accepted.connect(dlg.accept)
    dialog_btns.rejected.connect(dlg.reject)
    main_layout.addWidget(dialog_btns)

    if dlg.exec() != QDialog.DialogCode.Accepted:
        return

    errs = _validate_schema()
    if errs:
        QMessageBox.warning(parent, "Validation Errors", "\n".join(errs))
        return

    schema = _collect_schema()
    try:
        path.write_text(
            yaml.dump(schema, default_flow_style=False, allow_unicode=True),
            encoding="utf-8",
        )
        on_saved(f"Shared store schema saved: {path.name}")
    except Exception as exc:
        QMessageBox.critical(parent, "Save Failed", str(exc))

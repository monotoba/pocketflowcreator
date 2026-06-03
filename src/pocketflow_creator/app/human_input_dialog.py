"""Dialogs for the human_input_node — form and list collection modes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

try:
    from PySide6.QtWidgets import (
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QDoubleSpinBox,
        QFormLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QPushButton,
        QSpinBox,
        QVBoxLayout,
        QWidget,
    )
except ImportError:  # pragma: no cover - non-GUI environments
    QDialog = object  # type: ignore[assignment,misc]


@dataclass
class FieldDef:
    name: str
    key: str
    dtype: str
    default: str
    choices: list[str] = field(default_factory=list)


def parse_fields(fields_str: str) -> list[FieldDef]:
    """Parse 'label:type:default:choices;...' definitions into FieldDef objects.

    Uses maxsplit=3 so colons inside the choices segment are preserved.
    """
    result: list[FieldDef] = []
    for part in fields_str.split(";"):
        part = part.strip()
        if not part:
            continue
        segments = part.split(":", 3)
        name = segments[0].strip() if segments else ""
        if not name:
            continue
        dtype = segments[1].strip().lower() if len(segments) > 1 else "string"
        default = segments[2].strip() if len(segments) > 2 else ""
        choices_raw = segments[3].strip() if len(segments) > 3 else ""
        choices = [c.strip() for c in choices_raw.split(",") if c.strip()] if choices_raw else []
        key = name.lower().replace(" ", "_")
        result.append(FieldDef(name=name, key=key, dtype=dtype, default=default, choices=choices))
    return result


class FormInputDialog(QDialog):
    """Collect one or more named fields from the user."""

    def __init__(self, props: dict[str, Any], shared_store: dict[str, Any], parent: Any = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(str(props.get("title", "Human Input")))
        self.setMinimumWidth(380)
        self._field_widgets: dict[str, tuple[Any, str, list[str]]] = {}
        self._result: dict[str, object] = {}

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        fields_str = str(props.get("fields", ""))
        field_defs = parse_fields(fields_str)

        if not field_defs:
            layout.addWidget(QLabel("No fields configured.\nSet the 'fields' property in the Inspector."))
        else:
            for fd in field_defs:
                widget: QWidget
                if fd.choices:
                    cb = QComboBox()
                    cb.addItems(fd.choices)
                    if fd.default in fd.choices:
                        cb.setCurrentText(fd.default)
                    widget = cb
                elif fd.dtype == "integer":
                    sb = QSpinBox()
                    sb.setRange(-(2**31), 2**31 - 1)
                    try:
                        sb.setValue(int(fd.default))
                    except (ValueError, TypeError):
                        pass
                    widget = sb
                elif fd.dtype in ("float", "number"):
                    ds = QDoubleSpinBox()
                    ds.setRange(-1e12, 1e12)
                    ds.setDecimals(4)
                    try:
                        ds.setValue(float(fd.default))
                    except (ValueError, TypeError):
                        pass
                    widget = ds
                else:
                    le = QLineEdit()
                    le.setText(fd.default)
                    existing = str(shared_store.get(fd.key, ""))
                    if existing and not fd.default:
                        le.setPlaceholderText(existing)
                    widget = le
                form.addRow(fd.name + ":", widget)
                self._field_widgets[fd.key] = (widget, fd.dtype, fd.choices)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _accept(self) -> None:
        for key, (widget, _dtype, _choices) in self._field_widgets.items():
            if isinstance(widget, QComboBox):
                self._result[key] = widget.currentText()
            elif isinstance(widget, QSpinBox):
                self._result[key] = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                self._result[key] = widget.value()
            else:
                self._result[key] = widget.text()
        self.accept()

    @property
    def result_data(self) -> dict[str, object]:
        return self._result


class ListInputDialog(QDialog):
    """Collect a list of text items from the user."""

    def __init__(self, props: dict[str, Any], shared_store: dict[str, Any], parent: Any = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(str(props.get("title", "Human Input")))
        self.setMinimumWidth(420)
        self.setMinimumHeight(300)
        self._result: list[str] = []

        item_label = str(props.get("item_label", "item"))
        prompt_text = str(props.get("item_prompt", f"Enter {item_label}s. Add one per line."))

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(prompt_text))

        self._list = QListWidget()
        layout.addWidget(self._list)

        entry_row = QHBoxLayout()
        self._entry = QLineEdit()
        self._entry.setPlaceholderText(f"New {item_label}…")
        self._entry.returnPressed.connect(self._add_item)
        entry_row.addWidget(self._entry)

        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self._add_item)
        entry_row.addWidget(add_btn)

        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self._remove_selected)
        entry_row.addWidget(remove_btn)
        layout.addLayout(entry_row)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        done_btn = buttons.addButton("Done", QDialogButtonBox.ButtonRole.AcceptRole)
        done_btn.clicked.connect(self._accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _add_item(self) -> None:
        text = self._entry.text().strip()
        if text:
            self._list.addItem(text)
            self._entry.clear()

    def _remove_selected(self) -> None:
        for item in self._list.selectedItems():
            self._list.takeItem(self._list.row(item))

    def _accept(self) -> None:
        self._result = [self._list.item(i).text() for i in range(self._list.count())]
        self.accept()

    @property
    def result_data(self) -> list[str]:
        return self._result


def create_human_input_dialog(
    input_type: str,
    props: dict[str, Any],
    shared_store: dict[str, Any],
    parent: Any = None,
) -> QDialog:
    """Return the appropriate dialog for the given input_type."""
    if input_type == "list":
        return ListInputDialog(props, shared_store, parent)
    return FormInputDialog(props, shared_store, parent)

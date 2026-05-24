from __future__ import annotations

from typing import Any

try:
    from PySide6.QtWidgets import (
        QCheckBox,
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QListWidget,
        QMessageBox,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QVBoxLayout,
        QWidget,
    )
except Exception:  # pragma: no cover
    QDialog = object  # type: ignore[assignment,misc]

from pocketflow_creator.model.node_type import NodeTypeDefinition  # noqa: I001


_CATEGORIES = ["LLM", "Control", "IO", "Data", "Custom"]
_BASE_CLASSES = ["Node", "BatchNode", "AsyncNode", "llm_prompt_node", "file_reader_node"]


class NodeTypeWizard(QDialog):
    """Dialog for defining a new custom node type."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("New Custom Node Type")
        self.resize(560, 560)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        basic = QGroupBox("Identity")
        form = QFormLayout(basic)
        self._id_edit = QLineEdit()
        self._id_edit.setPlaceholderText("e.g. my_llm_node")
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g. My LLM Node")
        self._category_edit = QLineEdit()
        self._category_edit.setPlaceholderText(f"e.g. {_CATEGORIES[0]}")
        self._base_edit = QLineEdit()
        self._base_edit.setPlaceholderText(f"e.g. {_BASE_CLASSES[0]}")
        self._desc_edit = QLineEdit()
        form.addRow("Node Type ID *:", self._id_edit)
        form.addRow("Display Name *:", self._name_edit)
        form.addRow("Category *:", self._category_edit)
        form.addRow("Base Class *:", self._base_edit)
        form.addRow("Description:", self._desc_edit)
        layout.addWidget(basic)

        actions_group = QGroupBox("Actions")
        alay = QVBoxLayout(actions_group)
        self._actions_list = QListWidget()
        self._actions_list.addItems(["default"])
        alay.addWidget(self._actions_list)
        a_row = QHBoxLayout()
        self._action_edit = QLineEdit()
        self._action_edit.setPlaceholderText("action name")
        add_a = QPushButton("Add")
        del_a = QPushButton("Remove")
        add_a.clicked.connect(self._add_action)
        del_a.clicked.connect(self._remove_action)
        a_row.addWidget(self._action_edit)
        a_row.addWidget(add_a)
        a_row.addWidget(del_a)
        alay.addLayout(a_row)
        layout.addWidget(actions_group)

        props_group = QGroupBox("Properties")
        play = QVBoxLayout(props_group)
        self._props_table = QTableWidget(0, 3)
        self._props_table.setHorizontalHeaderLabels(["Name", "Type", "Default"])
        self._props_table.horizontalHeader().setStretchLastSection(True)
        play.addWidget(self._props_table)
        p_row = QHBoxLayout()
        add_p = QPushButton("Add Row")
        del_p = QPushButton("Remove Row")
        add_p.clicked.connect(self._add_prop_row)
        del_p.clicked.connect(self._remove_prop_row)
        p_row.addWidget(add_p)
        p_row.addWidget(del_p)
        p_row.addStretch()
        play.addLayout(p_row)
        layout.addWidget(props_group)

        flags_group = QGroupBox("Flags")
        flay = QHBoxLayout(flags_group)
        self._hooks_cb = QCheckBox("Allow Python Hooks")
        self._prompts_cb = QCheckBox("Allow Prompt Files")
        flay.addWidget(self._hooks_cb)
        flay.addWidget(self._prompts_cb)
        layout.addWidget(flags_group)

        layout.addWidget(QLabel("* Required fields"))

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        help_btn = buttons.addButton("?", QDialogButtonBox.ButtonRole.HelpRole)
        help_btn.clicked.connect(self._on_help)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _add_action(self) -> None:
        name = self._action_edit.text().strip()
        if name:
            self._actions_list.addItem(name)
            self._action_edit.clear()

    def _remove_action(self) -> None:
        row = self._actions_list.currentRow()
        if row >= 0:
            self._actions_list.takeItem(row)

    def _add_prop_row(self) -> None:
        r = self._props_table.rowCount()
        self._props_table.insertRow(r)
        for c in range(3):
            self._props_table.setItem(r, c, QTableWidgetItem(""))

    def _remove_prop_row(self) -> None:
        row = self._props_table.currentRow()
        if row >= 0:
            self._props_table.removeRow(row)

    def _on_help(self) -> None:
        from pocketflow_creator.app.help_browser import open_help

        open_help("context/node_type_wizard.md", self)

    def _on_accept(self) -> None:
        defn = self._collect()
        try:
            NodeTypeDefinition.from_mapping(defn)
        except ValueError as exc:
            QMessageBox.warning(self, "Validation Error", str(exc))
            return
        self.accept()

    def _collect(self) -> dict[str, Any]:
        actions = [
            self._actions_list.item(i).text()
            for i in range(self._actions_list.count())
        ]
        props: dict[str, dict[str, str]] = {}
        for r in range(self._props_table.rowCount()):
            name_item = self._props_table.item(r, 0)
            type_item = self._props_table.item(r, 1)
            default_item = self._props_table.item(r, 2)
            name = name_item.text().strip() if name_item else ""
            type_str = type_item.text().strip() if type_item else "string"
            default_str = default_item.text().strip() if default_item else ""
            if name:
                entry: dict[str, str] = {"type": type_str or "string"}
                if default_str:
                    entry["default"] = default_str
                props[name] = entry
        return {
            "node_type_id": self._id_edit.text().strip(),
            "display_name": self._name_edit.text().strip(),
            "category": self._category_edit.text().strip(),
            "base_class": self._base_edit.text().strip(),
            "description": self._desc_edit.text().strip(),
            "actions": actions,
            "properties": props,
            "allow_python_hooks": self._hooks_cb.isChecked(),
            "allow_prompt_files": self._prompts_cb.isChecked(),
        }

    def result_definition(self) -> dict[str, Any]:
        return self._collect()

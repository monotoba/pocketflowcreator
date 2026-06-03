"""PaletteWidget — the drag-source list widget for node types and snippets."""
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from PySide6.QtCore import QMimeData, QSize, Qt
    from PySide6.QtGui import QDrag
    from PySide6.QtWidgets import (
        QAbstractItemView,
        QListWidget,
        QListWidgetItem,
        QWidget,
    )
else:
    try:
        from PySide6.QtCore import QMimeData, QSize, Qt
        from PySide6.QtGui import QDrag
        from PySide6.QtWidgets import (
            QAbstractItemView,
            QListWidget,
            QListWidgetItem,
            QWidget,
        )
    except ImportError:  # pragma: no cover
        QListWidget = object

from pocketflow_creator.app.canvas.icons import make_node_icon
from pocketflow_creator.builtin_node_types import get_nodes_by_category
from pocketflow_creator.node_package_loader import get_addon_node_groups, get_user_node_groups

_MIME_NODE_TYPE = "application/x-pocketflow-node-type"
_MIME_NODE_SNIPPET = "application/x-pocketflow-node-snippet"
_ROLE_SNIPPET = Qt.ItemDataRole(Qt.ItemDataRole.UserRole.value + 1)  # type: ignore[attr-defined]


def _load_snippets() -> list[dict[str, Any]]:
    snippets_path = Path(__file__).parent.parent.parent / "node_snippets.yaml"
    if not snippets_path.exists():
        return []
    try:
        import yaml

        data = yaml.safe_load(snippets_path.read_text(encoding="utf-8")) or {}
        return list(data.get("snippets", []))
    except Exception:
        return []


def _make_category_header(label: str) -> QListWidgetItem:
    """Return a non-interactive category-header item."""
    item = QListWidgetItem(f"  {label}")
    item.setFlags(
        item.flags()
        & ~Qt.ItemFlag.ItemIsEnabled  # type: ignore[attr-defined]
        & ~Qt.ItemFlag.ItemIsSelectable  # type: ignore[attr-defined]
    )
    font = item.font()
    font.setBold(True)
    font.setPointSizeF(font.pointSizeF() * 0.85)
    item.setFont(font)
    return item


class PaletteWidget(QListWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)
        self.setIconSize(QSize(28, 28))

        for category, nodes in get_nodes_by_category():
            self.addItem(_make_category_header(category))
            for type_id, nt in nodes:
                item = QListWidgetItem(make_node_icon(type_id, 28), nt.display_name)
                item.setData(Qt.ItemDataRole.UserRole, type_id)
                self.addItem(item)

        # Add-on scientific & engineering node packages
        addon_groups = get_addon_node_groups()
        if addon_groups:
            addon_div = QListWidgetItem("─── Scientific & Engineering ───")
            addon_div.setFlags(
                addon_div.flags()
                & ~Qt.ItemFlag.ItemIsEnabled  # type: ignore[attr-defined]
                & ~Qt.ItemFlag.ItemIsSelectable  # type: ignore[attr-defined]
            )
            self.addItem(addon_div)
            for category, nodes in addon_groups:
                self.addItem(_make_category_header(category))
                for type_id, nt in nodes:
                    item = QListWidgetItem(make_node_icon(type_id, 28), nt.display_name)
                    item.setData(Qt.ItemDataRole.UserRole, type_id)
                    self.addItem(item)

        # User-installed node packages — grouped by category, separated from built-ins
        user_groups = get_user_node_groups()
        if user_groups:
            divider = QListWidgetItem("─── Custom Nodes ───")
            divider.setFlags(
                divider.flags()
                & ~Qt.ItemFlag.ItemIsEnabled  # type: ignore[attr-defined]
                & ~Qt.ItemFlag.ItemIsSelectable  # type: ignore[attr-defined]
            )
            self.addItem(divider)
            for category, nodes in user_groups:
                self.addItem(_make_category_header(category))
                for type_id, nt in nodes:
                    item = QListWidgetItem(make_node_icon(type_id, 28), nt.display_name)
                    item.setData(Qt.ItemDataRole.UserRole, type_id)
                    self.addItem(item)

        snippets = _load_snippets()
        if snippets:
            sep = QListWidgetItem("— Snippets —")
            sep.setFlags(sep.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            self.addItem(sep)
            for snippet in snippets:
                sitem = QListWidgetItem(str(snippet.get("display_name", snippet.get("type_id"))))
                sitem.setData(Qt.ItemDataRole.UserRole, snippet.get("type_id", "basic_node"))
                sitem.setData(_ROLE_SNIPPET, snippet)
                self.addItem(sitem)

    def startDrag(self, supported_actions: Any) -> None:
        current = self.currentItem()
        if current is None:
            return
        snippet: dict[str, Any] | None = current.data(_ROLE_SNIPPET)
        mime = QMimeData()
        if snippet is not None:
            mime.setData(_MIME_NODE_SNIPPET, json.dumps(snippet).encode())
        else:
            type_id: str = current.data(Qt.ItemDataRole.UserRole)
            mime.setData(_MIME_NODE_TYPE, type_id.encode())
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.CopyAction)

"""CustomizeToolbarDialog — lets the user re-order node-palette toolbar icons.

Each row shows the node display name together with its palette icon.
Up / Down buttons move the selected row.  Reset Default restores the
insertion order defined in BUILTIN_NODE_TYPES.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtCore import QSize, Qt
    from PySide6.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )
else:
    try:
        from PySide6.QtCore import QSize, Qt
        from PySide6.QtWidgets import (
            QDialog,
            QDialogButtonBox,
            QHBoxLayout,
            QLabel,
            QListWidget,
            QListWidgetItem,
            QPushButton,
            QVBoxLayout,
            QWidget,
        )
    except ImportError:  # pragma: no cover
        QDialog = object  # type: ignore[assignment,misc]
        QWidget = object  # type: ignore[assignment,misc]

from pocketflow_creator.app.canvas import make_node_icon


class CustomizeToolbarDialog(QDialog):
    """Modal dialog for re-ordering the node-palette toolbar.

    Parameters
    ----------
    current_order:
        Sequence of ``type_id`` strings in the order currently shown on the
        toolbar.  The dialog initialises its list from this sequence.
    display_names:
        Mapping from ``type_id`` to human-readable display name.
    default_order:
        Sequence of ``type_id`` strings representing the default order
        (used by the *Reset Default* button).
    parent:
        Optional Qt parent widget.
    """

    def __init__(
        self,
        current_order: list[str],
        display_names: dict[str, str],
        default_order: list[str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._display_names = display_names
        self._default_order = list(default_order)

        self.setWindowTitle(self.tr("Customize Toolbar"))
        self.setMinimumWidth(340)
        self.setModal(True)

        # ── List ──────────────────────────────────────────────────────────────
        self._list = QListWidget()
        self._list.setIconSize(QSize(24, 24))
        self._list.setDragDropMode(QListWidget.DragDropMode.NoDragDrop)
        self._populate(current_order)
        self._list.currentRowChanged.connect(self._update_buttons)

        # ── Up / Down / Reset ─────────────────────────────────────────────────
        self._btn_up = QPushButton(self.tr("↑  Up"))
        self._btn_down = QPushButton(self.tr("↓  Down"))
        self._btn_reset = QPushButton(self.tr("Reset Default"))
        self._btn_up.clicked.connect(self._move_up)
        self._btn_down.clicked.connect(self._move_down)
        self._btn_reset.clicked.connect(self._reset_default)

        side_layout = QVBoxLayout()
        side_layout.addWidget(self._btn_up)
        side_layout.addWidget(self._btn_down)
        side_layout.addSpacing(12)
        side_layout.addWidget(self._btn_reset)
        side_layout.addStretch()

        body_layout = QHBoxLayout()
        body_layout.addWidget(self._list, stretch=1)
        body_layout.addLayout(side_layout)

        # ── OK / Cancel ───────────────────────────────────────────────────────
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        hint = QLabel(self.tr("Select an item and use ↑ / ↓ to reorder."))
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        root = QVBoxLayout(self)
        root.addWidget(hint)
        root.addLayout(body_layout)
        root.addWidget(buttons)

        self._update_buttons()

    # ── helpers ───────────────────────────────────────────────────────────────

    def _populate(self, order: list[str]) -> None:
        self._list.clear()
        for type_id in order:
            name = self._display_names.get(type_id, type_id)
            item = QListWidgetItem(make_node_icon(type_id, 24), name)
            item.setData(Qt.ItemDataRole.UserRole, type_id)
            self._list.addItem(item)
        if self._list.count():
            self._list.setCurrentRow(0)

    def _update_buttons(self) -> None:
        row = self._list.currentRow()
        count = self._list.count()
        self._btn_up.setEnabled(row > 0)
        self._btn_down.setEnabled(0 <= row < count - 1)

    # ── slots ─────────────────────────────────────────────────────────────────

    def _move_up(self) -> None:
        row = self._list.currentRow()
        if row <= 0:
            return
        item = self._list.takeItem(row)
        self._list.insertItem(row - 1, item)
        self._list.setCurrentRow(row - 1)

    def _move_down(self) -> None:
        row = self._list.currentRow()
        if row < 0 or row >= self._list.count() - 1:
            return
        item = self._list.takeItem(row)
        self._list.insertItem(row + 1, item)
        self._list.setCurrentRow(row + 1)

    def _reset_default(self) -> None:
        self._populate(self._default_order)

    # ── result ────────────────────────────────────────────────────────────────

    def ordered_type_ids(self) -> list[str]:
        """Return the ``type_id`` list in the order the user set."""
        return [
            self._list.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(self._list.count())
        ]

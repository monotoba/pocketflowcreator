"""AutoArrangeDialog — settings dialog shown before running Auto Arrange."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import (
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QMainWindow,
        QSpinBox,
        QVBoxLayout,
    )
else:
    try:
        from PySide6.QtWidgets import (
            QComboBox,
            QDialog,
            QDialogButtonBox,
            QFormLayout,
            QMainWindow,
            QSpinBox,
            QVBoxLayout,
        )
    except ImportError:  # pragma: no cover
        QDialog = object  # type: ignore[assignment,misc]


class AutoArrangeDialog(QDialog):
    """Settings dialog shown before running Auto Arrange."""

    _ALGORITHMS = [
        ("Layered (BFS)", "layered"),
        ("Grid", "grid"),
        ("Force-Directed", "force"),
    ]
    _STYLES = [
        ("Straight", "straight"),
        ("Curved (Bezier)", "curved"),
        ("Orthogonal", "orthogonal"),
    ]

    def __init__(self, settings: dict, parent: QMainWindow | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Auto Arrange")
        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        self._algo_combo = QComboBox()
        for label, _ in self._ALGORITHMS:
            self._algo_combo.addItem(label)
        current_algo = settings.get("algorithm", "layered")
        idx = next((i for i, (_, v) in enumerate(self._ALGORITHMS) if v == current_algo), 0)
        self._algo_combo.setCurrentIndex(idx)
        form.addRow("Algorithm:", self._algo_combo)

        self._style_combo = QComboBox()
        for label, _ in self._STYLES:
            self._style_combo.addItem(label)
        current_style = settings.get("connector_style", "straight")
        sidx = next((i for i, (_, v) in enumerate(self._STYLES) if v == current_style), 0)
        self._style_combo.setCurrentIndex(sidx)
        form.addRow("Connector Style:", self._style_combo)

        self._h_gap = QSpinBox()
        self._h_gap.setRange(10, 400)
        self._h_gap.setValue(int(settings.get("h_gap", 60)))
        form.addRow("Horizontal Gap:", self._h_gap)

        self._v_gap = QSpinBox()
        self._v_gap.setRange(10, 400)
        self._v_gap.setValue(int(settings.get("v_gap", 30)))
        form.addRow("Vertical Gap:", self._v_gap)

        self._max_cols = QSpinBox()
        self._max_cols.setRange(1, 20)
        self._max_cols.setValue(int(settings.get("max_cols", 4)))
        form.addRow("Max Columns (Grid):", self._max_cols)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_settings(self) -> dict:
        return {
            "algorithm": self._ALGORITHMS[self._algo_combo.currentIndex()][1],
            "connector_style": self._STYLES[self._style_combo.currentIndex()][1],
            "h_gap": self._h_gap.value(),
            "v_gap": self._v_gap.value(),
            "max_cols": self._max_cols.value(),
        }

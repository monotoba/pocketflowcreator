"""NodeItem and EdgeItem — the graphical representations of nodes and edges.

GraphScene is referenced inside method bodies only (lazy import) to break the
circular dependency:  items → scene → items.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from PySide6.QtCore import QPointF, QRectF, Qt
    from PySide6.QtGui import (
        QBrush,
        QColor,
        QFont,
        QKeySequence,
        QPainter,
        QPainterPath,
        QPainterPathStroker,
        QPen,
        QPolygonF,
    )
    from PySide6.QtWidgets import (
        QGraphicsItem,
        QGraphicsPathItem,
        QMenu,
        QStyleOptionGraphicsItem,
        QWidget,
    )
else:
    try:
        from PySide6.QtCore import QPointF, QRectF, Qt
        from PySide6.QtGui import (
            QBrush,
            QColor,
            QFont,
            QKeySequence,
            QPainter,
            QPainterPath,
            QPainterPathStroker,
            QPen,
            QPolygonF,
        )
        from PySide6.QtWidgets import (
            QGraphicsItem,
            QGraphicsPathItem,
            QMenu,
            QStyleOptionGraphicsItem,
            QWidget,
        )
    except ImportError:  # pragma: no cover
        QGraphicsItem = object
        QGraphicsPathItem = object

from pocketflow_creator.model.graph_model import EdgeModel, NodeModel

# ── Node geometry constants ───────────────────────────────────────────────────
_WIDTH = 160
_HEIGHT = 60  # minimum / single-action node height (kept for layout spacing)
_HEADER_H = 36  # title (18 px) + type badge (13 px) + 5 px gap before action rows
_PORT_ROW_H = 18  # height allocated per action row
_PORT_R = 5


def _node_height(n_actions: int) -> int:
    """Dynamic node height: grows with action count; single-action stays at _HEIGHT."""
    return max(_HEIGHT, _HEADER_H + max(1, n_actions) * _PORT_ROW_H)


# ── Theme colour palettes ─────────────────────────────────────────────────────
_DARK_COLORS = {
    "node_bg": "#2a2a2a",
    "border_error": "#e05555",
    "border_select": "#4a9eff",
    "border_normal": "#555555",
    "title": "#ffffff",
    "badge": "#aaaaaa",
    "port_outline": "#888888",
    "port_fill": "#555555",
    "breakpoint": "#e05555",
    "edge": "#888888",
}

_LIGHT_COLORS = {
    "node_bg": "#f5f5f5",
    "border_error": "#cc3333",
    "border_select": "#0077cc",
    "border_normal": "#999999",
    "title": "#111111",
    "badge": "#555555",
    "port_outline": "#555555",
    "port_fill": "#888888",
    "breakpoint": "#cc3333",
    "edge": "#555555",
}


class NodeItem(QGraphicsItem):
    def __init__(self, node: NodeModel, parent: QGraphicsItem | None = None) -> None:
        super().__init__(parent)
        self._node = node
        self._has_error = False
        self._has_breakpoint = False
        self._is_start = False
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setPos(node.position["x"], node.position["y"])
        self.setToolTip(node.id)

    @property
    def node(self) -> NodeModel:
        return self._node

    def set_has_error(self, has_error: bool) -> None:
        self._has_error = has_error
        self.update()

    def set_breakpoint(self, active: bool) -> None:
        self._has_breakpoint = active
        self.update()

    def set_is_start(self, active: bool) -> None:
        self._is_start = active
        self.update()

    def boundingRect(self) -> QRectF:
        h = _node_height(len(self._node.actions or []))
        return QRectF(-_PORT_R, 0, _WIDTH + 2 * _PORT_R, h)

    @property
    def height(self) -> int:
        return _node_height(len(self._node.actions or []))

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        scene = self.scene()
        from pocketflow_creator.app.canvas.scene import GraphScene  # lazy – avoids circular import

        dark = scene.is_dark if isinstance(scene, GraphScene) else True
        colors = _DARK_COLORS if dark else _LIGHT_COLORS

        actions = self._node.actions or ["default"]
        h = _node_height(len(actions))

        body = QRectF(0, 0, _WIDTH, h)
        path = QPainterPath()
        path.addRoundedRect(body, 8, 8)
        painter.fillPath(path, QBrush(QColor(colors["node_bg"])))

        if self._has_error:
            border_pen = QPen(QColor(colors["border_error"]), 2)
        elif self.isSelected():
            border_pen = QPen(QColor(colors["border_select"]), 2)
        else:
            border_pen = QPen(QColor(colors["border_normal"]), 1)
        painter.setPen(border_pen)
        painter.drawPath(path)

        # ── Header: title (top-aligned) + type badge ────────────────────────
        base_font = painter.font()
        title_font = QFont(base_font)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(QPen(QColor(colors["title"])))
        painter.drawText(QRectF(12, 4, _WIDTH - 24, 18), Qt.AlignmentFlag.AlignVCenter, self._node.title)

        badge_font = QFont(base_font)
        badge_font.setPointSize(max(base_font.pointSize() - 1, 7))
        painter.setFont(badge_font)
        painter.setPen(QPen(QColor(colors["badge"])))
        painter.drawText(QRectF(12, 21, _WIDTH - 24, 13), Qt.AlignmentFlag.AlignVCenter, self._node.type_id)

        # Separator between header and action area (only for multi-action nodes)
        if len(actions) > 1:
            sep_pen = QPen(QColor(colors["border_normal"]), 1)
            sep_pen.setStyle(Qt.PenStyle.SolidLine)
            painter.setPen(sep_pen)
            painter.drawLine(QPointF(6, _HEADER_H), QPointF(_WIDTH - 6, _HEADER_H))

        # ── Input port (left side, vertically centred on the node) ──────────
        painter.setPen(QPen(QColor(colors["port_outline"]), 1))
        painter.setBrush(QBrush(QColor(colors["port_fill"])))
        painter.drawEllipse(QPointF(0, h / 2), _PORT_R, _PORT_R)

        # ── Action ports (right side, one row per action below the header) ──
        port_font = QFont(base_font)
        port_font.setPointSize(max(base_font.pointSize() - 2, 6))

        # Input port label — show input_key property (fallback "in")
        in_label = str(self._node.properties.get("input_key", "")).strip() or "in"
        painter.setFont(port_font)
        painter.setPen(QPen(QColor(colors["badge"])))
        painter.drawText(
            QRectF(_PORT_R + 4, h / 2 + _PORT_R, _WIDTH // 2 - 8, 14),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            in_label,
        )
        for action, y in self._action_port_ys(actions):
            painter.setPen(QPen(QColor(colors["port_outline"]), 1))
            painter.setBrush(QBrush(QColor(colors["port_fill"])))
            painter.drawEllipse(QPointF(_WIDTH, y), _PORT_R, _PORT_R)
            # Label: right-aligned inside the action row, clear of the port circle
            painter.setPen(QPen(QColor(colors["badge"])))
            painter.drawText(
                QRectF(8, y - 7, _WIDTH - 16, 14),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                action,
            )

        # ── Decorators ───────────────────────────────────────────────────────
        if self._has_breakpoint:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(colors["breakpoint"])))
            painter.drawEllipse(QPointF(_WIDTH - 10, 10), 5, 5)

        if self._is_start:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#44bb44")))
            triangle = QPolygonF(
                [
                    QPointF(8, h / 2 - 6),
                    QPointF(8, h / 2 + 6),
                    QPointF(18, h / 2),
                ]
            )
            painter.drawPolygon(triangle)

        if self._node.type_id == "stop_node":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#dd4444")))
            sq = 10
            painter.drawRect(int(_WIDTH - 8 - sq), int(h / 2 - sq / 2), sq, sq)

    @staticmethod
    def _action_port_ys(actions: list[str]) -> list[tuple[str, float]]:
        """Return [(action_name, local_y), …] placed in the action area below the header."""
        if not actions:
            actions = ["default"]
        n = len(actions)
        h = _node_height(n)
        row_h = (h - _HEADER_H) / n
        return [(actions[i], _HEADER_H + i * row_h + row_h / 2) for i in range(n)]

    def action_port_scene_pos(self, action: str) -> QPointF:
        """Return the scene position of the port for *action*."""
        actions = self._node.actions or ["default"]
        for a, y in self._action_port_ys(actions):
            if a == action:
                return self.mapToScene(QPointF(_WIDTH, y))
        # Fallback: first action port
        _, y = self._action_port_ys(actions)[0]
        return self.mapToScene(QPointF(_WIDTH, y))

    def port_scene_pos(self) -> QPointF:
        """First action port position (backward-compat for single-action nodes)."""
        actions = self._node.actions or ["default"]
        _, y = self._action_port_ys(actions)[0]
        return self.mapToScene(QPointF(_WIDTH, y))

    def input_port_scene_pos(self) -> QPointF:
        return self.mapToScene(QPointF(0, self.height / 2))

    def mouseDoubleClickEvent(self, event: Any) -> None:
        from pocketflow_creator.app.canvas.scene import GraphScene  # lazy – avoids circular import

        scene = self.scene()
        if isinstance(scene, GraphScene):
            scene.node_item_double_clicked.emit(self)
        event.accept()

    def contextMenuEvent(self, event: Any) -> None:
        from pocketflow_creator.app.canvas.scene import GraphScene  # lazy – avoids circular import

        scene = self.scene()
        if not isinstance(scene, GraphScene):
            return
        menu = QMenu()

        # ── Start node designation ────────────────────────────────────────────
        start_text = "Set as Start Node" if not self._is_start else "Already Start Node"
        act_start = menu.addAction(start_text)
        if self._is_start:
            act_start.setEnabled(False)

        menu.addSeparator()

        # ── Per-node operations ───────────────────────────────────────────────
        act_open = menu.addAction("Open Code")
        act_rename = menu.addAction("Rename")
        act_bp = menu.addAction("Toggle Breakpoint")
        act_bp.setShortcut(QKeySequence("F9"))

        menu.addSeparator()

        # ── Structural operations ─────────────────────────────────────────────
        act_dup = menu.addAction("Duplicate")
        act_del = menu.addAction("Delete")
        act_del.setShortcut(QKeySequence("Delete"))

        chosen = menu.exec(event.screenPos())

        if chosen is act_start and not self._is_start:
            scene.set_start_node_requested.emit(self)
        elif chosen is act_open:
            scene.node_open_code_requested.emit(self)
        elif chosen is act_rename:
            scene.node_rename_requested.emit(self)
        elif chosen is act_bp:
            scene.node_toggle_breakpoint_requested.emit(self)
        elif chosen is act_dup:
            scene.node_duplicate_requested.emit(self)
        elif chosen is act_del:
            scene.node_delete_requested.emit(self)

        event.accept()

    def mousePressEvent(self, event: Any) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = self.pos()  # type: ignore[assignment]
            from pocketflow_creator.app.canvas.scene import GraphScene  # lazy – avoids circular import

            scene = self.scene()
            if isinstance(scene, GraphScene):
                scene.node_drag_started.emit(self._node.id)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: Any) -> None:
        super().mouseReleaseEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            start = getattr(self, "_drag_start_pos", None)
            if start is not None and start != self.pos():
                from pocketflow_creator.app.canvas.scene import GraphScene  # lazy – avoids circular import

                scene = self.scene()
                if isinstance(scene, GraphScene):
                    scene.node_move_finished.emit(self._node.id)
            self._drag_start_pos = None

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            p = self.pos()
            self.node.position["x"] = p.x()
            self.node.position["y"] = p.y()
            from pocketflow_creator.app.canvas.scene import GraphScene  # lazy – avoids circular import

            scene = self.scene()
            if isinstance(scene, GraphScene):
                scene.update_edges()
        return super().itemChange(change, value)


class EdgeItem(QGraphicsPathItem):
    def __init__(
        self,
        edge: EdgeModel,
        src: NodeItem,
        tgt: NodeItem,
        parent: QGraphicsItem | None = None,
    ) -> None:
        super().__init__(parent)
        self._edge = edge
        self._src = src
        self._tgt = tgt
        self.setPen(QPen(QColor("#888888"), 1.5))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.update_position()

    @property
    def edge(self) -> EdgeModel:
        return self._edge

    def shape(self) -> QPainterPath:
        stroker = QPainterPathStroker()
        stroker.setWidth(12.0)
        return stroker.createStroke(self.path())

    def update_position(self, connector_style: str = "straight") -> None:
        src_pos = self._src.action_port_scene_pos(self._edge.action)
        tgt_pos = self._tgt.input_port_scene_pos()
        path = QPainterPath()
        path.moveTo(src_pos)
        if connector_style == "curved":
            mid_x = (src_pos.x() + tgt_pos.x()) / 2
            path.quadTo(QPointF(mid_x, src_pos.y()), tgt_pos)
        elif connector_style == "orthogonal":
            mid_x = (src_pos.x() + tgt_pos.x()) / 2
            path.lineTo(QPointF(mid_x, src_pos.y()))
            path.lineTo(QPointF(mid_x, tgt_pos.y()))
            path.lineTo(tgt_pos)
        else:
            path.lineTo(tgt_pos)
        self.setPath(path)

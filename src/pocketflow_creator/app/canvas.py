from __future__ import annotations

import uuid
from typing import Any

try:
    from PySide6.QtCore import QMimeData, QPointF, QRectF, Qt, Signal
    from PySide6.QtGui import (
        QBrush,
        QColor,
        QDrag,
        QFont,
        QPainter,
        QPainterPath,
        QPen,
    )
    from PySide6.QtWidgets import (
        QAbstractItemView,
        QGraphicsItem,
        QGraphicsLineItem,
        QGraphicsScene,
        QGraphicsView,
        QListWidget,
        QListWidgetItem,
        QStyleOptionGraphicsItem,
        QWidget,
    )
except Exception:  # pragma: no cover - permits import in non-GUI test environments
    def Signal(*a: Any, **kw: Any) -> Any:  # type: ignore[misc,no-redef]
        return None

    QGraphicsItem = object  # type: ignore[assignment,misc]
    QGraphicsLineItem = object  # type: ignore[assignment,misc]
    QGraphicsScene = object  # type: ignore[assignment,misc]
    QGraphicsView = object  # type: ignore[assignment,misc]
    QListWidget = object  # type: ignore[assignment,misc]

from pocketflow_creator.model.graph_model import EdgeModel, GraphModel, NodeModel

_MIME_NODE_TYPE = "application/x-pocketflow-node-type"
_WIDTH = 160
_HEIGHT = 60
_PORT_R = 5

_PALETTE_ITEMS: list[tuple[str, str]] = [
    ("Start Node", "start_node"),
    ("Stop Node", "stop_node"),
    ("Basic Node", "basic_node"),
    ("Router Node", "router_node"),
    ("LLM Prompt Node", "llm_prompt_node"),
    ("JSON LLM Node", "json_llm_node"),
    ("Classifier Node", "classifier_node"),
    ("Python Tool Node", "python_tool_node"),
    ("File Reader Node", "file_reader_node"),
    ("Human Review Node", "human_review_node"),
    ("Batch Node", "batch_node"),
    ("Subflow Node", "subflow_node"),
]


class NodeItem(QGraphicsItem):
    def __init__(self, node: NodeModel, parent: QGraphicsItem | None = None) -> None:
        super().__init__(parent)
        self._node = node
        self._has_error = False
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

    def boundingRect(self) -> QRectF:
        return QRectF(-_PORT_R, 0, _WIDTH + 2 * _PORT_R, _HEIGHT)

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        body = QRectF(0, 0, _WIDTH, _HEIGHT)
        path = QPainterPath()
        path.addRoundedRect(body, 8, 8)

        painter.fillPath(path, QBrush(QColor("#2a2a2a")))

        if self._has_error:
            border_pen = QPen(QColor("#e05555"), 2)
        elif self.isSelected():
            border_pen = QPen(QColor("#4a9eff"), 2)
        else:
            border_pen = QPen(QColor("#555555"), 1)
        painter.setPen(border_pen)
        painter.drawPath(path)

        base_font = painter.font()
        title_font = QFont(base_font)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(QPen(QColor("#ffffff")))
        painter.drawText(
            QRectF(12, 8, _WIDTH - 24, 22), Qt.AlignmentFlag.AlignVCenter, self._node.title
        )

        badge_font = QFont(base_font)
        badge_font.setPointSize(max(base_font.pointSize() - 1, 7))
        painter.setFont(badge_font)
        painter.setPen(QPen(QColor("#aaaaaa")))
        painter.drawText(
            QRectF(12, 30, _WIDTH - 24, 18), Qt.AlignmentFlag.AlignVCenter, self._node.type_id
        )

        painter.setPen(QPen(QColor("#888888"), 1))
        painter.setBrush(QBrush(QColor("#555555")))
        painter.drawEllipse(QPointF(0, _HEIGHT / 2), _PORT_R, _PORT_R)
        painter.drawEllipse(QPointF(_WIDTH, _HEIGHT / 2), _PORT_R, _PORT_R)

    def port_scene_pos(self) -> QPointF:
        return self.mapToScene(QPointF(_WIDTH, _HEIGHT / 2))

    def input_port_scene_pos(self) -> QPointF:
        return self.mapToScene(QPointF(0, _HEIGHT / 2))

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            scene = self.scene()
            if isinstance(scene, GraphScene):
                scene.update_edges()
        return super().itemChange(change, value)


class EdgeItem(QGraphicsLineItem):
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

    def update_position(self) -> None:
        src_pos = self._src.port_scene_pos()
        tgt_pos = self._tgt.input_port_scene_pos()
        self.setLine(src_pos.x(), src_pos.y(), tgt_pos.x(), tgt_pos.y())


class GraphScene(QGraphicsScene):
    node_item_selected = Signal(object)
    edge_item_selected = Signal(object)
    selection_cleared = Signal()

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self._node_items: dict[str, NodeItem] = {}
        self._edge_items: list[EdgeItem] = []
        self.selectionChanged.connect(self._on_selection_changed)

    def load_graph(self, graph: GraphModel) -> None:
        self.clear()
        self._node_items = {}
        self._edge_items = []
        for node in graph.nodes:
            item = NodeItem(node)
            self.addItem(item)
            self._node_items[node.id] = item
        for edge in graph.edges:
            src = self._node_items.get(edge.from_node)
            tgt = self._node_items.get(edge.to_node)
            if src and tgt:
                ei = EdgeItem(edge, src, tgt)
                self.addItem(ei)
                self._edge_items.append(ei)

    def create_node_at(self, type_id: str, pos: QPointF) -> NodeItem:
        node = NodeModel(
            id=f"node_{uuid.uuid4().hex[:8]}",
            type_id=type_id,
            title=type_id.replace("_", " ").title(),
            position={"x": pos.x(), "y": pos.y()},
        )
        item = NodeItem(node)
        self.addItem(item)
        self._node_items[node.id] = item
        return item

    def update_edges(self) -> None:
        for ei in self._edge_items:
            ei.update_position()

    def apply_validation(self, error_ids: set[str]) -> None:
        for node_id, item in self._node_items.items():
            item.set_has_error(node_id in error_ids)

    def _on_selection_changed(self) -> None:
        selected = self.selectedItems()
        if not selected:
            self.selection_cleared.emit()
            return
        first = selected[0]
        if isinstance(first, NodeItem):
            self.node_item_selected.emit(first)
        elif isinstance(first, EdgeItem):
            self.edge_item_selected.emit(first)


class GraphView(QGraphicsView):
    def __init__(self, scene: GraphScene, parent: QWidget | None = None) -> None:
        super().__init__(scene, parent)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setAcceptDrops(True)
        self._pan_active = False
        self._pan_start = QPointF()

    def wheelEvent(self, event: Any) -> None:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
            self.scale(factor, factor)
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event: Any) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._pan_active = True
            self._pan_start = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: Any) -> None:
        if self._pan_active:
            delta = event.position() - self._pan_start
            self._pan_start = event.position()
            self.horizontalScrollBar().setValue(
                int(self.horizontalScrollBar().value() - delta.x())
            )
            self.verticalScrollBar().setValue(
                int(self.verticalScrollBar().value() - delta.y())
            )
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: Any) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._pan_active = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def zoom_to_fit(self) -> None:
        scene = self.scene()
        if scene and scene.items():
            self.fitInView(scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
        else:
            self.resetTransform()

    def dragEnterEvent(self, event: Any) -> None:
        if event.mimeData().hasFormat(_MIME_NODE_TYPE):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: Any) -> None:
        if event.mimeData().hasFormat(_MIME_NODE_TYPE):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: Any) -> None:
        if not event.mimeData().hasFormat(_MIME_NODE_TYPE):
            event.ignore()
            return
        type_id = bytes(event.mimeData().data(_MIME_NODE_TYPE)).decode()
        scene = self.scene()
        if isinstance(scene, GraphScene):
            pos = self.mapToScene(event.position().toPoint())
            scene.create_node_at(type_id, pos)
        event.acceptProposedAction()


class PaletteWidget(QListWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)
        for display_name, type_id in _PALETTE_ITEMS:
            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, type_id)
            self.addItem(item)

    def startDrag(self, supported_actions: Any) -> None:
        current = self.currentItem()
        if current is None:
            return
        type_id: str = current.data(Qt.ItemDataRole.UserRole)
        mime = QMimeData()
        mime.setData(_MIME_NODE_TYPE, type_id.encode())
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.CopyAction)

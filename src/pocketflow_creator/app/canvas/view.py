"""GraphView — the QGraphicsView subclass with zoom, pan, drag-to-connect, and drop."""
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from PySide6.QtCore import QPointF, Qt, Signal
    from PySide6.QtGui import QColor, QPainter, QPen
    from PySide6.QtWidgets import (
        QGraphicsItem,
        QGraphicsLineItem,
        QGraphicsView,
        QWidget,
    )
else:
    try:
        from PySide6.QtCore import QPointF, Qt, Signal
        from PySide6.QtGui import QColor, QPainter, QPen
        from PySide6.QtWidgets import (
            QGraphicsItem,
            QGraphicsLineItem,
            QGraphicsView,
            QWidget,
        )
    except ImportError:  # pragma: no cover
        def Signal(*a: Any, **kw: Any) -> Any:
            return None

        QGraphicsView = object

from pocketflow_creator.app.canvas.items import NodeItem, EdgeItem, _PORT_R, _WIDTH
from pocketflow_creator.app.canvas.scene import GraphScene
from pocketflow_creator.app.canvas.palette import _MIME_NODE_TYPE, _MIME_NODE_SNIPPET

_DRAG_LINE_Z = 1000  # connector rubber-band drawn above all nodes while dragging


class GraphView(QGraphicsView):
    zoom_changed = Signal(float)  # emits current scale factor (1.0 = 100%)

    def __init__(self, scene: GraphScene, parent: QWidget | None = None) -> None:
        super().__init__(scene, parent)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setAcceptDrops(True)
        self._pan_active = False
        self._pan_start = QPointF()
        self._edge_src: NodeItem | None = None
        self._edge_src_action: str = "default"
        self._edge_rubber: QGraphicsLineItem | None = None

    def _node_at_action_port(
        self, scene_pos: QPointF
    ) -> tuple[NodeItem, str] | None:
        """Return (NodeItem, action_name) if scene_pos is near any action port."""
        scene = self.scene()
        if not isinstance(scene, GraphScene):
            return None
        hit_r = _PORT_R * 2.5
        for item in scene._node_items.values():
            actions = item.node.actions or ["default"]
            for action, y in NodeItem._action_port_ys(actions):
                port = item.mapToScene(QPointF(_WIDTH, y))
                dx = scene_pos.x() - port.x()
                dy = scene_pos.y() - port.y()
                if dx * dx + dy * dy <= hit_r * hit_r:
                    return item, action
        return None

    def _node_at_input_port(self, scene_pos: QPointF) -> NodeItem | None:
        """Return NodeItem near input port, with generous hit-radius + body fallback."""
        scene = self.scene()
        if not isinstance(scene, GraphScene):
            return None
        hit_r = _PORT_R * 4.0
        for item in scene._node_items.values():
            port = item.input_port_scene_pos()
            dx = scene_pos.x() - port.x()
            dy = scene_pos.y() - port.y()
            if dx * dx + dy * dy <= hit_r * hit_r:
                return item
        for item in scene._node_items.values():
            local = item.mapFromScene(scene_pos)
            if 0 <= local.y() <= item.height and -_PORT_R <= local.x() <= _WIDTH:
                return item
        return None

    def zoom_in(self) -> None:
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.scale(1.2, 1.2)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.zoom_changed.emit(self.transform().m11())

    def zoom_out(self) -> None:
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.scale(1 / 1.2, 1 / 1.2)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.zoom_changed.emit(self.transform().m11())

    def zoom_to_item(self, item: QGraphicsItem) -> None:
        rect = item.mapRectToScene(item.boundingRect()).adjusted(-20, -20, 20, 20)
        self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
        self.zoom_changed.emit(self.transform().m11())

    def wheelEvent(self, event: Any) -> None:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
            self.scale(factor, factor)
            self.zoom_changed.emit(self.transform().m11())
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event: Any) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._pan_active = True
            self._pan_start = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.position().toPoint())
            hit = self._node_at_action_port(scene_pos)
            if hit is not None:
                src, action = hit
                self._edge_src = src
                self._edge_src_action = action
                sp = src.action_port_scene_pos(action)
                rubber = QGraphicsLineItem(sp.x(), sp.y(), scene_pos.x(), scene_pos.y())
                rubber.setPen(QPen(QColor("#4a9eff"), 1.5, Qt.PenStyle.DashLine))
                rubber.setZValue(_DRAG_LINE_Z)
                self.scene().addItem(rubber)
                self._edge_rubber = rubber
                self.setCursor(Qt.CursorShape.CrossCursor)
                event.accept()
                return
        super().mousePressEvent(event)
        self.setFocus()  # ensure Delete key reaches the scene

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
        elif self._edge_src is not None and self._edge_rubber is not None:
            scene_pos = self.mapToScene(event.position().toPoint())
            sp = self._edge_src.action_port_scene_pos(self._edge_src_action)
            self._edge_rubber.setLine(sp.x(), sp.y(), scene_pos.x(), scene_pos.y())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: Any) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._pan_active = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        elif event.button() == Qt.MouseButton.LeftButton and self._edge_src is not None:
            src = self._edge_src
            self._edge_src = None
            scene = self.scene()
            if self._edge_rubber is not None:
                scene.removeItem(self._edge_rubber)
                self._edge_rubber = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
            # Use Qt's own spatial query — guaranteed correct under any zoom/pan/transform
            scene_pos = self.mapToScene(event.position().toPoint())
            tgt: NodeItem | None = None
            for item in scene.items(scene_pos):
                if isinstance(item, NodeItem) and item is not src:
                    tgt = item
                    break
            if tgt is not None and isinstance(scene, GraphScene):
                scene.edge_creation_requested.emit(src, tgt, self._edge_src_action)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def zoom_to_fit(self) -> None:
        scene = self.scene()
        if scene and scene.items():
            self.fitInView(scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
        else:
            self.resetTransform()
        self.zoom_changed.emit(self.transform().m11())

    def _has_node_mime(self, event: Any) -> bool:
        return event.mimeData().hasFormat(_MIME_NODE_TYPE) or event.mimeData().hasFormat(
            _MIME_NODE_SNIPPET
        )

    def dragEnterEvent(self, event: Any) -> None:
        if self._has_node_mime(event):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: Any) -> None:
        if self._has_node_mime(event):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: Any) -> None:
        scene = self.scene()
        if not isinstance(scene, GraphScene):
            event.ignore()
            return
        pos = self.mapToScene(event.position().toPoint())
        mime = event.mimeData()
        if mime.hasFormat(_MIME_NODE_SNIPPET):
            raw = bytes(mime.data(_MIME_NODE_SNIPPET)).decode()
            snippet: dict[str, Any] = json.loads(raw)
            scene.create_node_at(
                snippet.get("type_id", "basic_node"),
                pos,
                title=snippet.get("title"),
                actions=snippet.get("actions"),
                properties=snippet.get("properties"),
            )
        elif mime.hasFormat(_MIME_NODE_TYPE):
            type_id = bytes(mime.data(_MIME_NODE_TYPE)).decode()
            scene.create_node_at(type_id, pos)
        else:
            event.ignore()
            return
        event.acceptProposedAction()

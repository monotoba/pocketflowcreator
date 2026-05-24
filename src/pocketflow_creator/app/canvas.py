from __future__ import annotations

import json
import math
import uuid
from pathlib import Path
from typing import Any

try:
    from PySide6.QtCore import QMimeData, QPointF, QRectF, QSize, Qt, Signal
    from PySide6.QtGui import (
        QBrush,
        QColor,
        QDrag,
        QFont,
        QIcon,
        QPainter,
        QPainterPath,
        QPen,
        QPixmap,
        QPolygonF,
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
_MIME_NODE_SNIPPET = "application/x-pocketflow-node-snippet"
_ROLE_SNIPPET = Qt.ItemDataRole(Qt.ItemDataRole.UserRole.value + 1)  # type: ignore[attr-defined]


def _load_snippets() -> list[dict[str, Any]]:
    snippets_path = Path(__file__).parent.parent / "node_snippets.yaml"
    if not snippets_path.exists():
        return []
    try:
        import yaml

        data = yaml.safe_load(snippets_path.read_text(encoding="utf-8")) or {}
        return list(data.get("snippets", []))
    except Exception:
        return []
_WIDTH = 160
_HEIGHT = 60
_PORT_R = 5

# ── Node type visual metadata ─────────────────────────────────────────────
# (display_name, type_id, bg_color_hex)
_PALETTE_ITEMS_EX: list[tuple[str, str, str]] = [
    ("Start Node",        "start_node",       "#27ae60"),
    ("Stop Node",         "stop_node",        "#e74c3c"),
    ("Basic Node",        "basic_node",       "#2980b9"),
    ("Router Node",       "router_node",      "#e67e22"),
    ("LLM Prompt Node",   "llm_prompt_node",  "#8e44ad"),
    ("JSON LLM Node",     "json_llm_node",    "#16a085"),
    ("Classifier Node",   "classifier_node",  "#d35400"),
    ("Python Tool Node",  "python_tool_node", "#2c3e50"),
    ("File Reader Node",  "file_reader_node", "#1a6b3c"),
    ("Human Review Node", "human_review_node","#c0392b"),
    ("Batch Node",        "batch_node",       "#34495e"),
    ("Subflow Node",      "subflow_node",     "#7f8c8d"),
]

_PALETTE_ITEMS: list[tuple[str, str]] = [
    (name, tid) for name, tid, _ in _PALETTE_ITEMS_EX
]

# Map type_id → bg hex (used by NodeItem paint and icon generator)
NODE_TYPE_COLOR: dict[str, str] = {tid: color for _, tid, color in _PALETTE_ITEMS_EX}

# ── Per-type icon drawing functions ──────────────────────────────────────────
# Each receives (painter, size) with antialiasing already enabled and the
# background already painted. Draw white shapes that communicate the node's purpose.

def _ico_start(p: QPainter, sz: float) -> None:
    """Right-pointing play triangle — universally means 'start/begin'."""
    m = sz * 0.22
    poly = QPolygonF([QPointF(m, m), QPointF(sz - m, sz / 2), QPointF(m, sz - m)])
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    p.drawPolygon(poly)


def _ico_stop(p: QPainter, sz: float) -> None:
    """Rounded stop square — universally means 'stop/end'."""
    m = sz * 0.27
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    p.drawRoundedRect(QRectF(m, m, sz - 2 * m, sz - 2 * m), sz * 0.1, sz * 0.1)


def _ico_gear(p: QPainter, sz: float) -> None:
    """Gear/cog — means 'process / compute'."""
    cx, cy = sz / 2, sz / 2
    outer_r = sz * 0.42
    inner_r = sz * 0.29
    hole_r = sz * 0.14
    n = 6  # teeth (6 reads cleanly at small sizes)
    pts: list[QPointF] = []
    for i in range(n * 2):
        angle = math.pi * i / n - math.pi / (n * 2)
        r = outer_r if i % 2 == 0 else inner_r
        pts.append(QPointF(cx + r * math.cos(angle), cy + r * math.sin(angle)))
    gear = QPainterPath()
    gear.addPolygon(QPolygonF(pts))
    gear.closeSubpath()
    hole = QPainterPath()
    hole.addEllipse(QPointF(cx, cy), hole_r, hole_r)
    p.setPen(Qt.PenStyle.NoPen)
    p.fillPath(gear.subtracted(hole), QColor("white"))


def _ico_fork(p: QPainter, sz: float) -> None:
    """Y-fork: one line in, two lines out — means 'route / branch'."""
    w = max(2.0, sz * 0.12)
    pen = QPen(
        QColor("white"), w, Qt.PenStyle.SolidLine,
        Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin,
    )
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    cx, cy = sz * 0.46, sz / 2
    # Input stem
    p.drawLine(QPointF(sz * 0.1, cy), QPointF(cx, cy))
    # Two output branches
    p.drawLine(QPointF(cx, cy), QPointF(sz * 0.9, sz * 0.26))
    p.drawLine(QPointF(cx, cy), QPointF(sz * 0.9, sz * 0.74))
    # Arrowhead tips (small V shapes)
    ah = sz * 0.1
    for ty in (sz * 0.26, sz * 0.74):
        p.drawLine(QPointF(sz * 0.9 - ah, ty - ah * 0.6), QPointF(sz * 0.9, ty))
        p.drawLine(QPointF(sz * 0.9 - ah, ty + ah * 0.6), QPointF(sz * 0.9, ty))


def _ico_chat_bubble(p: QPainter, sz: float) -> None:
    """Speech bubble — means 'language model / AI prompt'."""
    bx, by = sz * 0.08, sz * 0.08
    bw, bh = sz * 0.84, sz * 0.64
    r = sz * 0.16
    path = QPainterPath()
    path.addRoundedRect(QRectF(bx, by, bw, bh), r, r)
    # Triangular tail pointing down-left
    tail = QPolygonF([
        QPointF(sz * 0.18, by + bh),
        QPointF(sz * 0.09, sz * 0.94),
        QPointF(sz * 0.38, by + bh),
    ])
    path.addPolygon(tail)
    p.setPen(Qt.PenStyle.NoPen)
    p.fillPath(path, QColor("white"))


def _ico_json_llm(p: QPainter, sz: float, bg: QColor) -> None:
    """Chat bubble + '{}' label — means 'structured LLM output'."""
    _ico_chat_bubble(p, sz)
    font = QFont()
    font.setPixelSize(max(7, int(sz * 0.30)))
    font.setBold(True)
    p.setFont(font)
    p.setPen(QPen(bg))
    # Draw '{}' centred in the bubble body
    p.drawText(
        QRectF(sz * 0.08, sz * 0.08, sz * 0.84, sz * 0.64),
        Qt.AlignmentFlag.AlignCenter,
        "{}",
    )


def _ico_funnel(p: QPainter, sz: float) -> None:
    """Filter funnel — means 'classify / filter / categorise'."""
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    # Wide trapezoid body
    body = QPolygonF([
        QPointF(sz * 0.07, sz * 0.12),
        QPointF(sz * 0.93, sz * 0.12),
        QPointF(sz * 0.62, sz * 0.56),
        QPointF(sz * 0.38, sz * 0.56),
    ])
    p.drawPolygon(body)
    # Narrow outlet tube
    p.drawRect(QRectF(sz * 0.38, sz * 0.56, sz * 0.24, sz * 0.32))


def _ico_terminal(p: QPainter, sz: float) -> None:
    """'>_' terminal prompt — means 'execute code / Python tool'."""
    w = max(2.0, sz * 0.11)
    pen = QPen(
        QColor("white"), w, Qt.PenStyle.SolidLine,
        Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin,
    )
    p.setPen(pen)
    # '>' chevron on left half
    tip_x = sz * 0.46
    cy = sz / 2
    p.drawLine(QPointF(sz * 0.16, cy - sz * 0.22), QPointF(tip_x, cy))
    p.drawLine(QPointF(tip_x, cy), QPointF(sz * 0.16, cy + sz * 0.22))
    # '_' cursor on right half
    p.drawLine(QPointF(sz * 0.54, cy + sz * 0.22), QPointF(sz * 0.84, cy + sz * 0.22))


def _ico_document(p: QPainter, sz: float, bg: QColor) -> None:
    """Document with folded corner — means 'read / load a file'."""
    bx, by = sz * 0.16, sz * 0.07
    bw, bh = sz * 0.68, sz * 0.86
    fold = sz * 0.22
    # Page body (minus fold triangle)
    page = QPainterPath()
    page.moveTo(bx, by)
    page.lineTo(bx + bw - fold, by)
    page.lineTo(bx + bw, by + fold)
    page.lineTo(bx + bw, by + bh)
    page.lineTo(bx, by + bh)
    page.closeSubpath()
    p.setPen(Qt.PenStyle.NoPen)
    p.fillPath(page, QColor("white"))
    # Fold crease triangle in a slightly lighter bg shade
    crease = QPainterPath()
    crease.moveTo(bx + bw - fold, by)
    crease.lineTo(bx + bw - fold, by + fold)
    crease.lineTo(bx + bw, by + fold)
    crease.closeSubpath()
    p.fillPath(crease, bg.lighter(145))
    # Three content lines in bg colour
    p.setPen(QPen(bg, max(1, int(sz * 0.07))))
    x1, x2 = bx + sz * 0.08, bx + bw - sz * 0.1
    for i in range(3):
        ly = by + sz * 0.36 + i * sz * 0.17
        p.drawLine(QPointF(x1, ly), QPointF(x2, ly))


def _ico_person(p: QPainter, sz: float) -> None:
    """Person silhouette — means 'human in the loop / review'."""
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    # Head
    p.drawEllipse(QPointF(sz / 2, sz * 0.30), sz * 0.17, sz * 0.17)
    # Shoulders: top half of a wide ellipse
    body = QPainterPath()
    body.addEllipse(QRectF(sz * 0.10, sz * 0.50, sz * 0.80, sz * 0.62))
    clip = QPainterPath()
    clip.addRect(QRectF(0, sz * 0.50, sz, sz * 0.50))
    p.fillPath(body.intersected(clip), QColor("white"))


def _ico_stack(p: QPainter, sz: float) -> None:
    """Three stacked offset pages — means 'batch / process many items'."""
    p.setPen(Qt.PenStyle.NoPen)
    rw, rh = sz * 0.58, sz * 0.52
    rx0, ry0 = sz * 0.14, sz * 0.26
    off = sz * 0.1
    for i, alpha in enumerate((110, 160, 255)):
        col = QColor(255, 255, 255, alpha)
        p.setBrush(QBrush(col))
        p.drawRoundedRect(
            QRectF(rx0 + (2 - i) * off, ry0 - (2 - i) * off, rw, rh),
            sz * 0.06, sz * 0.06,
        )


def _ico_subflow(p: QPainter, sz: float) -> None:
    """Box enclosing a mini-flowchart — means 'embedded / nested flow'."""
    # Outer dashed border
    pen = QPen(QColor("white"), max(1.5, sz * 0.08), Qt.PenStyle.DashLine)
    pen.setDashPattern([3, 2])
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    m = sz * 0.07
    p.drawRoundedRect(QRectF(m, m, sz - 2 * m, sz - 2 * m), sz * 0.12, sz * 0.12)
    # Inner mini-boxes and arrow
    solid = QPen(QColor("white"), max(1.0, sz * 0.06))
    p.setPen(solid)
    p.drawRect(QRectF(sz * 0.18, sz * 0.36, sz * 0.22, sz * 0.26))
    p.drawRect(QRectF(sz * 0.60, sz * 0.36, sz * 0.22, sz * 0.26))
    cy = sz * 0.49
    p.drawLine(QPointF(sz * 0.40, cy), QPointF(sz * 0.60, cy))
    ah = sz * 0.08
    p.drawLine(QPointF(sz * 0.60 - ah, cy - ah), QPointF(sz * 0.60, cy))
    p.drawLine(QPointF(sz * 0.60 - ah, cy + ah), QPointF(sz * 0.60, cy))


# Dispatch map: type_id → drawing function
_ICON_DRAW: dict[str, Any] = {
    "start_node":       _ico_start,
    "stop_node":        _ico_stop,
    "basic_node":       _ico_gear,
    "router_node":      _ico_fork,
    "llm_prompt_node":  _ico_chat_bubble,
    "json_llm_node":    None,  # handled specially (needs bg colour)
    "classifier_node":  _ico_funnel,
    "python_tool_node": _ico_terminal,
    "file_reader_node": None,  # handled specially (needs bg colour)
    "human_review_node":_ico_person,
    "batch_node":       _ico_stack,
    "subflow_node":     _ico_subflow,
}


def make_node_icon(type_id: str, size: int = 32) -> QIcon:
    """Return a QIcon for type_id, painted with purpose-built shapes."""
    color_hex = NODE_TYPE_COLOR.get(type_id, "#555555")
    bg = QColor(color_hex)

    px = QPixmap(size, size)
    px.fill(QColor("transparent"))
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Rounded-rect background
    p.setBrush(QBrush(bg))
    p.setPen(QPen(bg.darker(130), 1))
    r = size * 0.22
    p.drawRoundedRect(1, 1, size - 2, size - 2, r, r)

    # Draw the type-specific icon
    draw_fn = _ICON_DRAW.get(type_id)
    if draw_fn is not None:
        draw_fn(p, float(size))
    elif type_id == "json_llm_node":
        _ico_json_llm(p, float(size), bg)
    elif type_id == "file_reader_node":
        _ico_document(p, float(size), bg)
    else:
        # Fallback: draw type_id initials as text
        font = QFont()
        font.setPixelSize(max(8, int(size * 0.38)))
        font.setBold(True)
        p.setFont(font)
        p.setPen(QPen(QColor("white")))
        initials = "".join(w[0].upper() for w in type_id.split("_") if w)[:2]
        p.drawText(QRectF(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, initials)

    p.end()
    return QIcon(px)


class NodeItem(QGraphicsItem):
    def __init__(self, node: NodeModel, parent: QGraphicsItem | None = None) -> None:
        super().__init__(parent)
        self._node = node
        self._has_error = False
        self._has_breakpoint = False
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

    def boundingRect(self) -> QRectF:
        return QRectF(-_PORT_R, 0, _WIDTH + 2 * _PORT_R, _HEIGHT)

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        scene = self.scene()
        dark = scene._dark if hasattr(scene, "_dark") else True  # type: ignore[union-attr]
        colors = _DARK_COLORS if dark else _LIGHT_COLORS

        body = QRectF(0, 0, _WIDTH, _HEIGHT)
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

        base_font = painter.font()
        title_font = QFont(base_font)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(QPen(QColor(colors["title"])))
        painter.drawText(
            QRectF(12, 8, _WIDTH - 24, 22), Qt.AlignmentFlag.AlignVCenter, self._node.title
        )

        badge_font = QFont(base_font)
        badge_font.setPointSize(max(base_font.pointSize() - 1, 7))
        painter.setFont(badge_font)
        painter.setPen(QPen(QColor(colors["badge"])))
        painter.drawText(
            QRectF(12, 30, _WIDTH - 24, 18), Qt.AlignmentFlag.AlignVCenter, self._node.type_id
        )

        painter.setPen(QPen(QColor(colors["port_outline"]), 1))
        painter.setBrush(QBrush(QColor(colors["port_fill"])))
        painter.drawEllipse(QPointF(0, _HEIGHT / 2), _PORT_R, _PORT_R)
        painter.drawEllipse(QPointF(_WIDTH, _HEIGHT / 2), _PORT_R, _PORT_R)

        if self._has_breakpoint:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(colors["breakpoint"])))
            painter.drawEllipse(QPointF(_WIDTH - 10, 10), 5, 5)

    def port_scene_pos(self) -> QPointF:
        return self.mapToScene(QPointF(_WIDTH, _HEIGHT / 2))

    def input_port_scene_pos(self) -> QPointF:
        return self.mapToScene(QPointF(0, _HEIGHT / 2))

    def mouseDoubleClickEvent(self, event: Any) -> None:
        scene = self.scene()
        if isinstance(scene, GraphScene):
            scene.node_item_double_clicked.emit(self)

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


class GraphScene(QGraphicsScene):
    node_item_selected = Signal(object)
    edge_item_selected = Signal(object)
    selection_cleared = Signal()
    node_item_double_clicked = Signal(object)  # emits NodeItem
    node_created = Signal(object)              # emits NodeItem
    node_deleted = Signal(str)                 # emits node_id

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self._node_items: dict[str, NodeItem] = {}
        self._edge_items: list[EdgeItem] = []
        self._dark = True
        self.selectionChanged.connect(self._on_selection_changed)

    def set_dark(self, dark: bool) -> None:
        self._dark = dark
        edge_color = _DARK_COLORS["edge"] if dark else _LIGHT_COLORS["edge"]
        for ei in self._edge_items:
            ei.setPen(QPen(QColor(edge_color), 1.5))
        self.update()

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

    def create_node_at(
        self,
        type_id: str,
        pos: QPointF,
        *,
        title: str | None = None,
        actions: list[str] | None = None,
        properties: dict[str, Any] | None = None,
    ) -> NodeItem:
        node = NodeModel(
            id=f"node_{uuid.uuid4().hex[:8]}",
            type_id=type_id,
            title=title or type_id.replace("_", " ").title(),
            position={"x": pos.x(), "y": pos.y()},
            actions=actions or [],
            properties=properties or {},
        )
        item = NodeItem(node)
        self.addItem(item)
        self._node_items[node.id] = item
        self.node_created.emit(item)
        return item

    def update_edges(self) -> None:
        for ei in self._edge_items:
            ei.update_position()

    def apply_validation(self, error_ids: set[str]) -> None:
        for node_id, item in self._node_items.items():
            item.set_has_error(node_id in error_ids)

    def keyPressEvent(self, event: Any) -> None:
        if event.key() == Qt.Key.Key_Delete:  # type: ignore[attr-defined]
            for item in list(self.selectedItems()):
                if isinstance(item, NodeItem):
                    node_id = item.node.id
                    for ei in [e for e in self._edge_items if e._src is item or e._tgt is item]:
                        self.removeItem(ei)
                        self._edge_items.remove(ei)
                    self.removeItem(item)
                    self._node_items.pop(node_id, None)
                    self.node_deleted.emit(node_id)
        else:
            super().keyPressEvent(event)

    def auto_layout(self) -> None:
        """Hierarchical BFS layout: layers left-to-right, nodes top-to-bottom within layer."""
        if not self._node_items:
            return
        H_GAP = 60
        V_GAP = 30
        all_ids = set(self._node_items.keys())
        has_incoming: set[str] = {ei._tgt.node.id for ei in self._edge_items}
        roots = all_ids - has_incoming or all_ids

        root = next(
            (nid for nid in roots if self._node_items[nid].node.type_id == "start_node"),
            next(iter(roots)),
        )

        adjacency: dict[str, list[str]] = {nid: [] for nid in all_ids}
        for ei in self._edge_items:
            adjacency[ei._src.node.id].append(ei._tgt.node.id)

        layer: dict[str, int] = {root: 0}
        queue = [root]
        visited = {root}
        while queue:
            cur = queue.pop(0)
            for nb in adjacency[cur]:
                if nb not in visited:
                    visited.add(nb)
                    layer[nb] = layer[cur] + 1
                    queue.append(nb)

        max_layer = max(layer.values()) if layer else 0
        for nid in all_ids:
            if nid not in layer:
                max_layer += 1
                layer[nid] = max_layer

        layers: dict[int, list[str]] = {}
        for nid, lyr in layer.items():
            layers.setdefault(lyr, []).append(nid)

        for lyr_idx in sorted(layers.keys()):
            nodes_in_layer = layers[lyr_idx]
            total_h = len(nodes_in_layer) * (_HEIGHT + V_GAP) - V_GAP
            y_start = -total_h / 2
            x_pos = 60 + lyr_idx * (_WIDTH + H_GAP)
            for i, nid in enumerate(nodes_in_layer):
                item = self._node_items[nid]
                y_pos = y_start + i * (_HEIGHT + V_GAP)
                item.setPos(x_pos, y_pos)
                item.node.position["x"] = x_pos
                item.node.position["y"] = y_pos

        self.update_edges()

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


class PaletteWidget(QListWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)
        self.setIconSize(QSize(28, 28))
        for display_name, type_id in _PALETTE_ITEMS:
            item = QListWidgetItem(make_node_icon(type_id, 28), display_name)
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

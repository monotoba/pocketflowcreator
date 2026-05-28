"""GraphScene — the QGraphicsScene subclass that owns all canvas items."""
from __future__ import annotations

import math
import uuid
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from PySide6.QtCore import QPointF, Qt, Signal
    from PySide6.QtGui import QColor, QPen
    from PySide6.QtWidgets import QGraphicsScene
else:
    try:
        from PySide6.QtCore import QPointF, Qt, Signal
        from PySide6.QtGui import QColor, QPen
        from PySide6.QtWidgets import QGraphicsScene
    except ImportError:  # pragma: no cover
        def Signal(*a: Any, **kw: Any) -> Any:
            return None

        QGraphicsScene = object

from pocketflow_creator.model.graph_model import EdgeModel, GraphModel, NodeModel
from pocketflow_creator.app.canvas.items import (
    EdgeItem,
    NodeItem,
    _DARK_COLORS,
    _HEIGHT,
    _LIGHT_COLORS,
    _WIDTH,
)


class GraphScene(QGraphicsScene):
    node_item_selected = Signal(object)
    edge_item_selected = Signal(object)
    selection_cleared = Signal()
    node_item_double_clicked = Signal(object)  # emits NodeItem
    node_created = Signal(object)              # emits NodeItem
    node_deleted = Signal(str)                 # emits node_id
    edge_creation_requested = Signal(object, object, str)  # emits (src NodeItem, tgt NodeItem, action)
    edge_deleted = Signal(str)                 # emits edge_id
    set_start_node_requested = Signal(object)  # emits NodeItem
    node_drag_started = Signal(str)            # emits node_id when a drag begins
    node_move_finished = Signal(str)           # emits node_id when a drag ends with position change

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self._node_items: dict[str, NodeItem] = {}
        self._edge_items: list[EdgeItem] = []
        self._dark = True
        self._connector_style: str = "straight"
        self.selectionChanged.connect(self._on_selection_changed)

    @property
    def connector_style(self) -> str:
        return self._connector_style

    def set_connector_style(self, style: str) -> None:
        self._connector_style = style
        self.update_edges()

    @property
    def is_dark(self) -> bool:
        """Return True when the scene is rendering in dark mode."""
        return self._dark

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
            item.set_is_start(node.id == graph.start_node)
            self.addItem(item)
            self._node_items[node.id] = item
        for edge in graph.edges:
            src = self._node_items.get(edge.from_node)
            tgt = self._node_items.get(edge.to_node)
            if src and tgt:
                ei = EdgeItem(edge, src, tgt)
                self.addItem(ei)
                self._edge_items.append(ei)
        self.update_edges()

    def mark_start_node(self, node_id: str | None) -> None:
        for nid, item in self._node_items.items():
            item.set_is_start(nid == node_id)

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

    def add_edge(self, src: NodeItem, tgt: NodeItem, edge: EdgeModel) -> EdgeItem:
        ei = EdgeItem(edge, src, tgt)
        self.addItem(ei)
        self._edge_items.append(ei)
        ei.update_position(self._connector_style)
        return ei

    def update_edges(self) -> None:
        for ei in self._edge_items:
            ei.update_position(self._connector_style)

    def apply_validation(self, error_ids: set[str]) -> None:
        for node_id, item in self._node_items.items():
            item.set_has_error(node_id in error_ids)

    def delete_selected(self) -> None:
        """Remove all selected NodeItems and EdgeItems from the scene."""
        for item in list(self.selectedItems()):
            if isinstance(item, NodeItem):
                node_id = item.node.id
                for ei in [e for e in self._edge_items if e._src is item or e._tgt is item]:
                    self.removeItem(ei)
                    self._edge_items.remove(ei)
                    self.edge_deleted.emit(ei.edge.id)
                self.removeItem(item)
                self._node_items.pop(node_id, None)
                self.node_deleted.emit(node_id)
            elif isinstance(item, EdgeItem):
                edge_id = item.edge.id
                self.removeItem(item)
                if item in self._edge_items:
                    self._edge_items.remove(item)
                self.edge_deleted.emit(edge_id)

    def delete_node_by_id(self, node_id: str) -> None:
        """Remove a specific node from the scene by its ID."""
        item = self._node_items.get(node_id)
        if item is None:
            return
        for ei in [e for e in self._edge_items if e._src is item or e._tgt is item]:
            self.removeItem(ei)
            self._edge_items.remove(ei)
        self.removeItem(item)
        self._node_items.pop(node_id, None)
        self.node_deleted.emit(node_id)

    def keyPressEvent(self, event: Any) -> None:
        if event.key() == Qt.Key.Key_Delete:  # type: ignore[attr-defined]
            self.delete_selected()
        else:
            super().keyPressEvent(event)

    def auto_layout(self, h_gap: int = 60, v_gap: int = 30) -> None:
        """Hierarchical BFS layout: layers left-to-right, nodes top-to-bottom within layer."""
        if not self._node_items:
            return
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
            items_in_layer = [self._node_items[nid] for nid in nodes_in_layer]
            heights = [it.height for it in items_in_layer]
            total_h = sum(heights) + v_gap * (len(heights) - 1)
            y_start = -total_h / 2
            x_pos = 60 + lyr_idx * (_WIDTH + h_gap)
            y_pos = y_start
            for item, h in zip(items_in_layer, heights):
                item.setPos(x_pos, y_pos)
                item.node.position["x"] = x_pos
                item.node.position["y"] = y_pos
                y_pos += h + v_gap

        self.update_edges()

    def layout_grid(self, max_cols: int = 4, h_gap: int = 60, v_gap: int = 30) -> None:
        """Grid layout: nodes placed in rows and columns, left-to-right, top-to-bottom."""
        if not self._node_items:
            return
        items = list(self._node_items.values())
        for i, item in enumerate(items):
            col = i % max_cols
            row = i // max_cols
            x = 60 + col * (_WIDTH + h_gap)
            y = 60 + row * (item.height + v_gap)
            item.setPos(x, y)
            item.node.position["x"] = x
            item.node.position["y"] = y
        self.update_edges()

    def layout_force(self, h_gap: int = 60, v_gap: int = 30, iterations: int = 150) -> None:
        """Force-directed (spring-embedder) layout."""
        if not self._node_items:
            return
        items = self._node_items
        positions: dict[str, list[float]] = {
            nid: [item.pos().x(), item.pos().y()] for nid, item in items.items()
        }
        edges_list = [(ei._src.node.id, ei._tgt.node.id) for ei in self._edge_items]
        k = math.sqrt((_WIDTH + h_gap) * (_HEIGHT + v_gap))
        ids = list(items.keys())

        for step in range(iterations):
            forces: dict[str, list[float]] = {nid: [0.0, 0.0] for nid in ids}
            # Repulsion between all pairs
            for i, u in enumerate(ids):
                for v in ids[i + 1:]:
                    dx = positions[u][0] - positions[v][0]
                    dy = positions[u][1] - positions[v][1]
                    d = math.sqrt(dx * dx + dy * dy) or 0.1
                    f = k * k / d
                    forces[u][0] += f * dx / d
                    forces[u][1] += f * dy / d
                    forces[v][0] -= f * dx / d
                    forces[v][1] -= f * dy / d
            # Attraction along edges
            for u, v in edges_list:
                dx = positions[v][0] - positions[u][0]
                dy = positions[v][1] - positions[u][1]
                d = math.sqrt(dx * dx + dy * dy) or 0.1
                f = d * d / k
                forces[u][0] += f * dx / d
                forces[u][1] += f * dy / d
                forces[v][0] -= f * dx / d
                forces[v][1] -= f * dy / d
            # Apply with cooling temperature
            temp = (_WIDTH + h_gap) * (1.0 - step / iterations)
            for nid in ids:
                fx, fy = forces[nid]
                d = math.sqrt(fx * fx + fy * fy) or 0.1
                positions[nid][0] += (fx / d) * min(d, temp)
                positions[nid][1] += (fy / d) * min(d, temp)

        for nid, item in items.items():
            x, y = positions[nid]
            item.setPos(x, y)
            item.node.position["x"] = x
            item.node.position["y"] = y
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

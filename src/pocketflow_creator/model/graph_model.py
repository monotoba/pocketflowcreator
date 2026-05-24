from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class NodeModel:
    id: str
    type_id: str
    title: str
    position: dict[str, float] = field(default_factory=lambda: {"x": 0.0, "y": 0.0})
    properties: dict[str, Any] = field(default_factory=dict)
    actions: list[str] = field(default_factory=list)
    reads: list[str] = field(default_factory=list)
    writes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class EdgeModel:
    id: str
    from_node: str
    action: str
    to_node: str


@dataclass(slots=True)
class GraphModel:
    id: str
    title: str
    flow_type: str = "sync"
    start_node: str | None = None
    nodes: list[NodeModel] = field(default_factory=list)
    edges: list[EdgeModel] = field(default_factory=list)

    def node_ids(self) -> set[str]:
        return {node.id for node in self.nodes}

    def find_node(self, node_id: str) -> NodeModel | None:
        return next((node for node in self.nodes if node.id == node_id), None)

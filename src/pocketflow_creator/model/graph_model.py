from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TypedDict


class Position(TypedDict):
    """Canvas position for a node, in scene co-ordinates."""

    x: float
    y: float


@dataclass(slots=True)
class NodeModel:
    """Data model for a single canvas node.

    ``position`` is in scene co-ordinates.  ``actions`` is the list of
    output-action labels; an empty list means a single implicit "default" action.
    ``reads`` / ``writes`` document the shared-store keys this node accesses.
    """

    id: str
    type_id: str
    title: str
    position: Position = field(default_factory=lambda: Position(x=0.0, y=0.0))
    properties: dict[str, Any] = field(default_factory=dict)
    actions: list[str] = field(default_factory=list)
    reads: list[str] = field(default_factory=list)
    writes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class EdgeModel:
    """Directed connection between two nodes carrying a named action label."""

    id: str
    from_node: str
    action: str
    to_node: str


@dataclass(slots=True)
class GraphModel:
    """A complete flow graph: nodes, directed edges, and execution metadata."""

    id: str
    title: str
    flow_type: str = "sync"
    start_node: str | None = None
    nodes: list[NodeModel] = field(default_factory=list)
    edges: list[EdgeModel] = field(default_factory=list)

    def node_ids(self) -> set[str]:
        return {node.id for node in self.nodes}

    def node_index(self) -> dict[str, NodeModel]:
        """Return a fresh {id: NodeModel} mapping for O(1) repeated lookups.

        Builds a new dict on each call — use when multiple lookups are needed
        in a tight loop rather than calling find_node() for each.
        """
        return {node.id: node for node in self.nodes}

    def find_node(self, node_id: str) -> NodeModel | None:
        """Return the NodeModel with *node_id*, or None.

        O(n) — use node_index() to build a reusable lookup dict when making
        multiple calls in a loop.
        """
        return next((node for node in self.nodes if node.id == node_id), None)

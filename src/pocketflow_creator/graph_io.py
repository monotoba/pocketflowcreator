from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from pocketflow_creator.model.graph_model import EdgeModel, GraphModel, NodeModel

GRAPH_SCHEMA_VERSION = "0.1"


class GraphLoader:
    def load(self, path: Path) -> GraphModel:
        with path.open(encoding="utf-8") as f:
            data: dict[str, Any] = yaml.safe_load(f)
        version = str(data.get("schema_version", ""))
        if version != GRAPH_SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported graph schema version {version!r}; expected {GRAPH_SCHEMA_VERSION!r}"
            )
        return GraphModel(
            id=str(data["id"]),
            title=str(data["title"]),
            flow_type=str(data.get("flow_type", "sync")),
            start_node=data.get("start_node"),
            nodes=[self._parse_node(n) for n in data.get("nodes", [])],
            edges=[self._parse_edge(e) for e in data.get("edges", [])],
        )

    def _parse_node(self, data: dict[str, Any]) -> NodeModel:
        raw = data.get("position", {})
        return NodeModel(
            id=str(data["id"]),
            type_id=str(data["type_id"]),
            title=str(data["title"]),
            position={"x": float(raw.get("x", 0.0)), "y": float(raw.get("y", 0.0))},
            properties=dict(data.get("properties", {})),
            actions=list(data.get("actions", [])),
            reads=list(data.get("reads", [])),
            writes=list(data.get("writes", [])),
        )

    def _parse_edge(self, data: dict[str, Any]) -> EdgeModel:
        return EdgeModel(
            id=str(data["id"]),
            from_node=str(data["from_node"]),
            action=str(data["action"]),
            to_node=str(data["to_node"]),
        )


class GraphSaver:
    def save(self, graph: GraphModel, path: Path) -> None:
        data: dict[str, Any] = {
            "schema_version": GRAPH_SCHEMA_VERSION,
            "id": graph.id,
            "title": graph.title,
            "flow_type": graph.flow_type,
            "start_node": graph.start_node,
            "nodes": [self._node_to_dict(n) for n in graph.nodes],
            "edges": [self._edge_to_dict(e) for e in graph.edges],
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False, default_flow_style=False)

    def _node_to_dict(self, node: NodeModel) -> dict[str, Any]:
        d: dict[str, Any] = {
            "id": node.id,
            "type_id": node.type_id,
            "title": node.title,
            "position": node.position,
        }
        if node.properties:
            d["properties"] = node.properties
        if node.actions:
            d["actions"] = node.actions
        if node.reads:
            d["reads"] = node.reads
        if node.writes:
            d["writes"] = node.writes
        return d

    def _edge_to_dict(self, edge: EdgeModel) -> dict[str, Any]:
        return {
            "id": edge.id,
            "from_node": edge.from_node,
            "action": edge.action,
            "to_node": edge.to_node,
        }

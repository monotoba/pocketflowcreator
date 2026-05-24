from __future__ import annotations

from dataclasses import dataclass

from pocketflow_creator.model.graph_model import GraphModel


@dataclass(slots=True)
class ValidationIssue:
    severity: str
    code: str
    object_id: str
    message: str


class GraphValidator:
    """Starter validation engine for PocketFlow Creator graphs."""

    def validate(self, graph: GraphModel) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        issues.extend(self._validate_unique_node_ids(graph))
        issues.extend(self._validate_start_node(graph))
        issues.extend(self._validate_edges(graph))
        issues.extend(self._validate_declared_actions(graph))
        return issues

    def _validate_unique_node_ids(self, graph: GraphModel) -> list[ValidationIssue]:
        seen: set[str] = set()
        issues: list[ValidationIssue] = []
        for node in graph.nodes:
            if node.id in seen:
                issues.append(
                    ValidationIssue("error", "PFCE1002", node.id, f"Duplicate node ID: {node.id}")
                )
            seen.add(node.id)
        return issues

    def _validate_start_node(self, graph: GraphModel) -> list[ValidationIssue]:
        if not graph.start_node:
            return [ValidationIssue("error", "PFCE1001", graph.id, "No start node selected.")]
        if graph.start_node not in graph.node_ids():
            return [
                ValidationIssue(
                    "error",
                    "PFCE1003",
                    graph.id,
                    f"Start node '{graph.start_node}' does not exist.",
                )
            ]
        return []

    def _validate_edges(self, graph: GraphModel) -> list[ValidationIssue]:
        node_ids = graph.node_ids()
        issues: list[ValidationIssue] = []
        for edge in graph.edges:
            if edge.from_node not in node_ids:
                issues.append(
                    ValidationIssue(
                        "error",
                        "PFCE2001",
                        edge.id,
                        f"Edge source node '{edge.from_node}' does not exist.",
                    )
                )
            if edge.to_node not in node_ids:
                issues.append(
                    ValidationIssue(
                        "error",
                        "PFCE2002",
                        edge.id,
                        f"Edge destination node '{edge.to_node}' does not exist.",
                    )
                )
            if not edge.action:
                issues.append(
                    ValidationIssue("error", "PFCE2003", edge.id, "Edge has no action label.")
                )
        return issues

    def _validate_declared_actions(self, graph: GraphModel) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        for edge in graph.edges:
            source = graph.find_node(edge.from_node)
            if source is None:
                continue
            if source.actions and edge.action not in source.actions:
                issues.append(
                    ValidationIssue(
                        "error",
                        "PFCE2101",
                        edge.id,
                        f"Action '{edge.action}' is not declared by node '{source.id}'.",
                    )
                )
        return issues

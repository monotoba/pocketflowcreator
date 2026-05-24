from __future__ import annotations

from pocketflow_creator.model.graph_model import GraphModel
from pocketflow_creator.model.project import ProjectModel
from pocketflow_creator.validation.graph_validator import GraphValidator


def generate_project_report(project: ProjectModel, graphs: dict[str, GraphModel]) -> str:
    """Return a Markdown summary of the project's nodes, edges, and validation status."""
    lines: list[str] = [
        f"# {project.name} — Project Report",
        "",
        f"**Package:** `{project.package_name}`  ",
        f"**Provider:** {project.default_provider}  ",
        f"**Model:** {project.default_model}",
        "",
        "---",
        "",
    ]

    validator = GraphValidator()

    for rel, graph in graphs.items():
        issues = validator.validate(graph)
        status = "OK" if not issues else f"{len(issues)} issue(s)"
        lines += [
            f"## Graph: {graph.title} (`{rel}`)",
            "",
            f"- **Nodes:** {len(graph.nodes)}",
            f"- **Edges:** {len(graph.edges)}",
            f"- **Start node:** `{graph.start_node or 'none'}`",
            f"- **Validation:** {status}",
            "",
        ]

        if graph.nodes:
            lines += ["### Nodes", ""]
            lines += ["| ID | Title | Type | Actions |", "|----|-------|------|---------|"]
            for node in graph.nodes:
                actions = ", ".join(node.actions) or "default"
                lines.append(f"| `{node.id}` | {node.title} | {node.type_id} | {actions} |")
            lines.append("")

        if graph.edges:
            lines += ["### Edges", ""]
            lines += ["| ID | From | Action | To |", "|----|------|--------|----|"]
            for edge in graph.edges:
                lines.append(
                    f"| `{edge.id}` | `{edge.from_node}` | {edge.action} | `{edge.to_node}` |"
                )
            lines.append("")

        if issues:
            lines += ["### Validation Issues", ""]
            for issue in issues:
                lines.append(
                    f"- **[{issue.severity.upper()}]** `{issue.object_id}`: {issue.message}"
                )
            lines.append("")

    return "\n".join(lines)

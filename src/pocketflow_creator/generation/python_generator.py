from __future__ import annotations

from typing import TYPE_CHECKING

from jinja2 import Environment, PackageLoader, StrictUndefined

from pocketflow_creator.model.graph_model import GraphModel, NodeModel

if TYPE_CHECKING:
    from typing import TypedDict

    class _NodeCtx(TypedDict):
        class_name: str
        var_name: str
        title: str
        reads: list[str]
        writes: list[str]
        action: str


class PythonGenerator:
    """Jinja2 template-based code generator."""

    def __init__(self) -> None:
        loader = PackageLoader("pocketflow_creator", "templates")
        self._env = Environment(
            loader=loader,
            undefined=StrictUndefined,
            keep_trailing_newline=True,
        )
        self._env.filters["repr"] = repr

    def generate_nodes_py(self, graph: GraphModel) -> str:
        tmpl = self._env.get_template("nodes.py.j2")
        nodes = [self._node_ctx(n) for n in graph.nodes]
        return tmpl.render(nodes=nodes)

    def generate_flow_py(self, graph: GraphModel) -> str:
        tmpl = self._env.get_template("flow.py.j2")
        nodes = [self._node_ctx(n) for n in graph.nodes]
        class_names = [self._class_name(n) for n in graph.nodes]

        index = graph.node_index()
        edges = []
        for edge in graph.edges:
            src = index.get(edge.from_node)
            tgt = index.get(edge.to_node)
            if src and tgt:
                edges.append(
                    {
                        "from_var": self._var_name(src),
                        "to_var": self._var_name(tgt),
                        "action": edge.action,
                    }
                )

        start_node = index.get(graph.start_node or "") or (graph.nodes[0] if graph.nodes else None)
        start_var = self._var_name(start_node) if start_node else "None"

        return tmpl.render(
            nodes=nodes,
            class_names=class_names,
            edges=edges,
            start_var=start_var,
        )

    def _node_ctx(self, node: NodeModel) -> _NodeCtx:
        action = node.actions[0] if node.actions else "default"
        return {
            "class_name": self._class_name(node),
            "var_name": self._var_name(node),
            "title": node.title,
            "reads": node.reads,
            "writes": node.writes,
            "action": action,
        }

    @staticmethod
    def _class_name(node: NodeModel) -> str:
        raw = "".join(part.capitalize() for part in node.id.replace("-", "_").split("_") if part)
        return f"{raw or 'Unnamed'}Node"

    @staticmethod
    def _var_name(node: NodeModel) -> str:
        return node.id.replace("-", "_")

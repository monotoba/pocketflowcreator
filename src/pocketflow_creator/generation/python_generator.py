from __future__ import annotations

from pocketflow_creator.model.graph_model import GraphModel, NodeModel


class PythonGenerator:
    """Starter readable-code generator.

    This generator intentionally emits simple code. Future versions should use
    templates and separate generated code from custom code.
    """

    def generate_nodes_py(self, graph: GraphModel) -> str:
        lines = [
            "from __future__ import annotations",
            "",
            "try:",
            "    from pocketflow import Node",
            "except Exception:",
            "    class Node:  # fallback for generated-code inspection",
            "        def __init__(self, *args, **kwargs): pass",
            "",
        ]
        for node in graph.nodes:
            lines.extend(self._generate_node_class(node))
        return "\n".join(lines) + "\n"

    def generate_flow_py(self, graph: GraphModel) -> str:
        class_names = [self._class_name(node) for node in graph.nodes]
        lines = [
            "from __future__ import annotations",
            "",
            "try:",
            "    from pocketflow import Flow",
            "except Exception:",
            "    class Flow:",
            "        def __init__(self, start=None): self.start = start",
            "",
            f"from .nodes import {', '.join(class_names)}" if class_names else "",
            "",
            "",
            "def build_flow():",
        ]
        if not graph.nodes:
            lines.append("    return Flow(start=None)")
            return "\n".join(lines) + "\n"

        for node in graph.nodes:
            lines.append(f"    {self._var_name(node)} = {self._class_name(node)}()")
        lines.append("")
        for edge in graph.edges:
            source = graph.find_node(edge.from_node)
            target = graph.find_node(edge.to_node)
            if source and target:
                if edge.action == "default":
                    lines.append(f"    {self._var_name(source)} >> {self._var_name(target)}")
                else:
                    src, tgt = self._var_name(source), self._var_name(target)
                    lines.append(f"    {src} - {edge.action!r} >> {tgt}")
        start = graph.find_node(graph.start_node or "") or graph.nodes[0]
        lines.extend(["", f"    return Flow(start={self._var_name(start)})"])
        return "\n".join(lines) + "\n"

    def _generate_node_class(self, node: NodeModel) -> list[str]:
        class_name = self._class_name(node)
        action = node.actions[0] if node.actions else "default"
        return [
            "",
            "",
            f"class {class_name}(Node):",
            f"    \"\"\"Generated node for {node.title}.\"\"\"",
            "",
            "    def prep(self, shared):",
            f"        return {{key: shared.get(key) for key in {node.reads!r}}}",
            "",
            "    def exec(self, prep_res):",
            "        return prep_res",
            "",
            "    def post(self, shared, prep_res, exec_res):",
            f"        # TODO: map outputs to shared keys: {node.writes!r}",
            f"        return {action!r}",
        ]

    def _class_name(self, node: NodeModel) -> str:
        raw = ''.join(part.capitalize() for part in node.id.replace('-', '_').split('_') if part)
        return f"{raw or 'Unnamed'}Node"

    def _var_name(self, node: NodeModel) -> str:
        return node.id.replace('-', '_')

"""
Manages the per-graph live code file that stays in sync with the canvas.

Each project graph gets a file at  <project_root>/code/<stem>.py
containing one class stub per node, wrapped in NODE_START/END markers so
individual blocks can be located and removed without parsing Python.
"""
from __future__ import annotations

import re
from pathlib import Path

from pocketflow_creator.model.graph_model import NodeModel

_NODE_START = "# --- NODE_START: {node_id} ---"
_NODE_END = "# --- NODE_END: {node_id} ---"

_HEADER = '''\
"""
PocketFlow Creator — node implementations for {stem}.
Edit the method bodies freely. Do NOT remove the NODE_START / NODE_END markers.
"""
from __future__ import annotations


'''

_STUB = """\
{start}
class {class_name}({base_class}):
    \"\"\"{type_id}: {title}\"\"\"

    def prep(self, shared: dict) -> object:
        return None

    def exec(self, prep_res: object) -> object:
        return None

    def post(self, shared: dict, prep_res: object, exec_res: object) -> str:
        return "default"

{end}
"""


def _to_class_name(title: str) -> str:
    words = re.sub(r"[^a-zA-Z0-9\s]", " ", title).split()
    return "".join(w.capitalize() for w in words) or "Node"


def _stem_from_rel(graph_rel: str) -> str:
    name = Path(graph_rel).name
    if name.endswith(".pfcgraph.yaml"):
        return name[: -len(".pfcgraph.yaml")]
    return Path(name).stem


def get_code_file(graph_rel: str, project_root: Path) -> Path:
    return project_root / "code" / f"{_stem_from_rel(graph_rel)}.py"


def ensure_code_file(graph_rel: str, project_root: Path) -> Path:
    path = get_code_file(graph_rel, project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(_HEADER.format(stem=_stem_from_rel(graph_rel)), encoding="utf-8")
    return path


_BASE_CLASS_MAP: dict[str, str] = {
    "batch_node":                "BatchNode",
    "async_node":                "AsyncNode",
    "async_batch_node":          "AsyncBatchNode",
    "async_parallel_batch_node": "AsyncParallelBatchNode",
}


def _resolve_base_class(type_id: str, declared_base: str = "") -> str:
    """Return the PocketFlow base class for a node type.

    Uses the explicitly declared base_class if provided; otherwise infers from
    type_id keywords; falls back to "Node".
    """
    if declared_base and declared_base not in ("", "Node"):
        return declared_base
    return _BASE_CLASS_MAP.get(type_id.lower(), "Node")


def add_node(code_path: Path, node: NodeModel, base_class: str = "") -> int:
    """Add a class stub for node if absent. Returns 1-based line of the NODE_START marker.

    base_class: the PocketFlow base class to inherit from (e.g. "Node", "BatchNode").
    If empty, resolved from node.type_id.
    """
    text = code_path.read_text(encoding="utf-8")
    start_marker = _NODE_START.format(node_id=node.id)
    if start_marker in text:
        for i, line in enumerate(text.splitlines(), 1):
            if line.strip() == start_marker:
                return i
        return 1

    resolved = _resolve_base_class(node.type_id, base_class)
    stub = _STUB.format(
        start=start_marker,
        end=_NODE_END.format(node_id=node.id),
        class_name=_to_class_name(node.title),
        title=node.title,
        type_id=node.type_id,
        base_class=resolved,
    )
    new_text = text.rstrip("\n") + "\n\n" + stub
    code_path.write_text(new_text, encoding="utf-8")
    for i, line in enumerate(new_text.splitlines(), 1):
        if line.strip() == start_marker:
            return i
    return 1


def remove_node(code_path: Path, node_id: str) -> None:
    """Remove the class block for node_id, including surrounding blank lines."""
    start_marker = _NODE_START.format(node_id=node_id)
    end_marker = _NODE_END.format(node_id=node_id)
    text = code_path.read_text(encoding="utf-8")
    if start_marker not in text:
        return
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    inside = False
    for line in lines:
        if line.strip() == start_marker:
            inside = True
            while out and out[-1].strip() == "":
                out.pop()
        if not inside:
            out.append(line)
        if inside and line.strip() == end_marker:
            inside = False
    code_path.write_text("".join(out), encoding="utf-8")


def find_node_line(code_path: Path, node_id: str) -> int | None:
    """Return the 1-based line of the NODE_START marker for node_id, or None."""
    if not code_path.exists():
        return None
    start_marker = _NODE_START.format(node_id=node_id)
    for i, line in enumerate(code_path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip() == start_marker:
            return i
    return None

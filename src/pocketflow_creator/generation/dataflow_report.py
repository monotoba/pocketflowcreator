"""Data flow report generator.

Analyses a GraphModel and produces a plain-text report showing which shared
store keys each node reads and writes, execution order, and a key lifecycle
table.
"""

from __future__ import annotations

from collections import deque

from pocketflow_creator.model.graph_model import GraphModel, NodeModel
from pocketflow_creator.model.node_type import NodeTypeDefinition


def _classify_store_keys(
    node: NodeModel,
    type_def: NodeTypeDefinition | None,
) -> tuple[list[str], list[str]]:
    """Return (read_keys, write_keys) resolved from node properties + type metadata."""
    if type_def is None:
        return [], []

    reads: list[str] = []
    writes: list[str] = []

    for prop_name, meta in type_def.properties.items():
        desc = (meta.get("description") or "").lower()
        if "shared store key" not in desc:
            continue
        val = str(node.properties.get(prop_name, meta.get("default", ""))).strip()
        if not val:
            continue
        # "to write …" or "key written …" → the node writes this key
        if "to write" in desc or "key written" in desc:
            writes.append(val)
        else:
            reads.append(val)

    return reads, writes


def _truncate(text: str, width: int) -> str:
    return text if len(text) <= width else text[: width - 1] + "…"


def generate_dataflow_report(
    graph: GraphModel,
    node_types: dict[str, NodeTypeDefinition],
) -> str:
    """Return a plain-text data flow report for *graph*."""

    lines: list[str] = []
    heading = f"DATA FLOW REPORT — {graph.title}"
    lines += [heading, "=" * len(heading), ""]

    if not graph.nodes:
        lines.append("(graph has no nodes)")
        return "\n".join(lines)

    # ── build index structures ────────────────────────────────────────────────
    node_index: dict[str, NodeModel] = {n.id: n for n in graph.nodes}
    out_edges: dict[str, list[tuple[str, str]]] = {n.id: [] for n in graph.nodes}
    for edge in graph.edges:
        out_edges.setdefault(edge.from_node, []).append((edge.action, edge.to_node))

    # BFS from start node → determines execution order and "reachable" set
    start = graph.start_node
    bfs_order: list[str] = []
    reachable: set[str] = set()
    if start and start in node_index:
        q: deque[str] = deque([start])
        reachable.add(start)
        while q:
            nid = q.popleft()
            bfs_order.append(nid)
            for _action, to_id in sorted(out_edges.get(nid, []), key=lambda x: x[0]):
                if to_id not in reachable and to_id in node_index:
                    reachable.add(to_id)
                    q.append(to_id)

    # unreachable nodes appended at the end
    for n in graph.nodes:
        if n.id not in reachable:
            bfs_order.append(n.id)

    # step number lookup (for edge annotations)
    step_of: dict[str, int] = {nid: i for i, nid in enumerate(bfs_order, 1)}

    # ── classify read / write keys for every node ────────────────────────────
    node_reads: dict[str, list[str]] = {}
    node_writes: dict[str, list[str]] = {}
    for n in graph.nodes:
        r, w = _classify_store_keys(n, node_types.get(n.type_id))
        node_reads[n.id] = r
        node_writes[n.id] = w

    # ── Section 1 — Node table ───────────────────────────────────────────────
    CW = (5, 26, 24, 22, 22)  # col widths: Step, Title, Type, Reads, Writes
    lines.append("NODE DATA FLOW")
    lines.append("─" * 80)
    hdr = f"{'Step':<{CW[0]}}  {'Node':<{CW[1]}}  {'Type':<{CW[2]}}  {'Reads (store keys)':<{CW[3]}}  Writes (store keys)"
    lines.append(hdr)
    lines.append("  ".join("─" * w for w in CW))

    for step, nid in enumerate(bfs_order, 1):
        node = node_index.get(nid)
        if not node:
            continue

        reads_str = ", ".join(node_reads[nid]) or "—"
        writes_str = ", ".join(node_writes[nid]) or "—"
        suffix = "" if nid in reachable else " [unreachable]"
        title_col = _truncate(node.title + suffix, CW[1])
        type_col = _truncate(node.type_id, CW[2])
        reads_col = _truncate(reads_str, CW[3])

        lines.append(f"{step:<{CW[0]}}  {title_col:<{CW[1]}}  {type_col:<{CW[2]}}  {reads_col:<{CW[3]}}  {writes_str}")

        # Show branch destinations when there is more than one outgoing action
        edges = sorted(out_edges.get(nid, []), key=lambda x: x[0])
        if len(edges) > 1:
            for i, (action, to_id) in enumerate(edges):
                to_node = node_index.get(to_id)
                to_title = to_node.title if to_node else to_id
                branch = "└" if i == len(edges) - 1 else "├"
                lines.append(f"       {branch}─[{action}]→ Step {step_of.get(to_id, '?')}: {to_title}")

    lines.append("")

    # ── Section 2 — Shared store key lifecycle ───────────────────────────────
    all_keys: set[str] = set()
    for nid in bfs_order:
        all_keys.update(node_reads.get(nid, []))
        all_keys.update(node_writes.get(nid, []))

    if all_keys:
        KW, WW = 22, 28
        lines.append("SHARED STORE KEY LIFECYCLE")
        lines.append("─" * 80)
        lines.append(f"{'Key':<{KW}}  {'Written by':<{WW}}  Read by")
        lines.append("  ".join(["─" * KW, "─" * WW, "─" * 26]))

        for key in sorted(all_keys):
            writers = [node_index[nid].title for nid in bfs_order if key in node_writes.get(nid, []) and nid in node_index]
            readers = [node_index[nid].title for nid in bfs_order if key in node_reads.get(nid, []) and nid in node_index]
            writers_str = _truncate(", ".join(writers) if writers else "(external)", WW)
            readers_str = ", ".join(readers) if readers else "(not consumed)"
            lines.append(f"{repr(key):<{KW}}  {writers_str:<{WW}}  {readers_str}")
        lines.append("")

    # ── Section 3 — Warnings ─────────────────────────────────────────────────
    notes: list[str] = []

    # Routing mismatches: edge action doesn't match any action the source node emits
    for nid in bfs_order:
        node = node_index.get(nid)
        if not node:
            continue
        declared = set(node.actions or ["default"])
        edges = out_edges.get(nid, [])
        mismatched = [
            (action, node_index[to_id].title if to_id in node_index else to_id)
            for action, to_id in edges
            if action not in declared and action != "default"
        ]
        # Also warn when ALL edges use "default" but node emits specific actions
        # (legacy graphs where edge actions were never set)
        all_default = edges and all(action == "default" for action, _ in edges)
        if all_default and declared != {"default"}:
            notes.append(
                f"  ⚠  {node.title!r}: all outgoing edges use action 'default' but this "
                f"node emits {sorted(declared)} — routing will use the fallback path. "
                f"Redraw edges from the correct action ports to fix routing."
            )
        elif mismatched:
            for action, to_title in mismatched:
                notes.append(f"  ⚠  {node.title!r} → {to_title!r}: edge action '{action}' is not in this node's actions {sorted(declared)}")

    for key in sorted(all_keys):
        writers = [nid for nid in bfs_order if key in node_writes.get(nid, [])]
        readers = [nid for nid in bfs_order if key in node_reads.get(nid, [])]

        if writers and not readers:
            wt = ", ".join(node_index[nid].title for nid in writers if nid in node_index)
            notes.append(f'  ! "{key}" written by {wt} — not consumed by any node')

        if not writers and readers:
            rt = ", ".join(node_index[nid].title for nid in readers if nid in node_index)
            notes.append(f'  ! "{key}" read by {rt} — not written by any node (must be supplied externally)')

        if len(writers) > 1:
            wt = ", ".join(node_index[nid].title for nid in writers if nid in node_index)
            notes.append(f'  ! "{key}" written by multiple nodes: {wt} — later write overwrites earlier')

    if notes:
        lines.append("DATA FLOW NOTES")
        lines.append("─" * 80)
        lines += notes
        lines.append("")

    return "\n".join(lines)

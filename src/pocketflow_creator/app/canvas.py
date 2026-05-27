from __future__ import annotations

import json
import math
import uuid
from pathlib import Path
from typing import Any

try:
    from PySide6.QtCore import QMimeData, QPointF, QRectF, QSize, Qt, Signal
    from PySide6.QtGui import (
        QBrush,
        QColor,
        QDrag,
        QFont,
        QIcon,
        QPainter,
        QPainterPath,
        QPainterPathStroker,
        QPen,
        QPixmap,
        QPolygonF,
    )
    from PySide6.QtWidgets import (
        QAbstractItemView,
        QGraphicsItem,
        QGraphicsLineItem,
        QGraphicsPathItem,
        QGraphicsScene,
        QGraphicsView,
        QListWidget,
        QListWidgetItem,
        QMenu,
        QStyleOptionGraphicsItem,
        QWidget,
    )
except Exception:  # pragma: no cover - permits import in non-GUI test environments
    def Signal(*a: Any, **kw: Any) -> Any:  # type: ignore[misc,no-redef]
        return None

    QGraphicsItem = object  # type: ignore[assignment,misc]
    QGraphicsLineItem = object  # type: ignore[assignment,misc]
    QGraphicsPathItem = object  # type: ignore[assignment,misc]
    QGraphicsScene = object  # type: ignore[assignment,misc]
    QGraphicsView = object  # type: ignore[assignment,misc]
    QListWidget = object  # type: ignore[assignment,misc]

from pocketflow_creator.model.graph_model import EdgeModel, GraphModel, NodeModel

_MIME_NODE_TYPE = "application/x-pocketflow-node-type"
_MIME_NODE_SNIPPET = "application/x-pocketflow-node-snippet"
_ROLE_SNIPPET = Qt.ItemDataRole(Qt.ItemDataRole.UserRole.value + 1)  # type: ignore[attr-defined]


def _load_snippets() -> list[dict[str, Any]]:
    snippets_path = Path(__file__).parent.parent / "node_snippets.yaml"
    if not snippets_path.exists():
        return []
    try:
        import yaml

        data = yaml.safe_load(snippets_path.read_text(encoding="utf-8")) or {}
        return list(data.get("snippets", []))
    except Exception:
        return []
_WIDTH = 160
_HEIGHT = 60       # minimum / single-action node height (kept for layout spacing)
_HEADER_H = 36     # title (18 px) + type badge (13 px) + 5 px gap before action rows
_PORT_ROW_H = 18   # height allocated per action row
_PORT_R = 5


def _node_height(n_actions: int) -> int:
    """Dynamic node height: grows with action count; single-action stays at _HEIGHT."""
    return max(_HEIGHT, _HEADER_H + max(1, n_actions) * _PORT_ROW_H)

# ── Node type visual metadata ─────────────────────────────────────────────
# (display_name, type_id, bg_color_hex)
_PALETTE_ITEMS_EX: list[tuple[str, str, str]] = [
    ("Start Node",        "start_node",       "#27ae60"),
    ("Stop Node",         "stop_node",        "#e74c3c"),
    ("Basic Node",        "basic_node",       "#2980b9"),
    ("Router Node",       "router_node",      "#e67e22"),
    ("LLM Prompt Node",   "llm_prompt_node",  "#8e44ad"),
    ("JSON LLM Node",     "json_llm_node",    "#16a085"),
    ("Classifier Node",   "classifier_node",  "#d35400"),
    ("Python Tool Node",  "python_tool_node", "#2c3e50"),
    ("File Reader Node",  "file_reader_node", "#1a6b3c"),
    ("File Writer Node",  "file_writer_node", "#1565c0"),
    ("Human Review Node", "human_review_node","#c0392b"),
    ("Human Input Node",         "human_input_node",         "#5c6bc0"),
    ("Batch Node",                "batch_node",                "#34495e"),
    ("Async Node",               "async_node",               "#6a1b9a"),
    ("Async Batch Node",         "async_batch_node",         "#00695c"),
    ("Async Parallel Batch Node","async_parallel_batch_node","#1a237e"),
    ("Agent Node",               "agent_node",               "#bf6900"),
    ("RAG Node",                 "rag_node",                 "#006064"),
    ("Judge Node",               "judge_node",               "#880e4f"),
    ("Subflow Node",             "subflow_node",             "#7f8c8d"),
]

_PALETTE_ITEMS: list[tuple[str, str]] = [
    (name, tid) for name, tid, _ in _PALETTE_ITEMS_EX
]

# Map type_id → bg hex (used by NodeItem paint and icon generator)
NODE_TYPE_COLOR: dict[str, str] = {tid: color for _, tid, color in _PALETTE_ITEMS_EX}

# ── Per-type icon drawing functions ──────────────────────────────────────────
# Each receives (painter, size) with antialiasing already enabled and the
# background already painted. Draw white shapes that communicate the node's purpose.

def _ico_start(p: QPainter, sz: float) -> None:
    """Right-pointing play triangle — universally means 'start/begin'."""
    m = sz * 0.22
    poly = QPolygonF([QPointF(m, m), QPointF(sz - m, sz / 2), QPointF(m, sz - m)])
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    p.drawPolygon(poly)


def _ico_stop(p: QPainter, sz: float) -> None:
    """Rounded stop square — universally means 'stop/end'."""
    m = sz * 0.27
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    p.drawRoundedRect(QRectF(m, m, sz - 2 * m, sz - 2 * m), sz * 0.1, sz * 0.1)


def _ico_gear(p: QPainter, sz: float) -> None:
    """Gear/cog — means 'process / compute'."""
    cx, cy = sz / 2, sz / 2
    outer_r = sz * 0.42
    inner_r = sz * 0.29
    hole_r = sz * 0.14
    n = 6  # teeth (6 reads cleanly at small sizes)
    pts: list[QPointF] = []
    for i in range(n * 2):
        angle = math.pi * i / n - math.pi / (n * 2)
        r = outer_r if i % 2 == 0 else inner_r
        pts.append(QPointF(cx + r * math.cos(angle), cy + r * math.sin(angle)))
    gear = QPainterPath()
    gear.addPolygon(QPolygonF(pts))
    gear.closeSubpath()
    hole = QPainterPath()
    hole.addEllipse(QPointF(cx, cy), hole_r, hole_r)
    p.setPen(Qt.PenStyle.NoPen)
    p.fillPath(gear.subtracted(hole), QColor("white"))


def _ico_fork(p: QPainter, sz: float) -> None:
    """Y-fork: one line in, two lines out — means 'route / branch'."""
    w = max(2.0, sz * 0.12)
    pen = QPen(
        QColor("white"), w, Qt.PenStyle.SolidLine,
        Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin,
    )
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    cx, cy = sz * 0.46, sz / 2
    # Input stem
    p.drawLine(QPointF(sz * 0.1, cy), QPointF(cx, cy))
    # Two output branches
    p.drawLine(QPointF(cx, cy), QPointF(sz * 0.9, sz * 0.26))
    p.drawLine(QPointF(cx, cy), QPointF(sz * 0.9, sz * 0.74))
    # Arrowhead tips (small V shapes)
    ah = sz * 0.1
    for ty in (sz * 0.26, sz * 0.74):
        p.drawLine(QPointF(sz * 0.9 - ah, ty - ah * 0.6), QPointF(sz * 0.9, ty))
        p.drawLine(QPointF(sz * 0.9 - ah, ty + ah * 0.6), QPointF(sz * 0.9, ty))


def _ico_chat_bubble(p: QPainter, sz: float) -> None:
    """Speech bubble — means 'language model / AI prompt'."""
    bx, by = sz * 0.08, sz * 0.08
    bw, bh = sz * 0.84, sz * 0.64
    r = sz * 0.16
    path = QPainterPath()
    path.addRoundedRect(QRectF(bx, by, bw, bh), r, r)
    # Triangular tail pointing down-left
    tail = QPolygonF([
        QPointF(sz * 0.18, by + bh),
        QPointF(sz * 0.09, sz * 0.94),
        QPointF(sz * 0.38, by + bh),
    ])
    path.addPolygon(tail)
    p.setPen(Qt.PenStyle.NoPen)
    p.fillPath(path, QColor("white"))


def _ico_json_llm(p: QPainter, sz: float, bg: QColor) -> None:
    """Chat bubble + '{}' label — means 'structured LLM output'."""
    _ico_chat_bubble(p, sz)
    font = QFont()
    font.setPixelSize(max(7, int(sz * 0.30)))
    font.setBold(True)
    p.setFont(font)
    p.setPen(QPen(bg))
    # Draw '{}' centred in the bubble body
    p.drawText(
        QRectF(sz * 0.08, sz * 0.08, sz * 0.84, sz * 0.64),
        Qt.AlignmentFlag.AlignCenter,
        "{}",
    )


def _ico_funnel(p: QPainter, sz: float) -> None:
    """Filter funnel — means 'classify / filter / categorise'."""
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    # Wide trapezoid body
    body = QPolygonF([
        QPointF(sz * 0.07, sz * 0.12),
        QPointF(sz * 0.93, sz * 0.12),
        QPointF(sz * 0.62, sz * 0.56),
        QPointF(sz * 0.38, sz * 0.56),
    ])
    p.drawPolygon(body)
    # Narrow outlet tube
    p.drawRect(QRectF(sz * 0.38, sz * 0.56, sz * 0.24, sz * 0.32))


def _ico_terminal(p: QPainter, sz: float) -> None:
    """'>_' terminal prompt — means 'execute code / Python tool'."""
    w = max(2.0, sz * 0.11)
    pen = QPen(
        QColor("white"), w, Qt.PenStyle.SolidLine,
        Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin,
    )
    p.setPen(pen)
    # '>' chevron on left half
    tip_x = sz * 0.46
    cy = sz / 2
    p.drawLine(QPointF(sz * 0.16, cy - sz * 0.22), QPointF(tip_x, cy))
    p.drawLine(QPointF(tip_x, cy), QPointF(sz * 0.16, cy + sz * 0.22))
    # '_' cursor on right half
    p.drawLine(QPointF(sz * 0.54, cy + sz * 0.22), QPointF(sz * 0.84, cy + sz * 0.22))


def _ico_document(p: QPainter, sz: float, bg: QColor) -> None:
    """Document with folded corner — means 'read / load a file'."""
    bx, by = sz * 0.16, sz * 0.07
    bw, bh = sz * 0.68, sz * 0.86
    fold = sz * 0.22
    # Page body (minus fold triangle)
    page = QPainterPath()
    page.moveTo(bx, by)
    page.lineTo(bx + bw - fold, by)
    page.lineTo(bx + bw, by + fold)
    page.lineTo(bx + bw, by + bh)
    page.lineTo(bx, by + bh)
    page.closeSubpath()
    p.setPen(Qt.PenStyle.NoPen)
    p.fillPath(page, QColor("white"))
    # Fold crease triangle in a slightly lighter bg shade
    crease = QPainterPath()
    crease.moveTo(bx + bw - fold, by)
    crease.lineTo(bx + bw - fold, by + fold)
    crease.lineTo(bx + bw, by + fold)
    crease.closeSubpath()
    p.fillPath(crease, bg.lighter(145))
    # Three content lines in bg colour
    p.setPen(QPen(bg, max(1, int(sz * 0.07))))
    x1, x2 = bx + sz * 0.08, bx + bw - sz * 0.1
    for i in range(3):
        ly = by + sz * 0.36 + i * sz * 0.17
        p.drawLine(QPointF(x1, ly), QPointF(x2, ly))


def _ico_file_writer(p: QPainter, sz: float, bg: QColor) -> None:
    """Document with pencil — means 'write / save to file'."""
    bx, by = sz * 0.16, sz * 0.07
    bw, bh = sz * 0.68, sz * 0.86
    fold = sz * 0.22
    # Page body
    page = QPainterPath()
    page.moveTo(bx, by)
    page.lineTo(bx + bw - fold, by)
    page.lineTo(bx + bw, by + fold)
    page.lineTo(bx + bw, by + bh)
    page.lineTo(bx, by + bh)
    page.closeSubpath()
    p.setPen(Qt.PenStyle.NoPen)
    p.fillPath(page, QColor("white"))
    # Fold crease
    crease = QPainterPath()
    crease.moveTo(bx + bw - fold, by)
    crease.lineTo(bx + bw - fold, by + fold)
    crease.lineTo(bx + bw, by + fold)
    crease.closeSubpath()
    p.fillPath(crease, bg.lighter(145))
    # One short line near top to suggest a document
    p.setPen(QPen(bg, max(1, int(sz * 0.07))))
    x2 = bx + bw - sz * 0.22
    p.drawLine(QPointF(bx + sz * 0.08, by + sz * 0.32), QPointF(x2, by + sz * 0.32))
    # Pencil: diagonal shaft (bg-dark colour, visible against white page)
    shaft_w = max(3, int(sz * 0.13))
    shaft_pen = QPen(
        bg.darker(110), shaft_w, Qt.PenStyle.SolidLine,
        Qt.PenCapStyle.FlatCap, Qt.PenJoinStyle.MiterJoin,
    )
    p.setPen(shaft_pen)
    # Shaft runs from upper-right toward lower-left
    p.drawLine(QPointF(sz * 0.60, sz * 0.44), QPointF(sz * 0.32, sz * 0.72))
    # Tip: filled triangle pointing to the write point
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(bg.darker(125)))
    tip = QPolygonF([
        QPointF(sz * 0.32, sz * 0.72),
        QPointF(sz * 0.25, sz * 0.65),
        QPointF(sz * 0.18, sz * 0.82),
    ])
    p.drawPolygon(tip)
    # Eraser cap: small rectangle at the top of the shaft
    p.setBrush(QBrush(QColor(220, 160, 160)))
    cap = QPolygonF([
        QPointF(sz * 0.60, sz * 0.44),
        QPointF(sz * 0.65, sz * 0.39),
        QPointF(sz * 0.70, sz * 0.44),
        QPointF(sz * 0.65, sz * 0.49),
    ])
    p.drawPolygon(cap)


def _ico_person(p: QPainter, sz: float) -> None:
    """Person silhouette — means 'human in the loop / review'."""
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    # Head
    p.drawEllipse(QPointF(sz / 2, sz * 0.30), sz * 0.17, sz * 0.17)
    # Shoulders: top half of a wide ellipse
    body = QPainterPath()
    body.addEllipse(QRectF(sz * 0.10, sz * 0.50, sz * 0.80, sz * 0.62))
    clip = QPainterPath()
    clip.addRect(QRectF(0, sz * 0.50, sz, sz * 0.50))
    p.fillPath(body.intersected(clip), QColor("white"))


def _ico_stack(p: QPainter, sz: float) -> None:
    """Three stacked offset pages — means 'batch / process many items'."""
    p.setPen(Qt.PenStyle.NoPen)
    rw, rh = sz * 0.58, sz * 0.52
    rx0, ry0 = sz * 0.14, sz * 0.26
    off = sz * 0.1
    for i, alpha in enumerate((110, 160, 255)):
        col = QColor(255, 255, 255, alpha)
        p.setBrush(QBrush(col))
        p.drawRoundedRect(
            QRectF(rx0 + (2 - i) * off, ry0 - (2 - i) * off, rw, rh),
            sz * 0.06, sz * 0.06,
        )


def _ico_subflow(p: QPainter, sz: float) -> None:
    """Box enclosing a mini-flowchart — means 'embedded / nested flow'."""
    # Outer dashed border
    pen = QPen(QColor("white"), max(1.5, sz * 0.08), Qt.PenStyle.DashLine)
    pen.setDashPattern([3, 2])
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    m = sz * 0.07
    p.drawRoundedRect(QRectF(m, m, sz - 2 * m, sz - 2 * m), sz * 0.12, sz * 0.12)
    # Inner mini-boxes and arrow
    solid = QPen(QColor("white"), max(1.0, sz * 0.06))
    p.setPen(solid)
    p.drawRect(QRectF(sz * 0.18, sz * 0.36, sz * 0.22, sz * 0.26))
    p.drawRect(QRectF(sz * 0.60, sz * 0.36, sz * 0.22, sz * 0.26))
    cy = sz * 0.49
    p.drawLine(QPointF(sz * 0.40, cy), QPointF(sz * 0.60, cy))
    ah = sz * 0.08
    p.drawLine(QPointF(sz * 0.60 - ah, cy - ah), QPointF(sz * 0.60, cy))
    p.drawLine(QPointF(sz * 0.60 - ah, cy + ah), QPointF(sz * 0.60, cy))


def _ico_lightning(p: QPainter, sz: float) -> None:
    """Lightning bolt — means 'async / non-blocking'."""
    pts = QPolygonF([
        QPointF(sz * 0.60, sz * 0.08),
        QPointF(sz * 0.32, sz * 0.52),
        QPointF(sz * 0.50, sz * 0.52),
        QPointF(sz * 0.40, sz * 0.92),
        QPointF(sz * 0.68, sz * 0.48),
        QPointF(sz * 0.50, sz * 0.48),
    ])
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    p.drawPolygon(pts)


def _ico_async_batch(p: QPainter, sz: float) -> None:
    """Stacked pages + lightning bolt — means 'async batch'."""
    p.setPen(Qt.PenStyle.NoPen)
    rw, rh = sz * 0.50, sz * 0.44
    rx0, ry0 = sz * 0.08, sz * 0.22
    off = sz * 0.09
    for i, alpha in enumerate((110, 160, 255)):
        p.setBrush(QBrush(QColor(255, 255, 255, alpha)))
        p.drawRoundedRect(
            QRectF(rx0 + (2 - i) * off, ry0 - (2 - i) * off, rw, rh),
            sz * 0.05, sz * 0.05,
        )
    # Lightning bolt in the bottom-right quadrant
    s = sz * 0.40
    bx, by = sz * 0.54, sz * 0.52
    bolt = QPolygonF([
        QPointF(bx + s * 0.60, by),
        QPointF(bx + s * 0.25, by + s * 0.48),
        QPointF(bx + s * 0.48, by + s * 0.48),
        QPointF(bx + s * 0.35, by + s * 1.00),
        QPointF(bx + s * 0.75, by + s * 0.52),
        QPointF(bx + s * 0.52, by + s * 0.52),
    ])
    p.setBrush(QBrush(QColor("white")))
    p.drawPolygon(bolt)


def _ico_parallel_arrows(p: QPainter, sz: float) -> None:
    """Three parallel right-pointing arrows — means 'concurrent async batch'."""
    w = max(2.0, sz * 0.10)
    pen = QPen(
        QColor("white"), w, Qt.PenStyle.SolidLine,
        Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin,
    )
    p.setPen(pen)
    ah = sz * 0.14
    for cy in (sz * 0.28, sz * 0.50, sz * 0.72):
        x1, x2 = sz * 0.12, sz * 0.82
        p.drawLine(QPointF(x1, cy), QPointF(x2, cy))
        p.drawLine(QPointF(x2 - ah, cy - ah * 0.65), QPointF(x2, cy))
        p.drawLine(QPointF(x2 - ah, cy + ah * 0.65), QPointF(x2, cy))


def _ico_agent(p: QPainter, sz: float) -> None:
    """Robot face — means 'autonomous AI agent'."""
    w = max(1.5, sz * 0.08)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    # Antenna
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawLine(QPointF(sz * 0.50, sz * 0.09), QPointF(sz * 0.50, sz * 0.24))
    p.setBrush(QBrush(QColor("white")))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QPointF(sz * 0.50, sz * 0.07), sz * 0.06, sz * 0.06)
    # Face outline
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QRectF(sz * 0.14, sz * 0.24, sz * 0.72, sz * 0.62),
                      sz * 0.12, sz * 0.12)
    # Eyes
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    p.drawEllipse(QPointF(sz * 0.35, sz * 0.48), sz * 0.09, sz * 0.09)
    p.drawEllipse(QPointF(sz * 0.65, sz * 0.48), sz * 0.09, sz * 0.09)
    # Mouth
    p.setPen(pen)
    p.drawLine(QPointF(sz * 0.32, sz * 0.72), QPointF(sz * 0.68, sz * 0.72))


def _ico_rag(p: QPainter, sz: float) -> None:
    """Magnifying glass with text lines — means 'retrieve and generate'."""
    w = max(2.0, sz * 0.11)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    cx, cy, r = sz * 0.40, sz * 0.38, sz * 0.26
    # Magnifying glass circle
    p.drawEllipse(QPointF(cx, cy), r, r)
    # Handle
    p.drawLine(QPointF(cx + r * 0.72, cy + r * 0.72), QPointF(sz * 0.88, sz * 0.88))
    # Text lines inside the lens
    lw = max(1.0, sz * 0.07)
    thin = QPen(QColor("white"), lw, Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(thin)
    for i in range(3):
        ly = cy - r * 0.32 + i * r * 0.34
        p.drawLine(QPointF(cx - r * 0.54, ly), QPointF(cx + r * 0.54, ly))


def _ico_scales(p: QPainter, sz: float) -> None:
    """Balance scales — means 'evaluate / judge / score'."""
    w = max(1.5, sz * 0.09)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    cx = sz * 0.50
    # Central post
    p.drawLine(QPointF(cx, sz * 0.14), QPointF(cx, sz * 0.84))
    # Horizontal beam
    p.drawLine(QPointF(sz * 0.14, sz * 0.26), QPointF(sz * 0.86, sz * 0.26))
    # Chains
    p.drawLine(QPointF(sz * 0.24, sz * 0.26), QPointF(sz * 0.24, sz * 0.58))
    p.drawLine(QPointF(sz * 0.76, sz * 0.26), QPointF(sz * 0.76, sz * 0.58))
    # Pans
    p.drawLine(QPointF(sz * 0.10, sz * 0.58), QPointF(sz * 0.38, sz * 0.58))
    p.drawLine(QPointF(sz * 0.62, sz * 0.58), QPointF(sz * 0.90, sz * 0.58))
    # Base
    p.drawLine(QPointF(sz * 0.34, sz * 0.84), QPointF(sz * 0.66, sz * 0.84))


def _ico_human_input(p: QPainter, sz: float) -> None:
    """Small person silhouette above a text-input rectangle — means 'keyboard input'."""
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    # Head (smaller than _ico_person so there's room for the input box)
    p.drawEllipse(QPointF(sz / 2, sz * 0.22), sz * 0.13, sz * 0.13)
    # Shoulders: upper half of a wide ellipse
    body = QPainterPath()
    body.addEllipse(QRectF(sz * 0.22, sz * 0.36, sz * 0.56, sz * 0.34))
    clip = QPainterPath()
    clip.addRect(QRectF(0, sz * 0.36, sz, sz * 0.34))
    p.fillPath(body.intersected(clip), QColor("white"))
    # Input box at the bottom
    w = max(1.5, sz * 0.08)
    pen = QPen(
        QColor("white"), w, Qt.PenStyle.SolidLine,
        Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin,
    )
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    bx, by = sz * 0.10, sz * 0.72
    bw, bh = sz * 0.80, sz * 0.20
    p.drawRoundedRect(QRectF(bx, by, bw, bh), sz * 0.05, sz * 0.05)
    # Text stub and cursor inside the box
    cy = by + bh / 2
    p.drawLine(QPointF(bx + sz * 0.07, cy), QPointF(bx + sz * 0.30, cy))
    p.drawLine(
        QPointF(bx + sz * 0.30, by + sz * 0.04),
        QPointF(bx + sz * 0.30, by + bh - sz * 0.04),
    )


# Dispatch map: type_id → drawing function
_ICON_DRAW: dict[str, Any] = {
    "start_node":       _ico_start,
    "stop_node":        _ico_stop,
    "basic_node":       _ico_gear,
    "router_node":      _ico_fork,
    "llm_prompt_node":  _ico_chat_bubble,
    "json_llm_node":    None,  # handled specially (needs bg colour)
    "classifier_node":  _ico_funnel,
    "python_tool_node": _ico_terminal,
    "file_reader_node": None,  # handled specially (needs bg colour)
    "file_writer_node": None,  # handled specially (needs bg colour)
    "human_review_node":         _ico_person,
    "batch_node":                _ico_stack,
    "async_node":                _ico_lightning,
    "async_batch_node":          _ico_async_batch,
    "async_parallel_batch_node": _ico_parallel_arrows,
    "agent_node":                _ico_agent,
    "rag_node":                  _ico_rag,
    "judge_node":                _ico_scales,
    "subflow_node":              _ico_subflow,
    "human_input_node":          _ico_human_input,
}


def _paint_node_pixmap(type_id: str, size: int, bg: QColor) -> QPixmap:
    """Paint one icon pixmap with the given background colour."""
    px = QPixmap(size, size)
    px.fill(QColor("transparent"))
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Rounded-rect background
    p.setBrush(QBrush(bg))
    p.setPen(QPen(bg.darker(130), 1))
    r = size * 0.22
    p.drawRoundedRect(1, 1, size - 2, size - 2, r, r)

    # Type-specific shape
    draw_fn = _ICON_DRAW.get(type_id)
    if draw_fn is not None:
        draw_fn(p, float(size))
    elif type_id == "json_llm_node":
        _ico_json_llm(p, float(size), bg)
    elif type_id == "file_reader_node":
        _ico_document(p, float(size), bg)
    elif type_id == "file_writer_node":
        _ico_file_writer(p, float(size), bg)
    else:
        font = QFont()
        font.setPixelSize(max(8, int(size * 0.38)))
        font.setBold(True)
        p.setFont(font)
        p.setPen(QPen(QColor("white")))
        initials = "".join(w[0].upper() for w in type_id.split("_") if w)[:2]
        p.drawText(QRectF(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, initials)

    p.end()
    return px


def make_node_icon(type_id: str, size: int = 32) -> QIcon:
    """Return a QIcon with Normal, Active (hover), and pressed pixmaps."""
    base = QColor(NODE_TYPE_COLOR.get(type_id, "#555555"))

    icon = QIcon()
    # Normal — base colour
    icon.addPixmap(_paint_node_pixmap(type_id, size, base), QIcon.Mode.Normal)
    # Active / hover — noticeably lighter background
    icon.addPixmap(
        _paint_node_pixmap(type_id, size, base.lighter(150)), QIcon.Mode.Active
    )
    # Selected / pressed — brightest, used on click
    icon.addPixmap(
        _paint_node_pixmap(type_id, size, base.lighter(180)), QIcon.Mode.Selected
    )
    return icon


class NodeItem(QGraphicsItem):
    def __init__(self, node: NodeModel, parent: QGraphicsItem | None = None) -> None:
        super().__init__(parent)
        self._node = node
        self._has_error = False
        self._has_breakpoint = False
        self._is_start = False
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setPos(node.position["x"], node.position["y"])
        self.setToolTip(node.id)

    @property
    def node(self) -> NodeModel:
        return self._node

    def set_has_error(self, has_error: bool) -> None:
        self._has_error = has_error
        self.update()

    def set_breakpoint(self, active: bool) -> None:
        self._has_breakpoint = active
        self.update()

    def set_is_start(self, active: bool) -> None:
        self._is_start = active
        self.update()

    def boundingRect(self) -> QRectF:
        h = _node_height(len(self._node.actions or []))
        return QRectF(-_PORT_R, 0, _WIDTH + 2 * _PORT_R, h)

    @property
    def height(self) -> int:
        return _node_height(len(self._node.actions or []))

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        scene = self.scene()
        dark = scene._dark if hasattr(scene, "_dark") else True  # type: ignore[union-attr]
        colors = _DARK_COLORS if dark else _LIGHT_COLORS

        actions = self._node.actions or ["default"]
        h = _node_height(len(actions))

        body = QRectF(0, 0, _WIDTH, h)
        path = QPainterPath()
        path.addRoundedRect(body, 8, 8)
        painter.fillPath(path, QBrush(QColor(colors["node_bg"])))

        if self._has_error:
            border_pen = QPen(QColor(colors["border_error"]), 2)
        elif self.isSelected():
            border_pen = QPen(QColor(colors["border_select"]), 2)
        else:
            border_pen = QPen(QColor(colors["border_normal"]), 1)
        painter.setPen(border_pen)
        painter.drawPath(path)

        # ── Header: title (top-aligned) + type badge ────────────────────────
        base_font = painter.font()
        title_font = QFont(base_font)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(QPen(QColor(colors["title"])))
        painter.drawText(
            QRectF(12, 4, _WIDTH - 24, 18), Qt.AlignmentFlag.AlignVCenter, self._node.title
        )

        badge_font = QFont(base_font)
        badge_font.setPointSize(max(base_font.pointSize() - 1, 7))
        painter.setFont(badge_font)
        painter.setPen(QPen(QColor(colors["badge"])))
        painter.drawText(
            QRectF(12, 21, _WIDTH - 24, 13), Qt.AlignmentFlag.AlignVCenter, self._node.type_id
        )

        # Separator between header and action area (only for multi-action nodes)
        if len(actions) > 1:
            sep_pen = QPen(QColor(colors["border_normal"]), 1)
            sep_pen.setStyle(Qt.PenStyle.SolidLine)
            painter.setPen(sep_pen)
            painter.drawLine(QPointF(6, _HEADER_H), QPointF(_WIDTH - 6, _HEADER_H))

        # ── Input port (left side, vertically centred on the node) ──────────
        painter.setPen(QPen(QColor(colors["port_outline"]), 1))
        painter.setBrush(QBrush(QColor(colors["port_fill"])))
        painter.drawEllipse(QPointF(0, h / 2), _PORT_R, _PORT_R)

        # ── Action ports (right side, one row per action below the header) ──
        port_font = QFont(base_font)
        port_font.setPointSize(max(base_font.pointSize() - 2, 6))

        # Input port label — show input_key property (fallback "in")
        in_label = str(self._node.properties.get("input_key", "")).strip() or "in"
        painter.setFont(port_font)
        painter.setPen(QPen(QColor(colors["badge"])))
        painter.drawText(
            QRectF(_PORT_R + 4, h / 2 + _PORT_R, _WIDTH // 2 - 8, 14),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            in_label,
        )
        for action, y in self._action_port_ys(actions):
            painter.setPen(QPen(QColor(colors["port_outline"]), 1))
            painter.setBrush(QBrush(QColor(colors["port_fill"])))
            painter.drawEllipse(QPointF(_WIDTH, y), _PORT_R, _PORT_R)
            # Label: right-aligned inside the action row, clear of the port circle
            painter.setPen(QPen(QColor(colors["badge"])))
            painter.drawText(
                QRectF(8, y - 7, _WIDTH - 16, 14),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                action,
            )

        # ── Decorators ───────────────────────────────────────────────────────
        if self._has_breakpoint:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(colors["breakpoint"])))
            painter.drawEllipse(QPointF(_WIDTH - 10, 10), 5, 5)

        if self._is_start:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#44bb44")))
            triangle = QPolygonF([
                QPointF(8, h / 2 - 6),
                QPointF(8, h / 2 + 6),
                QPointF(18, h / 2),
            ])
            painter.drawPolygon(triangle)

        if self._node.type_id == "stop_node":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#dd4444")))
            sq = 10
            painter.drawRect(
                int(_WIDTH - 8 - sq), int(h / 2 - sq / 2), sq, sq
            )

    @staticmethod
    def _action_port_ys(actions: list[str]) -> list[tuple[str, float]]:
        """Return [(action_name, local_y), …] placed in the action area below the header."""
        if not actions:
            actions = ["default"]
        n = len(actions)
        h = _node_height(n)
        row_h = (h - _HEADER_H) / n
        return [(actions[i], _HEADER_H + i * row_h + row_h / 2) for i in range(n)]

    def action_port_scene_pos(self, action: str) -> QPointF:
        """Return the scene position of the port for *action*."""
        actions = self._node.actions or ["default"]
        for a, y in self._action_port_ys(actions):
            if a == action:
                return self.mapToScene(QPointF(_WIDTH, y))
        # Fallback: first action port
        _, y = self._action_port_ys(actions)[0]
        return self.mapToScene(QPointF(_WIDTH, y))

    def port_scene_pos(self) -> QPointF:
        """First action port position (backward-compat for single-action nodes)."""
        actions = self._node.actions or ["default"]
        _, y = self._action_port_ys(actions)[0]
        return self.mapToScene(QPointF(_WIDTH, y))

    def input_port_scene_pos(self) -> QPointF:
        return self.mapToScene(QPointF(0, self.height / 2))

    def mouseDoubleClickEvent(self, event: Any) -> None:
        scene = self.scene()
        if isinstance(scene, GraphScene):
            scene.node_item_double_clicked.emit(self)
        event.accept()

    def contextMenuEvent(self, event: Any) -> None:
        scene = self.scene()
        if not isinstance(scene, GraphScene):
            return
        menu = QMenu()
        start_text = "Set as Start Node" if not self._is_start else "Already Start Node"
        act = menu.addAction(start_text)
        if self._is_start:
            act.setEnabled(False)
        chosen = menu.exec(event.screenPos())
        if chosen is act and not self._is_start:
            scene.set_start_node_requested.emit(self)
        event.accept()

    def mousePressEvent(self, event: Any) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = self.pos()
            scene = self.scene()
            if isinstance(scene, GraphScene):
                scene.node_drag_started.emit(self._node.id)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: Any) -> None:
        super().mouseReleaseEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            start = getattr(self, "_drag_start_pos", None)
            if start is not None and start != self.pos():
                scene = self.scene()
                if isinstance(scene, GraphScene):
                    scene.node_move_finished.emit(self._node.id)
            self._drag_start_pos = None

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            p = self.pos()
            self.node.position["x"] = p.x()
            self.node.position["y"] = p.y()
            scene = self.scene()
            if isinstance(scene, GraphScene):
                scene.update_edges()
        return super().itemChange(change, value)


class EdgeItem(QGraphicsPathItem):
    def __init__(
        self,
        edge: EdgeModel,
        src: NodeItem,
        tgt: NodeItem,
        parent: QGraphicsItem | None = None,
    ) -> None:
        super().__init__(parent)
        self._edge = edge
        self._src = src
        self._tgt = tgt
        self.setPen(QPen(QColor("#888888"), 1.5))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.update_position()

    @property
    def edge(self) -> EdgeModel:
        return self._edge

    def shape(self) -> QPainterPath:
        stroker = QPainterPathStroker()
        stroker.setWidth(12.0)
        return stroker.createStroke(self.path())

    def update_position(self, connector_style: str = "straight") -> None:
        src_pos = self._src.action_port_scene_pos(self._edge.action)
        tgt_pos = self._tgt.input_port_scene_pos()
        path = QPainterPath()
        path.moveTo(src_pos)
        if connector_style == "curved":
            mid_x = (src_pos.x() + tgt_pos.x()) / 2
            path.quadTo(QPointF(mid_x, src_pos.y()), tgt_pos)
        elif connector_style == "orthogonal":
            mid_x = (src_pos.x() + tgt_pos.x()) / 2
            path.lineTo(QPointF(mid_x, src_pos.y()))
            path.lineTo(QPointF(mid_x, tgt_pos.y()))
            path.lineTo(tgt_pos)
        else:
            path.lineTo(tgt_pos)
        self.setPath(path)


_DARK_COLORS = {
    "node_bg": "#2a2a2a",
    "border_error": "#e05555",
    "border_select": "#4a9eff",
    "border_normal": "#555555",
    "title": "#ffffff",
    "badge": "#aaaaaa",
    "port_outline": "#888888",
    "port_fill": "#555555",
    "breakpoint": "#e05555",
    "edge": "#888888",
}

_LIGHT_COLORS = {
    "node_bg": "#f5f5f5",
    "border_error": "#cc3333",
    "border_select": "#0077cc",
    "border_normal": "#999999",
    "title": "#111111",
    "badge": "#555555",
    "port_outline": "#555555",
    "port_fill": "#888888",
    "breakpoint": "#cc3333",
    "edge": "#555555",
}


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


class GraphView(QGraphicsView):
    zoom_changed = Signal(float)  # emits current scale factor (1.0 = 100%)

    def __init__(self, scene: GraphScene, parent: QWidget | None = None) -> None:
        super().__init__(scene, parent)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setAcceptDrops(True)
        self._pan_active = False
        self._pan_start = QPointF()
        self._edge_src: NodeItem | None = None
        self._edge_src_action: str = "default"
        self._edge_rubber: QGraphicsLineItem | None = None

    def _node_at_action_port(
        self, scene_pos: QPointF
    ) -> tuple[NodeItem, str] | None:
        """Return (NodeItem, action_name) if scene_pos is near any action port."""
        scene = self.scene()
        if not isinstance(scene, GraphScene):
            return None
        hit_r = _PORT_R * 2.5
        for item in scene._node_items.values():
            actions = item.node.actions or ["default"]
            for action, y in NodeItem._action_port_ys(actions):
                port = item.mapToScene(QPointF(_WIDTH, y))
                dx = scene_pos.x() - port.x()
                dy = scene_pos.y() - port.y()
                if dx * dx + dy * dy <= hit_r * hit_r:
                    return item, action
        return None

    def _node_at_input_port(self, scene_pos: QPointF) -> NodeItem | None:
        """Return NodeItem near input port, with generous hit-radius + body fallback."""
        scene = self.scene()
        if not isinstance(scene, GraphScene):
            return None
        hit_r = _PORT_R * 4.0
        for item in scene._node_items.values():
            port = item.input_port_scene_pos()
            dx = scene_pos.x() - port.x()
            dy = scene_pos.y() - port.y()
            if dx * dx + dy * dy <= hit_r * hit_r:
                return item
        for item in scene._node_items.values():
            local = item.mapFromScene(scene_pos)
            if 0 <= local.y() <= item.height and -_PORT_R <= local.x() <= _WIDTH:
                return item
        return None

    def zoom_in(self) -> None:
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.scale(1.2, 1.2)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.zoom_changed.emit(self.transform().m11())

    def zoom_out(self) -> None:
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.scale(1 / 1.2, 1 / 1.2)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.zoom_changed.emit(self.transform().m11())

    def zoom_to_item(self, item: QGraphicsItem) -> None:
        rect = item.mapRectToScene(item.boundingRect()).adjusted(-20, -20, 20, 20)
        self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
        self.zoom_changed.emit(self.transform().m11())

    def wheelEvent(self, event: Any) -> None:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
            self.scale(factor, factor)
            self.zoom_changed.emit(self.transform().m11())
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event: Any) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._pan_active = True
            self._pan_start = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.position().toPoint())
            hit = self._node_at_action_port(scene_pos)
            if hit is not None:
                src, action = hit
                self._edge_src = src
                self._edge_src_action = action
                sp = src.action_port_scene_pos(action)
                rubber = QGraphicsLineItem(sp.x(), sp.y(), scene_pos.x(), scene_pos.y())
                rubber.setPen(QPen(QColor("#4a9eff"), 1.5, Qt.PenStyle.DashLine))
                rubber.setZValue(-1)
                self.scene().addItem(rubber)
                self._edge_rubber = rubber
                self.setCursor(Qt.CursorShape.CrossCursor)
                event.accept()
                return
        super().mousePressEvent(event)
        self.setFocus()  # ensure Delete key reaches the scene

    def mouseMoveEvent(self, event: Any) -> None:
        if self._pan_active:
            delta = event.position() - self._pan_start
            self._pan_start = event.position()
            self.horizontalScrollBar().setValue(
                int(self.horizontalScrollBar().value() - delta.x())
            )
            self.verticalScrollBar().setValue(
                int(self.verticalScrollBar().value() - delta.y())
            )
            event.accept()
        elif self._edge_src is not None and self._edge_rubber is not None:
            scene_pos = self.mapToScene(event.position().toPoint())
            sp = self._edge_src.action_port_scene_pos(self._edge_src_action)
            self._edge_rubber.setLine(sp.x(), sp.y(), scene_pos.x(), scene_pos.y())
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: Any) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._pan_active = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        elif event.button() == Qt.MouseButton.LeftButton and self._edge_src is not None:
            src = self._edge_src
            self._edge_src = None
            scene = self.scene()
            if self._edge_rubber is not None:
                scene.removeItem(self._edge_rubber)
                self._edge_rubber = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
            # Use Qt's own spatial query — guaranteed correct under any zoom/pan/transform
            scene_pos = self.mapToScene(event.position().toPoint())
            tgt: NodeItem | None = None
            for item in scene.items(scene_pos):
                if isinstance(item, NodeItem) and item is not src:
                    tgt = item
                    break
            if tgt is not None and isinstance(scene, GraphScene):
                scene.edge_creation_requested.emit(src, tgt, self._edge_src_action)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def zoom_to_fit(self) -> None:
        scene = self.scene()
        if scene and scene.items():
            self.fitInView(scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
        else:
            self.resetTransform()
        self.zoom_changed.emit(self.transform().m11())

    def _has_node_mime(self, event: Any) -> bool:
        return event.mimeData().hasFormat(_MIME_NODE_TYPE) or event.mimeData().hasFormat(
            _MIME_NODE_SNIPPET
        )

    def dragEnterEvent(self, event: Any) -> None:
        if self._has_node_mime(event):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: Any) -> None:
        if self._has_node_mime(event):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: Any) -> None:
        scene = self.scene()
        if not isinstance(scene, GraphScene):
            event.ignore()
            return
        pos = self.mapToScene(event.position().toPoint())
        mime = event.mimeData()
        if mime.hasFormat(_MIME_NODE_SNIPPET):
            raw = bytes(mime.data(_MIME_NODE_SNIPPET)).decode()
            snippet: dict[str, Any] = json.loads(raw)
            scene.create_node_at(
                snippet.get("type_id", "basic_node"),
                pos,
                title=snippet.get("title"),
                actions=snippet.get("actions"),
                properties=snippet.get("properties"),
            )
        elif mime.hasFormat(_MIME_NODE_TYPE):
            type_id = bytes(mime.data(_MIME_NODE_TYPE)).decode()
            scene.create_node_at(type_id, pos)
        else:
            event.ignore()
            return
        event.acceptProposedAction()


class PaletteWidget(QListWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)
        self.setIconSize(QSize(28, 28))
        for display_name, type_id in _PALETTE_ITEMS:
            item = QListWidgetItem(make_node_icon(type_id, 28), display_name)
            item.setData(Qt.ItemDataRole.UserRole, type_id)
            self.addItem(item)

        snippets = _load_snippets()
        if snippets:
            sep = QListWidgetItem("— Snippets —")
            sep.setFlags(sep.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            self.addItem(sep)
            for snippet in snippets:
                sitem = QListWidgetItem(str(snippet.get("display_name", snippet.get("type_id"))))
                sitem.setData(Qt.ItemDataRole.UserRole, snippet.get("type_id", "basic_node"))
                sitem.setData(_ROLE_SNIPPET, snippet)
                self.addItem(sitem)

    def startDrag(self, supported_actions: Any) -> None:
        current = self.currentItem()
        if current is None:
            return
        snippet: dict[str, Any] | None = current.data(_ROLE_SNIPPET)
        mime = QMimeData()
        if snippet is not None:
            mime.setData(_MIME_NODE_SNIPPET, json.dumps(snippet).encode())
        else:
            type_id: str = current.data(Qt.ItemDataRole.UserRole)
            mime.setData(_MIME_NODE_TYPE, type_id.encode())
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.CopyAction)

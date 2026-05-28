"""Icon drawing functions and node-type visual metadata.

Each ``_ico_*`` function receives a QPainter and a size (float) with
antialiasing already enabled and the background already filled.  They draw
white shapes that communicate the node's purpose.
"""
from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from PySide6.QtCore import QPointF, QRectF, Qt
    from PySide6.QtGui import (
        QBrush,
        QColor,
        QFont,
        QIcon,
        QPainter,
        QPainterPath,
        QPen,
        QPixmap,
        QPolygonF,
    )
else:
    try:
        from PySide6.QtCore import QPointF, QRectF, Qt
        from PySide6.QtGui import (
            QBrush,
            QColor,
            QFont,
            QIcon,
            QPainter,
            QPainterPath,
            QPen,
            QPixmap,
            QPolygonF,
        )
    except ImportError:  # pragma: no cover
        pass  # Icon functions are never called without a running Qt instance.


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

# Map type_id → bg hex (used by NodeItem paint and icon generator)
NODE_TYPE_COLOR: dict[str, str] = {tid: color for _, tid, color in _PALETTE_ITEMS_EX}


# ── Per-type icon drawing functions ──────────────────────────────────────────

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
# None entries are handled specially in _paint_node_pixmap (they need the bg colour).
_ICON_DRAW: dict[str, Any] = {
    "start_node":       _ico_start,
    "stop_node":        _ico_stop,
    "basic_node":       _ico_gear,
    "router_node":      _ico_fork,
    "llm_prompt_node":  _ico_chat_bubble,
    "json_llm_node":    None,  # needs bg colour
    "classifier_node":  _ico_funnel,
    "python_tool_node": _ico_terminal,
    "file_reader_node": None,  # needs bg colour
    "file_writer_node": None,  # needs bg colour
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

"""Icon drawing functions and node-type visual metadata.

Each ``_ico_*`` function has the uniform signature
``(p: QPainter, sz: float, bg: QColor) -> None``.
Antialiasing is already enabled and the background already filled before
the function is called.  Functions that don't use ``bg`` accept it and
ignore it so that ``_ICON_DRAW`` can dispatch all 20 uniformly.
"""
from __future__ import annotations

import math
from collections.abc import Callable
from typing import TYPE_CHECKING

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
    # ── AI / Reasoning ────────────────────────────────────────────────────────
    ("Chain of Thought Node",    "chain_of_thought_node",    "#4527a0"),
    ("Majority Vote Node",       "majority_vote_node",       "#00796b"),
    ("Supervisor Node",          "supervisor_node",          "#2e7d32"),
    ("Debate Advocate Node",     "debate_advocate_node",     "#e64a19"),
    ("Debate Judge Node",        "debate_judge_node",        "#6d4c41"),
    # ── Web / Search ──────────────────────────────────────────────────────────
    ("Web Search Node",          "web_search_node",          "#0277bd"),
    ("Web Scrape Node",          "web_scrape_node",          "#01579b"),
    ("API Call Node",            "api_call_node",            "#311b92"),
    # ── Data / Vector / Embeddings ────────────────────────────────────────────
    ("Text Chunk Node",          "text_chunk_node",          "#558b2f"),
    ("Embed Node",               "embed_node",               "#e65100"),
    ("Vector Index Node",        "vector_index_node",        "#283593"),
    ("Vector Retrieve Node",     "vector_retrieve_node",     "#0d47a1"),
    # ── Database / SQL ────────────────────────────────────────────────────────
    ("DB Schema Node",           "db_schema_node",           "#4e342e"),
    ("NL to SQL Node",           "nl_to_sql_node",           "#827717"),
    ("SQL Execute Node",         "sql_execute_node",         "#1b5e20"),
    # ── Voice / Audio ─────────────────────────────────────────────────────────
    ("Speech to Text Node",      "speech_to_text_node",      "#ad1457"),
    ("Text to Speech Node",      "text_to_speech_node",      "#c2185b"),
    # ── Document / Vision ─────────────────────────────────────────────────────
    ("PDF Extract Node",         "pdf_extract_node",         "#0e4757"),
    ("Image Vision Node",        "image_vision_node",        "#0097a7"),
    ("Data Validate Node",       "data_validate_node",       "#b71c1c"),
    # ── Code / Execution ──────────────────────────────────────────────────────
    ("Code Gen Node",            "code_gen_node",            "#33691e"),
    ("Code Exec Node",           "code_exec_node",           "#004d40"),
    ("Test Gen Node",            "test_gen_node",            "#388e3c"),
    # ── Data Processing ───────────────────────────────────────────────────────
    ("Map Node",                 "map_node",                 "#455a64"),
    ("Reduce Node",              "reduce_node",              "#37474f"),
    ("Condition Node",           "condition_node",           "#ff8f00"),
    ("Loop Counter Node",        "loop_counter_node",        "#5d4037"),
    ("Transform Node",           "transform_node",           "#546e7a"),
    ("Merge Node",               "merge_node",               "#004d61"),
    # ── Calendar ──────────────────────────────────────────────────────────────
    ("Calendar Read Node",       "calendar_read_node",       "#1976d2"),
    ("Calendar Write Node",      "calendar_write_node",      "#1e88e5"),
    # ── MCP / Agent Protocol ──────────────────────────────────────────────────
    ("MCP Tool Node",            "mcp_tool_node",            "#4a148c"),
    ("A2A Send Node",            "a2a_send_node",            "#7b1fa2"),
    ("A2A Receive Node",         "a2a_receive_node",         "#8e24aa"),
    # ── Observability / Utility ───────────────────────────────────────────────
    ("Log Node",                 "log_node",                 "#607d8b"),
    ("Timer Node",               "timer_node",               "#00897b"),
    ("Cache Node",               "cache_node",               "#bf360c"),
    ("Trace Node",               "trace_node",               "#263238"),
    # ── Data Structures / Memory ──────────────────────────────────────────────
    ("Registry Node",            "registry_node",            "#c62828"),
    ("Stack Push Node",          "stack_push_node",          "#8d6e63"),
    ("Stack Pop Node",           "stack_pop_node",           "#795548"),
    ("Queue Enqueue Node",       "queue_enqueue_node",       "#26a69a"),
    ("Queue Dequeue Node",       "queue_dequeue_node",       "#009688"),
    ("Local Memory Node",        "local_memory_node",        "#3949ab"),
    # ── System / Shell / Hardware ─────────────────────────────────────────────
    ("Shell Command Node",       "shell_command_node",       "#004d00"),
    ("TTY Serial Node",          "tty_serial_node",          "#f57f17"),
    ("Spreadsheet Node",         "spreadsheet_node",         "#1b7a1b"),
    # ── Networking / Sockets ──────────────────────────────────────────────────
    ("Socket Node",              "socket_node",              "#00838f"),
    ("WebSocket Node",           "websocket_node",           "#00acc1"),
    ("Webhook Trigger Node",     "webhook_trigger_node",     "#6200ea"),
    # ── AI / LLM Utilities ────────────────────────────────────────────────────
    ("Context Compact Node",     "context_compact_node",     "#4a0072"),
    ("Conversation History Node","conversation_history_node","#3f51b5"),
    # ── Text / Data Processing ────────────────────────────────────────────────
    ("Regex Node",               "regex_node",               "#d84315"),
    ("Template Render Node",     "template_render_node",     "#f9a825"),
    ("JSON Parse Node",          "json_parse_node",          "#00695c"),
    ("List Operations Node",     "list_ops_node",            "#424242"),
    ("String Operations Node",   "string_ops_node",          "#3e2723"),
    # ── Resilience / Flow Utilities ───────────────────────────────────────────
    ("Retry Node",               "retry_node",               "#e53935"),
    ("Rate Limiter Node",        "rate_limiter_node",        "#00600f"),
    # ── Messaging / Notifications ─────────────────────────────────────────────
    ("Email Send Node",          "email_send_node",          "#d50000"),
    ("Email Read Node",          "email_read_node",          "#c51162"),
    ("Notification Node",        "notification_node",        "#ff6f00"),
    # ── Security / Configuration ──────────────────────────────────────────────
    ("Secret Node",              "secret_node",              "#212121"),
]

# Map type_id → bg hex (used by NodeItem paint and icon generator)
NODE_TYPE_COLOR: dict[str, str] = {tid: color for _, tid, color in _PALETTE_ITEMS_EX}


# ── Per-type icon drawing functions ──────────────────────────────────────────
# All functions share the uniform signature (p, sz, bg).
# Functions that do not use bg accept and ignore it.

def _ico_start(p: QPainter, sz: float, bg: QColor) -> None:
    """Right-pointing play triangle — universally means 'start/begin'."""
    m = sz * 0.22
    poly = QPolygonF([QPointF(m, m), QPointF(sz - m, sz / 2), QPointF(m, sz - m)])
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    p.drawPolygon(poly)


def _ico_stop(p: QPainter, sz: float, bg: QColor) -> None:
    """Rounded stop square — universally means 'stop/end'."""
    m = sz * 0.27
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    p.drawRoundedRect(QRectF(m, m, sz - 2 * m, sz - 2 * m), sz * 0.1, sz * 0.1)


def _ico_gear(p: QPainter, sz: float, bg: QColor) -> None:
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


def _ico_fork(p: QPainter, sz: float, bg: QColor) -> None:
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


def _ico_chat_bubble(p: QPainter, sz: float, bg: QColor) -> None:
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
    _ico_chat_bubble(p, sz, bg)
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


def _ico_funnel(p: QPainter, sz: float, bg: QColor) -> None:
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


def _ico_terminal(p: QPainter, sz: float, bg: QColor) -> None:
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


def _ico_person(p: QPainter, sz: float, bg: QColor) -> None:
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


def _ico_stack(p: QPainter, sz: float, bg: QColor) -> None:
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


def _ico_subflow(p: QPainter, sz: float, bg: QColor) -> None:
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


def _ico_lightning(p: QPainter, sz: float, bg: QColor) -> None:
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


def _ico_async_batch(p: QPainter, sz: float, bg: QColor) -> None:
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


def _ico_parallel_arrows(p: QPainter, sz: float, bg: QColor) -> None:
    """Three parallel arrows + lightning bolt — means 'concurrent async batch'."""
    w = max(2.0, sz * 0.10)
    pen = QPen(
        QColor("white"), w, Qt.PenStyle.SolidLine,
        Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin,
    )
    p.setPen(pen)
    # Arrows shortened to leave room for the bolt on the right
    ah = sz * 0.11
    for cy in (sz * 0.28, sz * 0.50, sz * 0.72):
        x1, x2 = sz * 0.10, sz * 0.58
        p.drawLine(QPointF(x1, cy), QPointF(x2, cy))
        p.drawLine(QPointF(x2 - ah, cy - ah * 0.65), QPointF(x2, cy))
        p.drawLine(QPointF(x2 - ah, cy + ah * 0.65), QPointF(x2, cy))
    # Lightning bolt in the bottom-right — same proportions as _ico_async_batch
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    s = sz * 0.34
    bx, by = sz * 0.60, sz * 0.52
    bolt = QPolygonF([
        QPointF(bx + s * 0.60, by),
        QPointF(bx + s * 0.25, by + s * 0.48),
        QPointF(bx + s * 0.48, by + s * 0.48),
        QPointF(bx + s * 0.35, by + s * 1.00),
        QPointF(bx + s * 0.75, by + s * 0.52),
        QPointF(bx + s * 0.52, by + s * 0.52),
    ])
    p.drawPolygon(bolt)


def _ico_agent(p: QPainter, sz: float, bg: QColor) -> None:
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


def _ico_rag(p: QPainter, sz: float, bg: QColor) -> None:
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


def _ico_scales(p: QPainter, sz: float, bg: QColor) -> None:
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


def _ico_human_input(p: QPainter, sz: float, bg: QColor) -> None:
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


# ── AI / Reasoning icon functions ────────────────────────────────────────────

def _ico_chain_of_thought(p: QPainter, sz: float, bg: QColor) -> None:
    """Chain of linked circles — means 'step-by-step reasoning'."""
    w = max(1.5, sz * 0.08)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    r = sz * 0.12
    # Three nodes along a path, left to right
    cx1, cy1 = sz * 0.20, sz * 0.60
    cx2, cy2 = sz * 0.50, sz * 0.32
    cx3, cy3 = sz * 0.80, sz * 0.60
    p.drawEllipse(QPointF(cx1, cy1), r, r)
    p.drawEllipse(QPointF(cx2, cy2), r, r)
    p.drawEllipse(QPointF(cx3, cy3), r, r)
    # Connecting lines between circles
    p.drawLine(QPointF(cx1 + r * 0.71, cy1 - r * 0.71), QPointF(cx2 - r * 0.71, cy2 + r * 0.71))
    p.drawLine(QPointF(cx2 + r * 0.71, cy2 + r * 0.71), QPointF(cx3 - r * 0.71, cy3 - r * 0.71))
    # Thought dots above chain
    for i, dx in enumerate([0.35, 0.50, 0.65]):
        dot_r = sz * (0.025 + i * 0.01)
        p.setBrush(QBrush(QColor("white")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(sz * dx, sz * 0.14), dot_r, dot_r)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)


def _ico_majority_vote(p: QPainter, sz: float, bg: QColor) -> None:
    """Three tick marks with a checkmark winner — means 'vote / consensus'."""
    w = max(1.5, sz * 0.09)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Three horizontal ballot lines
    for i, y in enumerate([sz * 0.28, sz * 0.50, sz * 0.72]):
        p.drawLine(QPointF(sz * 0.18, y), QPointF(sz * 0.58, y))
    # Big checkmark on the right for the winner
    p.drawLine(QPointF(sz * 0.64, sz * 0.54), QPointF(sz * 0.74, sz * 0.68))
    p.drawLine(QPointF(sz * 0.74, sz * 0.68), QPointF(sz * 0.88, sz * 0.34))


def _ico_supervisor(p: QPainter, sz: float, bg: QColor) -> None:
    """Person above two sub-agents — means 'orchestrate / supervise'."""
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    # Supervisor head
    p.drawEllipse(QPointF(sz * 0.50, sz * 0.18), sz * 0.12, sz * 0.12)
    # Supervisor body (triangle / shoulders)
    tri = QPolygonF([
        QPointF(sz * 0.50, sz * 0.32),
        QPointF(sz * 0.30, sz * 0.55),
        QPointF(sz * 0.70, sz * 0.55),
    ])
    p.drawPolygon(tri)
    # Two sub-agents below (small circles)
    p.drawEllipse(QPointF(sz * 0.28, sz * 0.74), sz * 0.09, sz * 0.09)
    p.drawEllipse(QPointF(sz * 0.72, sz * 0.74), sz * 0.09, sz * 0.09)
    # Lines from supervisor to sub-agents
    w = max(1.2, sz * 0.07)
    p.setPen(QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
                  Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    p.drawLine(QPointF(sz * 0.40, sz * 0.55), QPointF(sz * 0.28, sz * 0.65))
    p.drawLine(QPointF(sz * 0.60, sz * 0.55), QPointF(sz * 0.72, sz * 0.65))


def _ico_debate_advocate(p: QPainter, sz: float, bg: QColor) -> None:
    """Speech bubble with a raised finger — means 'argue a position'."""
    w = max(1.5, sz * 0.08)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Speech bubble
    bx, by, bw, bh = sz * 0.08, sz * 0.08, sz * 0.60, sz * 0.48
    p.drawRoundedRect(QRectF(bx, by, bw, bh), sz * 0.10, sz * 0.10)
    # Tail pointing down-right
    p.drawLine(QPointF(bx + bw * 0.55, by + bh), QPointF(bx + bw * 0.75, by + bh + sz * 0.10))
    # "!" inside bubble
    mid_x = bx + bw / 2
    p.drawLine(QPointF(mid_x, by + bh * 0.18), QPointF(mid_x, by + bh * 0.62))
    p.setBrush(QBrush(QColor("white")))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QPointF(mid_x, by + bh * 0.78), sz * 0.04, sz * 0.04)
    # Raised finger (right side)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawLine(QPointF(sz * 0.80, sz * 0.85), QPointF(sz * 0.80, sz * 0.44))
    p.drawLine(QPointF(sz * 0.80, sz * 0.44), QPointF(sz * 0.72, sz * 0.38))


def _ico_debate_judge(p: QPainter, sz: float, bg: QColor) -> None:
    """Gavel — means 'judge / decide / rule'."""
    w = max(1.8, sz * 0.10)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Gavel head (thick rect)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    head = QRectF(sz * 0.48, sz * 0.10, sz * 0.38, sz * 0.22)
    p.drawRoundedRect(head, sz * 0.05, sz * 0.05)
    # Handle diagonal
    p.setPen(pen)
    p.drawLine(QPointF(sz * 0.54, sz * 0.32), QPointF(sz * 0.14, sz * 0.82))
    # Sound block
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    block = QRectF(sz * 0.10, sz * 0.76, sz * 0.40, sz * 0.14)
    p.drawRoundedRect(block, sz * 0.03, sz * 0.03)


# ── Web / Search icon functions ───────────────────────────────────────────────

def _ico_web_search(p: QPainter, sz: float, bg: QColor) -> None:
    """Magnifier over a globe grid — means 'web search'."""
    w = max(1.5, sz * 0.08)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Globe circle
    gr = sz * 0.30
    gcx, gcy = sz * 0.40, sz * 0.42
    p.drawEllipse(QPointF(gcx, gcy), gr, gr)
    # Globe latitude / longitude lines
    p.drawLine(QPointF(gcx - gr, gcy), QPointF(gcx + gr, gcy))
    p.drawEllipse(QPointF(gcx, gcy), gr * 0.52, gr)
    # Magnifier handle
    handle_len = sz * 0.20
    hx = gcx + gr * 0.72
    hy = gcy + gr * 0.72
    p.drawLine(QPointF(hx, hy), QPointF(hx + handle_len, hy + handle_len))
    # Magnifier lens ring (small circle)
    p.drawEllipse(QPointF(gcx + gr * 0.48, gcy + gr * 0.48), sz * 0.10, sz * 0.10)


def _ico_web_scrape(p: QPainter, sz: float, bg: QColor) -> None:
    """Page with down-arrow — means 'scrape / extract content'."""
    w = max(1.5, sz * 0.08)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Document outline with folded corner
    p.drawLine(QPointF(sz * 0.20, sz * 0.10), QPointF(sz * 0.65, sz * 0.10))
    p.drawLine(QPointF(sz * 0.65, sz * 0.10), QPointF(sz * 0.80, sz * 0.25))
    p.drawLine(QPointF(sz * 0.80, sz * 0.25), QPointF(sz * 0.80, sz * 0.82))
    p.drawLine(QPointF(sz * 0.80, sz * 0.82), QPointF(sz * 0.20, sz * 0.82))
    p.drawLine(QPointF(sz * 0.20, sz * 0.82), QPointF(sz * 0.20, sz * 0.10))
    p.drawLine(QPointF(sz * 0.65, sz * 0.10), QPointF(sz * 0.65, sz * 0.25))
    p.drawLine(QPointF(sz * 0.65, sz * 0.25), QPointF(sz * 0.80, sz * 0.25))
    # Text lines
    for ly in [sz * 0.38, sz * 0.50, sz * 0.62]:
        p.drawLine(QPointF(sz * 0.30, ly), QPointF(sz * 0.70, ly))
    # Down arrow overlay (extraction)
    p.setPen(QPen(QColor("white"), w * 1.5, Qt.PenStyle.SolidLine,
                  Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    p.drawLine(QPointF(sz * 0.50, sz * 0.32), QPointF(sz * 0.50, sz * 0.68))
    p.drawLine(QPointF(sz * 0.38, sz * 0.56), QPointF(sz * 0.50, sz * 0.68))
    p.drawLine(QPointF(sz * 0.62, sz * 0.56), QPointF(sz * 0.50, sz * 0.68))


def _ico_api_call(p: QPainter, sz: float, bg: QColor) -> None:
    """< / > angle brackets — universally means 'API / code endpoint'."""
    w = max(2.0, sz * 0.11)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Left bracket <
    p.drawLine(QPointF(sz * 0.38, sz * 0.28), QPointF(sz * 0.18, sz * 0.50))
    p.drawLine(QPointF(sz * 0.18, sz * 0.50), QPointF(sz * 0.38, sz * 0.72))
    # Right bracket >
    p.drawLine(QPointF(sz * 0.62, sz * 0.28), QPointF(sz * 0.82, sz * 0.50))
    p.drawLine(QPointF(sz * 0.82, sz * 0.50), QPointF(sz * 0.62, sz * 0.72))
    # Slash /
    p.drawLine(QPointF(sz * 0.57, sz * 0.24), QPointF(sz * 0.43, sz * 0.76))


# ── Data / Vector icon functions ──────────────────────────────────────────────

def _ico_text_chunk(p: QPainter, sz: float, bg: QColor) -> None:
    """Text block split by a scissor cut — means 'chunk / split text'."""
    w = max(1.5, sz * 0.08)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Three text lines (top block)
    for ly in [sz * 0.16, sz * 0.28]:
        p.drawLine(QPointF(sz * 0.14, ly), QPointF(sz * 0.86, ly))
    # Dashed cut line in the middle
    dash_pen = QPen(QColor("white"), w, Qt.PenStyle.DashLine)
    p.setPen(dash_pen)
    p.drawLine(QPointF(sz * 0.10, sz * 0.50), QPointF(sz * 0.90, sz * 0.50))
    # Scissors blades
    p.setPen(pen)
    p.drawLine(QPointF(sz * 0.74, sz * 0.42), QPointF(sz * 0.92, sz * 0.34))
    p.drawLine(QPointF(sz * 0.74, sz * 0.58), QPointF(sz * 0.92, sz * 0.66))
    p.setBrush(QBrush(QColor("white")))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QPointF(sz * 0.72, sz * 0.50), sz * 0.06, sz * 0.06)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Three text lines (bottom block)
    for ly in [sz * 0.72, sz * 0.84]:
        p.drawLine(QPointF(sz * 0.14, ly), QPointF(sz * 0.86, ly))


def _ico_embed(p: QPainter, sz: float, bg: QColor) -> None:
    """Text word → dense vector bar chart — means 'embed / vectorise'."""
    w = max(1.5, sz * 0.08)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(QBrush(QColor("white")))
    # Word representation: short text line
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawLine(QPointF(sz * 0.14, sz * 0.24), QPointF(sz * 0.54, sz * 0.24))
    # Arrow pointing right
    p.drawLine(QPointF(sz * 0.54, sz * 0.24), QPointF(sz * 0.66, sz * 0.24))
    p.drawLine(QPointF(sz * 0.58, sz * 0.18), QPointF(sz * 0.66, sz * 0.24))
    p.drawLine(QPointF(sz * 0.58, sz * 0.30), QPointF(sz * 0.66, sz * 0.24))
    # Vector bars (5 varying heights)
    heights = [0.38, 0.56, 0.28, 0.50, 0.44]
    bar_w = sz * 0.08
    p.setBrush(QBrush(QColor("white")))
    p.setPen(Qt.PenStyle.NoPen)
    base_y = sz * 0.82
    for i, h in enumerate(heights):
        x = sz * (0.14 + i * 0.16)
        bar_h = sz * h
        p.drawRect(QRectF(x, base_y - bar_h, bar_w, bar_h))


def _ico_vector_index(p: QPainter, sz: float, bg: QColor) -> None:
    """Tree/grid of vectors being indexed — means 'build vector index'."""
    w = max(1.5, sz * 0.08)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Database cylinder
    cx = sz * 0.50
    cyl_w, cyl_h = sz * 0.54, sz * 0.54
    top_ell_h = sz * 0.14
    bx = (sz - cyl_w) / 2
    by = sz * 0.20
    p.drawEllipse(QRectF(bx, by, cyl_w, top_ell_h))
    p.drawLine(QPointF(bx, by + top_ell_h / 2), QPointF(bx, by + cyl_h))
    p.drawLine(QPointF(bx + cyl_w, by + top_ell_h / 2), QPointF(bx + cyl_w, by + cyl_h))
    p.drawArc(QRectF(bx, by + cyl_h - top_ell_h / 2, cyl_w, top_ell_h), 0, -180 * 16)
    # Plus / index symbol in upper-right
    p.setPen(QPen(QColor("white"), w * 1.2, Qt.PenStyle.SolidLine,
                  Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    px2, py2, pr = sz * 0.76, sz * 0.22, sz * 0.10
    p.drawLine(QPointF(px2 - pr, py2), QPointF(px2 + pr, py2))
    p.drawLine(QPointF(px2, py2 - pr), QPointF(px2, py2 + pr))


def _ico_vector_retrieve(p: QPainter, sz: float, bg: QColor) -> None:
    """Cylinder with an upward arrow — means 'retrieve / query vector store'."""
    w = max(1.5, sz * 0.08)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    cx = sz * 0.50
    cyl_w, cyl_h = sz * 0.54, sz * 0.54
    top_ell_h = sz * 0.14
    bx = (sz - cyl_w) / 2
    by = sz * 0.34
    p.drawEllipse(QRectF(bx, by, cyl_w, top_ell_h))
    p.drawLine(QPointF(bx, by + top_ell_h / 2), QPointF(bx, by + cyl_h))
    p.drawLine(QPointF(bx + cyl_w, by + top_ell_h / 2), QPointF(bx + cyl_w, by + cyl_h))
    p.drawArc(QRectF(bx, by + cyl_h - top_ell_h / 2, cyl_w, top_ell_h), 0, -180 * 16)
    # Upward arrow
    arr_x = sz * 0.50
    p.drawLine(QPointF(arr_x, sz * 0.30), QPointF(arr_x, sz * 0.12))
    p.drawLine(QPointF(arr_x - sz * 0.10, sz * 0.22), QPointF(arr_x, sz * 0.12))
    p.drawLine(QPointF(arr_x + sz * 0.10, sz * 0.22), QPointF(arr_x, sz * 0.12))


# ── Database / SQL icon functions ─────────────────────────────────────────────

def _ico_db_schema(p: QPainter, sz: float, bg: QColor) -> None:
    """Table grid with column headers — means 'database schema'."""
    w = max(1.2, sz * 0.07)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Outer table border
    p.drawRect(QRectF(sz * 0.12, sz * 0.14, sz * 0.76, sz * 0.72))
    # Header row
    p.drawLine(QPointF(sz * 0.12, sz * 0.30), QPointF(sz * 0.88, sz * 0.30))
    # Vertical column separator
    p.drawLine(QPointF(sz * 0.50, sz * 0.14), QPointF(sz * 0.50, sz * 0.86))
    # Row separator
    p.drawLine(QPointF(sz * 0.12, sz * 0.55), QPointF(sz * 0.88, sz * 0.55))
    # Header fill dots (indicate key)
    p.setBrush(QBrush(QColor("white")))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QPointF(sz * 0.31, sz * 0.22), sz * 0.04, sz * 0.04)
    p.drawEllipse(QPointF(sz * 0.69, sz * 0.22), sz * 0.04, sz * 0.04)


def _ico_nl_to_sql(p: QPainter, sz: float, bg: QColor) -> None:
    """English text arrow → SQL keyword SELECT — means 'NL to SQL'."""
    w = max(1.5, sz * 0.08)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # "text" representation: two short lines
    p.drawLine(QPointF(sz * 0.12, sz * 0.26), QPointF(sz * 0.44, sz * 0.26))
    p.drawLine(QPointF(sz * 0.12, sz * 0.36), QPointF(sz * 0.36, sz * 0.36))
    # Arrow
    p.drawLine(QPointF(sz * 0.12, sz * 0.52), QPointF(sz * 0.56, sz * 0.52))
    p.drawLine(QPointF(sz * 0.46, sz * 0.44), QPointF(sz * 0.56, sz * 0.52))
    p.drawLine(QPointF(sz * 0.46, sz * 0.60), QPointF(sz * 0.56, sz * 0.52))
    # "SQL" keyword block
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    p.drawRoundedRect(QRectF(sz * 0.58, sz * 0.62, sz * 0.32, sz * 0.24), sz * 0.05, sz * 0.05)
    font = QFont()
    font.setPixelSize(max(6, int(sz * 0.18)))
    font.setBold(True)
    p.setFont(font)
    p.setPen(QPen(bg))
    p.drawText(QRectF(sz * 0.58, sz * 0.62, sz * 0.32, sz * 0.24), Qt.AlignmentFlag.AlignCenter, "SQL")


def _ico_sql_execute(p: QPainter, sz: float, bg: QColor) -> None:
    """Play triangle inside a cylinder — means 'execute SQL'."""
    w = max(1.5, sz * 0.08)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Cylinder
    cx = sz * 0.50
    cyl_w, cyl_h = sz * 0.60, sz * 0.56
    top_ell_h = sz * 0.14
    bx = (sz - cyl_w) / 2
    by = sz * 0.18
    p.drawEllipse(QRectF(bx, by, cyl_w, top_ell_h))
    p.drawLine(QPointF(bx, by + top_ell_h / 2), QPointF(bx, by + cyl_h))
    p.drawLine(QPointF(bx + cyl_w, by + top_ell_h / 2), QPointF(bx + cyl_w, by + cyl_h))
    p.drawArc(QRectF(bx, by + cyl_h - top_ell_h / 2, cyl_w, top_ell_h), 0, -180 * 16)
    # Play triangle inside
    m = sz * 0.15
    cy_mid = by + top_ell_h / 2 + (cyl_h - top_ell_h) * 0.45
    tri = QPolygonF([
        QPointF(cx - m * 0.7, cy_mid - m * 0.8),
        QPointF(cx + m * 0.9, cy_mid),
        QPointF(cx - m * 0.7, cy_mid + m * 0.8),
    ])
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    p.drawPolygon(tri)


# ── Voice / Audio icon functions ──────────────────────────────────────────────

def _ico_speech_to_text(p: QPainter, sz: float, bg: QColor) -> None:
    """Microphone with right arrow to text lines — means 'transcribe speech'."""
    w = max(1.5, sz * 0.08)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(QBrush(QColor("white")))
    # Microphone capsule
    mic_cx, mic_cy = sz * 0.28, sz * 0.34
    p.drawRoundedRect(QRectF(mic_cx - sz * 0.09, sz * 0.12, sz * 0.18, sz * 0.36),
                      sz * 0.09, sz * 0.09)
    # Microphone stand
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawArc(QRectF(mic_cx - sz * 0.16, sz * 0.28, sz * 0.32, sz * 0.24),
              0, -180 * 16)
    p.drawLine(QPointF(mic_cx, sz * 0.52), QPointF(mic_cx, sz * 0.64))
    p.drawLine(QPointF(mic_cx - sz * 0.10, sz * 0.64), QPointF(mic_cx + sz * 0.10, sz * 0.64))
    # Arrow →
    arr_x = sz * 0.52
    p.drawLine(QPointF(arr_x, sz * 0.50), QPointF(sz * 0.70, sz * 0.50))
    p.drawLine(QPointF(sz * 0.62, sz * 0.42), QPointF(sz * 0.70, sz * 0.50))
    p.drawLine(QPointF(sz * 0.62, sz * 0.58), QPointF(sz * 0.70, sz * 0.50))
    # Text lines
    for ly in [sz * 0.34, sz * 0.46, sz * 0.58]:
        p.drawLine(QPointF(sz * 0.72, ly), QPointF(sz * 0.90, ly))


def _ico_text_to_speech(p: QPainter, sz: float, bg: QColor) -> None:
    """Sound waves emanating from a speaker — means 'text to speech'."""
    w = max(1.5, sz * 0.08)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(QBrush(QColor("white")))
    # Speaker body
    sx, sy = sz * 0.12, sz * 0.36
    sw, sh = sz * 0.20, sz * 0.28
    p.drawRect(QRectF(sx, sy, sw, sh))
    # Speaker cone
    cone = QPolygonF([
        QPointF(sx + sw, sy),
        QPointF(sx + sw + sz * 0.16, sy - sz * 0.16),
        QPointF(sx + sw + sz * 0.16, sy + sh + sz * 0.16),
        QPointF(sx + sw, sy + sh),
    ])
    p.drawPolygon(cone)
    # Sound waves
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    for r_mult, start_y_off in [(0.18, 0.18), (0.28, 0.28), (0.38, 0.38)]:
        r = sz * r_mult
        wave_cx = sx + sw + sz * 0.16
        p.drawArc(
            QRectF(wave_cx - r * 0.3, sz / 2 - r, r * 0.6, r * 2),
            -90 * 16, 180 * 16
        )


# ── Document / Vision icon functions ─────────────────────────────────────────

def _ico_pdf_extract(p: QPainter, sz: float, bg: QColor) -> None:
    """PDF page with a highlighted text selection — means 'extract from PDF'."""
    w = max(1.2, sz * 0.07)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Page outline
    p.drawLine(QPointF(sz * 0.18, sz * 0.08), QPointF(sz * 0.66, sz * 0.08))
    p.drawLine(QPointF(sz * 0.66, sz * 0.08), QPointF(sz * 0.82, sz * 0.24))
    p.drawLine(QPointF(sz * 0.82, sz * 0.24), QPointF(sz * 0.82, sz * 0.92))
    p.drawLine(QPointF(sz * 0.82, sz * 0.92), QPointF(sz * 0.18, sz * 0.92))
    p.drawLine(QPointF(sz * 0.18, sz * 0.92), QPointF(sz * 0.18, sz * 0.08))
    p.drawLine(QPointF(sz * 0.66, sz * 0.08), QPointF(sz * 0.66, sz * 0.24))
    p.drawLine(QPointF(sz * 0.66, sz * 0.24), QPointF(sz * 0.82, sz * 0.24))
    # "PDF" label
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    p.drawRoundedRect(QRectF(sz * 0.24, sz * 0.30, sz * 0.30, sz * 0.18), sz * 0.04, sz * 0.04)
    font = QFont()
    font.setPixelSize(max(5, int(sz * 0.14)))
    font.setBold(True)
    p.setFont(font)
    p.setPen(QPen(bg))
    p.drawText(QRectF(sz * 0.24, sz * 0.30, sz * 0.30, sz * 0.18), Qt.AlignmentFlag.AlignCenter, "PDF")
    # Highlighted text lines
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    for ly in [sz * 0.58, sz * 0.70, sz * 0.82]:
        p.drawLine(QPointF(sz * 0.26, ly), QPointF(sz * 0.74, ly))


def _ico_image_vision(p: QPainter, sz: float, bg: QColor) -> None:
    """Camera aperture / eye — means 'see / vision / image understanding'."""
    w = max(1.5, sz * 0.08)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    cx, cy = sz / 2, sz / 2
    # Eye outline (almond shape via arc pair)
    path = QPainterPath()
    path.moveTo(sz * 0.12, cy)
    path.cubicTo(sz * 0.12, sz * 0.24, sz * 0.88, sz * 0.24, sz * 0.88, cy)
    path.cubicTo(sz * 0.88, sz * 0.76, sz * 0.12, sz * 0.76, sz * 0.12, cy)
    p.drawPath(path)
    # Iris ring
    p.drawEllipse(QPointF(cx, cy), sz * 0.20, sz * 0.20)
    # Pupil
    p.setBrush(QBrush(QColor("white")))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QPointF(cx, cy), sz * 0.08, sz * 0.08)


def _ico_data_validate(p: QPainter, sz: float, bg: QColor) -> None:
    """Shield with a checkmark — means 'validate / verify data'."""
    w = max(1.5, sz * 0.08)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Shield outline
    shield = QPainterPath()
    shield.moveTo(sz * 0.50, sz * 0.10)
    shield.lineTo(sz * 0.86, sz * 0.24)
    shield.lineTo(sz * 0.86, sz * 0.56)
    shield.cubicTo(sz * 0.86, sz * 0.82, sz * 0.50, sz * 0.92, sz * 0.50, sz * 0.92)
    shield.cubicTo(sz * 0.50, sz * 0.92, sz * 0.14, sz * 0.82, sz * 0.14, sz * 0.56)
    shield.lineTo(sz * 0.14, sz * 0.24)
    shield.closeSubpath()
    p.drawPath(shield)
    # Checkmark inside shield
    p.drawLine(QPointF(sz * 0.32, sz * 0.54), QPointF(sz * 0.46, sz * 0.68))
    p.drawLine(QPointF(sz * 0.46, sz * 0.68), QPointF(sz * 0.68, sz * 0.40))


# ── Code / Execution icon functions ──────────────────────────────────────────

def _ico_code_gen(p: QPainter, sz: float, bg: QColor) -> None:
    """Stars / sparkles above code brackets — means 'AI generates code'."""
    w = max(1.5, sz * 0.08)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Left bracket {
    p.drawLine(QPointF(sz * 0.36, sz * 0.46), QPointF(sz * 0.28, sz * 0.54))
    p.drawLine(QPointF(sz * 0.28, sz * 0.54), QPointF(sz * 0.36, sz * 0.62))
    # Right bracket }
    p.drawLine(QPointF(sz * 0.64, sz * 0.46), QPointF(sz * 0.72, sz * 0.54))
    p.drawLine(QPointF(sz * 0.72, sz * 0.54), QPointF(sz * 0.64, sz * 0.62))
    # Sparkle star (4 lines from center)
    sx2, sy2 = sz * 0.50, sz * 0.26
    for angle in [0, 45, 90, 135]:
        rad = math.radians(angle)
        dx, dy = math.cos(rad) * sz * 0.10, math.sin(rad) * sz * 0.10
        p.drawLine(QPointF(sx2 - dx, sy2 - dy), QPointF(sx2 + dx, sy2 + dy))
    # Small dots at sparkle tips
    p.setBrush(QBrush(QColor("white")))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QPointF(sz * 0.26, sz * 0.70), sz * 0.04, sz * 0.04)
    p.drawEllipse(QPointF(sz * 0.74, sz * 0.70), sz * 0.04, sz * 0.04)


def _ico_code_exec(p: QPainter, sz: float, bg: QColor) -> None:
    """Terminal prompt > with a running spinner — means 'execute code'."""
    w = max(1.5, sz * 0.08)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Terminal rectangle
    p.drawRoundedRect(QRectF(sz * 0.10, sz * 0.14, sz * 0.80, sz * 0.60),
                      sz * 0.06, sz * 0.06)
    # Prompt > symbol
    p.drawLine(QPointF(sz * 0.22, sz * 0.38), QPointF(sz * 0.34, sz * 0.46))
    p.drawLine(QPointF(sz * 0.34, sz * 0.46), QPointF(sz * 0.22, sz * 0.54))
    # Blinking cursor
    p.drawLine(QPointF(sz * 0.38, sz * 0.38), QPointF(sz * 0.38, sz * 0.54))
    # Spinner arc (partial circle at bottom)
    p.drawArc(QRectF(sz * 0.36, sz * 0.72, sz * 0.28, sz * 0.18),
              30 * 16, 270 * 16)
    # Arrow tip of spinner
    p.drawLine(QPointF(sz * 0.36, sz * 0.81), QPointF(sz * 0.42, sz * 0.90))
    p.drawLine(QPointF(sz * 0.42, sz * 0.90), QPointF(sz * 0.50, sz * 0.82))


def _ico_test_gen(p: QPainter, sz: float, bg: QColor) -> None:
    """Clipboard with checkboxes — means 'generate tests'."""
    w = max(1.2, sz * 0.07)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Clipboard outer rect
    p.drawRoundedRect(QRectF(sz * 0.16, sz * 0.18, sz * 0.68, sz * 0.72),
                      sz * 0.06, sz * 0.06)
    # Clipboard tab
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    p.drawRoundedRect(QRectF(sz * 0.36, sz * 0.10, sz * 0.28, sz * 0.16),
                      sz * 0.04, sz * 0.04)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Three test rows: checkbox + line
    for i, checked in enumerate([True, True, False]):
        y = sz * (0.36 + i * 0.18)
        # Checkbox square
        cbx, cbs = sz * 0.24, sz * 0.12
        p.drawRect(QRectF(cbx, y - cbs / 2, cbs, cbs))
        if checked:
            p.drawLine(QPointF(cbx + cbs * 0.18, y), QPointF(cbx + cbs * 0.46, y + cbs * 0.30))
            p.drawLine(QPointF(cbx + cbs * 0.46, y + cbs * 0.30), QPointF(cbx + cbs * 0.82, y - cbs * 0.22))
        # Text stub
        p.drawLine(QPointF(sz * 0.42, y), QPointF(sz * 0.76, y))


# ── Data Processing icon functions ────────────────────────────────────────────

def _ico_map_node(p: QPainter, sz: float, bg: QColor) -> None:
    """One input → many outputs (fan-out arrows) — means 'map / apply to each'."""
    w = max(1.5, sz * 0.08)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Input arrow (left)
    p.drawLine(QPointF(sz * 0.10, sz * 0.50), QPointF(sz * 0.36, sz * 0.50))
    # Fan out to 3 outputs
    for y_out in [sz * 0.24, sz * 0.50, sz * 0.76]:
        p.drawLine(QPointF(sz * 0.36, sz * 0.50), QPointF(sz * 0.64, y_out))
        # Small arrowhead
        dx, dy = sz * 0.64 - sz * 0.36, y_out - sz * 0.50
        length = math.sqrt(dx * dx + dy * dy)
        ux, uy = dx / length * sz * 0.08, dy / length * sz * 0.08
        px2 = sz * 0.64 - ux
        py2 = y_out - uy
        perp_x, perp_y = -uy * 0.5, ux * 0.5
        p.drawLine(QPointF(px2 - perp_x, py2 - perp_y), QPointF(sz * 0.64, y_out))
        p.drawLine(QPointF(px2 + perp_x, py2 + perp_y), QPointF(sz * 0.64, y_out))
    p.drawLine(QPointF(sz * 0.64, sz * 0.24), QPointF(sz * 0.90, sz * 0.24))
    p.drawLine(QPointF(sz * 0.64, sz * 0.50), QPointF(sz * 0.90, sz * 0.50))
    p.drawLine(QPointF(sz * 0.64, sz * 0.76), QPointF(sz * 0.90, sz * 0.76))


def _ico_reduce_node(p: QPainter, sz: float, bg: QColor) -> None:
    """Many inputs → one output (fan-in) — means 'reduce / aggregate'."""
    w = max(1.5, sz * 0.08)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Three inputs
    for y_in in [sz * 0.24, sz * 0.50, sz * 0.76]:
        p.drawLine(QPointF(sz * 0.10, y_in), QPointF(sz * 0.36, y_in))
    # Fan-in lines
    for y_in in [sz * 0.24, sz * 0.50, sz * 0.76]:
        p.drawLine(QPointF(sz * 0.36, y_in), QPointF(sz * 0.64, sz * 0.50))
    # Output arrow
    p.drawLine(QPointF(sz * 0.64, sz * 0.50), QPointF(sz * 0.90, sz * 0.50))
    p.drawLine(QPointF(sz * 0.80, sz * 0.42), QPointF(sz * 0.90, sz * 0.50))
    p.drawLine(QPointF(sz * 0.80, sz * 0.58), QPointF(sz * 0.90, sz * 0.50))


def _ico_condition(p: QPainter, sz: float, bg: QColor) -> None:
    """Diamond shape — universal flowchart decision symbol."""
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    diamond = QPolygonF([
        QPointF(sz * 0.50, sz * 0.10),
        QPointF(sz * 0.88, sz * 0.50),
        QPointF(sz * 0.50, sz * 0.90),
        QPointF(sz * 0.12, sz * 0.50),
    ])
    p.drawPolygon(diamond)
    # ? mark inside
    font = QFont()
    font.setPixelSize(max(8, int(sz * 0.34)))
    font.setBold(True)
    p.setFont(font)
    p.setPen(QPen(bg))
    p.drawText(QRectF(0, 0, sz, sz), Qt.AlignmentFlag.AlignCenter, "?")


def _ico_loop_counter(p: QPainter, sz: float, bg: QColor) -> None:
    """Circular arrow with a counter badge — means 'loop / iterate'."""
    w = max(1.5, sz * 0.08)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Circular arc (270 degrees — open at top-right)
    p.drawArc(QRectF(sz * 0.16, sz * 0.18, sz * 0.58, sz * 0.58),
              60 * 16, 270 * 16)
    # Arrow tip
    tip_x, tip_y = sz * 0.70, sz * 0.30
    p.drawLine(QPointF(tip_x, tip_y), QPointF(tip_x + sz * 0.10, tip_y - sz * 0.04))
    p.drawLine(QPointF(tip_x, tip_y), QPointF(tip_x + sz * 0.04, tip_y + sz * 0.10))
    # Counter badge (small number box)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    p.drawRoundedRect(QRectF(sz * 0.62, sz * 0.60, sz * 0.28, sz * 0.28),
                      sz * 0.05, sz * 0.05)
    font = QFont()
    font.setPixelSize(max(6, int(sz * 0.18)))
    font.setBold(True)
    p.setFont(font)
    p.setPen(QPen(bg))
    p.drawText(QRectF(sz * 0.62, sz * 0.60, sz * 0.28, sz * 0.28),
               Qt.AlignmentFlag.AlignCenter, "N")


def _ico_transform(p: QPainter, sz: float, bg: QColor) -> None:
    """Box → arrow → box with shape change — means 'transform data'."""
    w = max(1.5, sz * 0.08)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Input shape: rough square
    p.drawRect(QRectF(sz * 0.08, sz * 0.34, sz * 0.24, sz * 0.32))
    # Output shape: diamond
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    out_cx, out_cy = sz * 0.80, sz * 0.50
    diamond = QPolygonF([
        QPointF(out_cx, out_cy - sz * 0.18),
        QPointF(out_cx + sz * 0.16, out_cy),
        QPointF(out_cx, out_cy + sz * 0.18),
        QPointF(out_cx - sz * 0.16, out_cy),
    ])
    p.drawPolygon(diamond)
    # Arrow between them
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawLine(QPointF(sz * 0.34, sz * 0.50), QPointF(sz * 0.56, sz * 0.50))
    p.drawLine(QPointF(sz * 0.48, sz * 0.43), QPointF(sz * 0.56, sz * 0.50))
    p.drawLine(QPointF(sz * 0.48, sz * 0.57), QPointF(sz * 0.56, sz * 0.50))


def _ico_merge(p: QPainter, sz: float, bg: QColor) -> None:
    """Two streams flowing into one — means 'merge / combine'."""
    w = max(1.5, sz * 0.09)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Two input arrows
    p.drawLine(QPointF(sz * 0.10, sz * 0.28), QPointF(sz * 0.44, sz * 0.50))
    p.drawLine(QPointF(sz * 0.10, sz * 0.72), QPointF(sz * 0.44, sz * 0.50))
    # Merged output
    p.drawLine(QPointF(sz * 0.44, sz * 0.50), QPointF(sz * 0.88, sz * 0.50))
    # Arrowhead
    p.drawLine(QPointF(sz * 0.78, sz * 0.42), QPointF(sz * 0.88, sz * 0.50))
    p.drawLine(QPointF(sz * 0.78, sz * 0.58), QPointF(sz * 0.88, sz * 0.50))
    # Joining dot
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    p.drawEllipse(QPointF(sz * 0.44, sz * 0.50), sz * 0.06, sz * 0.06)


# ── Calendar icon functions ───────────────────────────────────────────────────

def _ico_calendar_read(p: QPainter, sz: float, bg: QColor) -> None:
    """Calendar page with a magnifier — means 'read calendar events'."""
    w = max(1.2, sz * 0.07)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Calendar outer rect
    p.drawRoundedRect(QRectF(sz * 0.10, sz * 0.18, sz * 0.56, sz * 0.60),
                      sz * 0.04, sz * 0.04)
    # Header band
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    p.drawRoundedRect(QRectF(sz * 0.10, sz * 0.18, sz * 0.56, sz * 0.14),
                      sz * 0.04, sz * 0.04)
    # Header pins
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawLine(QPointF(sz * 0.28, sz * 0.12), QPointF(sz * 0.28, sz * 0.24))
    p.drawLine(QPointF(sz * 0.48, sz * 0.12), QPointF(sz * 0.48, sz * 0.24))
    # Grid dots (6 day slots)
    p.setBrush(QBrush(QColor("white")))
    p.setPen(Qt.PenStyle.NoPen)
    for row in range(2):
        for col in range(3):
            cx_d = sz * (0.22 + col * 0.16)
            cy_d = sz * (0.44 + row * 0.18)
            p.drawEllipse(QPointF(cx_d, cy_d), sz * 0.04, sz * 0.04)
    # Magnifier
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(QPointF(sz * 0.74, sz * 0.62), sz * 0.12, sz * 0.12)
    p.drawLine(QPointF(sz * 0.83, sz * 0.71), QPointF(sz * 0.90, sz * 0.82))


def _ico_calendar_write(p: QPainter, sz: float, bg: QColor) -> None:
    """Calendar page with a plus badge — means 'create calendar event'."""
    w = max(1.2, sz * 0.07)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Calendar outer rect
    p.drawRoundedRect(QRectF(sz * 0.10, sz * 0.18, sz * 0.56, sz * 0.60),
                      sz * 0.04, sz * 0.04)
    # Header band
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    p.drawRoundedRect(QRectF(sz * 0.10, sz * 0.18, sz * 0.56, sz * 0.14),
                      sz * 0.04, sz * 0.04)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawLine(QPointF(sz * 0.28, sz * 0.12), QPointF(sz * 0.28, sz * 0.24))
    p.drawLine(QPointF(sz * 0.48, sz * 0.12), QPointF(sz * 0.48, sz * 0.24))
    # Grid dots (6 day slots)
    p.setBrush(QBrush(QColor("white")))
    p.setPen(Qt.PenStyle.NoPen)
    for row in range(2):
        for col in range(3):
            cx_d = sz * (0.22 + col * 0.16)
            cy_d = sz * (0.44 + row * 0.18)
            p.drawEllipse(QPointF(cx_d, cy_d), sz * 0.04, sz * 0.04)
    # Plus badge (circle with + in bottom-right)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    p.drawEllipse(QPointF(sz * 0.76, sz * 0.66), sz * 0.16, sz * 0.16)
    p.setPen(QPen(bg, w * 1.2, Qt.PenStyle.SolidLine,
                  Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    p.drawLine(QPointF(sz * 0.76 - sz * 0.08, sz * 0.66), QPointF(sz * 0.76 + sz * 0.08, sz * 0.66))
    p.drawLine(QPointF(sz * 0.76, sz * 0.66 - sz * 0.08), QPointF(sz * 0.76, sz * 0.66 + sz * 0.08))


# ── MCP / Agent Protocol icon functions ──────────────────────────────────────

def _ico_mcp_tool(p: QPainter, sz: float, bg: QColor) -> None:
    """Plug connector — means 'connect to MCP tool server'."""
    w = max(1.5, sz * 0.09)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Plug body (rect)
    p.drawRoundedRect(QRectF(sz * 0.28, sz * 0.36, sz * 0.44, sz * 0.42),
                      sz * 0.06, sz * 0.06)
    # Prongs (two teeth at top)
    p.drawLine(QPointF(sz * 0.38, sz * 0.36), QPointF(sz * 0.38, sz * 0.16))
    p.drawLine(QPointF(sz * 0.62, sz * 0.36), QPointF(sz * 0.62, sz * 0.16))
    # Cord at bottom
    p.drawLine(QPointF(sz * 0.50, sz * 0.78), QPointF(sz * 0.50, sz * 0.90))
    p.drawLine(QPointF(sz * 0.38, sz * 0.90), QPointF(sz * 0.62, sz * 0.90))
    # Small circle (indicator light)
    p.setBrush(QBrush(QColor("white")))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QPointF(sz * 0.50, sz * 0.56), sz * 0.06, sz * 0.06)


def _ico_a2a_send(p: QPainter, sz: float, bg: QColor) -> None:
    """Two agent heads with outbound arrow between them — means 'send to agent'."""
    w = max(1.3, sz * 0.08)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    # Left agent head
    p.drawEllipse(QPointF(sz * 0.22, sz * 0.28), sz * 0.12, sz * 0.12)
    body_l = QPainterPath()
    body_l.addEllipse(QRectF(sz * 0.08, sz * 0.42, sz * 0.28, sz * 0.26))
    clip = QPainterPath()
    clip.addRect(QRectF(sz * 0.08, sz * 0.42, sz * 0.28, sz * 0.26))
    p.fillPath(body_l.intersected(clip), QColor("white"))
    # Right agent head
    p.drawEllipse(QPointF(sz * 0.78, sz * 0.28), sz * 0.12, sz * 0.12)
    body_r = QPainterPath()
    body_r.addEllipse(QRectF(sz * 0.64, sz * 0.42, sz * 0.28, sz * 0.26))
    p.fillPath(body_r.intersected(clip), QColor("white"))
    # Arrow from left to right
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawLine(QPointF(sz * 0.36, sz * 0.50), QPointF(sz * 0.60, sz * 0.50))
    p.drawLine(QPointF(sz * 0.52, sz * 0.42), QPointF(sz * 0.60, sz * 0.50))
    p.drawLine(QPointF(sz * 0.52, sz * 0.58), QPointF(sz * 0.60, sz * 0.50))
    # "→" emphasis dot
    p.setBrush(QBrush(QColor("white")))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QPointF(sz * 0.50, sz * 0.80), sz * 0.06, sz * 0.06)


def _ico_a2a_receive(p: QPainter, sz: float, bg: QColor) -> None:
    """Two agent heads with inbound arrow — means 'receive from agent'."""
    w = max(1.3, sz * 0.08)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    # Left agent head
    p.drawEllipse(QPointF(sz * 0.22, sz * 0.28), sz * 0.12, sz * 0.12)
    clip = QPainterPath()
    clip.addRect(QRectF(sz * 0.08, sz * 0.42, sz * 0.28, sz * 0.26))
    body_l = QPainterPath()
    body_l.addEllipse(QRectF(sz * 0.08, sz * 0.42, sz * 0.28, sz * 0.26))
    p.fillPath(body_l.intersected(clip), QColor("white"))
    # Right agent head
    p.drawEllipse(QPointF(sz * 0.78, sz * 0.28), sz * 0.12, sz * 0.12)
    clip2 = QPainterPath()
    clip2.addRect(QRectF(sz * 0.64, sz * 0.42, sz * 0.28, sz * 0.26))
    body_r = QPainterPath()
    body_r.addEllipse(QRectF(sz * 0.64, sz * 0.42, sz * 0.28, sz * 0.26))
    p.fillPath(body_r.intersected(clip2), QColor("white"))
    # Arrow from right to left (receive)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawLine(QPointF(sz * 0.64, sz * 0.50), QPointF(sz * 0.38, sz * 0.50))
    p.drawLine(QPointF(sz * 0.46, sz * 0.42), QPointF(sz * 0.38, sz * 0.50))
    p.drawLine(QPointF(sz * 0.46, sz * 0.58), QPointF(sz * 0.38, sz * 0.50))
    # Inbox tray indicator dot
    p.setBrush(QBrush(QColor("white")))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QPointF(sz * 0.50, sz * 0.80), sz * 0.06, sz * 0.06)


# ── Observability / Utility icon functions ────────────────────────────────────

def _ico_log_node(p: QPainter, sz: float, bg: QColor) -> None:
    """Scroll / log roll — means 'log / record'."""
    w = max(1.2, sz * 0.07)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Scroll body
    p.drawRoundedRect(QRectF(sz * 0.16, sz * 0.20, sz * 0.68, sz * 0.60),
                      sz * 0.10, sz * 0.10)
    # Scroll curl (top and bottom arcs)
    p.drawArc(QRectF(sz * 0.08, sz * 0.14, sz * 0.20, sz * 0.16), 90 * 16, 180 * 16)
    p.drawArc(QRectF(sz * 0.08, sz * 0.70, sz * 0.20, sz * 0.16), 90 * 16, 180 * 16)
    # Text lines on scroll
    for ly in [sz * 0.35, sz * 0.50, sz * 0.65]:
        p.drawLine(QPointF(sz * 0.32, ly), QPointF(sz * 0.76, ly))


def _ico_timer_node(p: QPainter, sz: float, bg: QColor) -> None:
    """Stopwatch — means 'time / measure elapsed time'."""
    w = max(1.5, sz * 0.08)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Watch body (circle)
    cx, cy = sz * 0.50, sz * 0.56
    r = sz * 0.34
    p.drawEllipse(QPointF(cx, cy), r, r)
    # Crown at top
    p.drawLine(QPointF(sz * 0.44, sz * 0.20), QPointF(sz * 0.56, sz * 0.20))
    p.drawLine(QPointF(sz * 0.50, sz * 0.20), QPointF(sz * 0.50, sz * 0.22))
    # Button
    p.drawRoundedRect(QRectF(sz * 0.44, sz * 0.16, sz * 0.12, sz * 0.08),
                      sz * 0.03, sz * 0.03)
    # Clock hands (hour at 12, minute at 2)
    p.drawLine(QPointF(cx, cy), QPointF(cx, cy - r * 0.60))
    p.drawLine(QPointF(cx, cy), QPointF(cx + r * 0.50, cy - r * 0.28))
    # Tick marks
    for angle_deg in range(0, 360, 60):
        a = math.radians(angle_deg)
        p.drawLine(
            QPointF(cx + (r - sz * 0.06) * math.sin(a), cy - (r - sz * 0.06) * math.cos(a)),
            QPointF(cx + r * math.sin(a), cy - r * math.cos(a)),
        )


def _ico_cache_node(p: QPainter, sz: float, bg: QColor) -> None:
    """Lightning bolt inside a storage cylinder — means 'fast cache'."""
    w = max(1.5, sz * 0.08)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Cylinder
    cyl_w, cyl_h = sz * 0.60, sz * 0.60
    top_ell_h = sz * 0.14
    bx = (sz - cyl_w) / 2
    by = sz * 0.14
    p.drawEllipse(QRectF(bx, by, cyl_w, top_ell_h))
    p.drawLine(QPointF(bx, by + top_ell_h / 2), QPointF(bx, by + cyl_h))
    p.drawLine(QPointF(bx + cyl_w, by + top_ell_h / 2), QPointF(bx + cyl_w, by + cyl_h))
    p.drawArc(QRectF(bx, by + cyl_h - top_ell_h / 2, cyl_w, top_ell_h), 0, -180 * 16)
    # Lightning bolt inside
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    bolt = QPolygonF([
        QPointF(sz * 0.56, sz * 0.30),
        QPointF(sz * 0.44, sz * 0.52),
        QPointF(sz * 0.52, sz * 0.52),
        QPointF(sz * 0.44, sz * 0.72),
        QPointF(sz * 0.58, sz * 0.48),
        QPointF(sz * 0.50, sz * 0.48),
    ])
    p.drawPolygon(bolt)


def _ico_trace_node(p: QPainter, sz: float, bg: QColor) -> None:
    """Span timeline bars — means 'distributed trace / telemetry'."""
    w = max(1.2, sz * 0.07)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(QBrush(QColor("white")))
    bar_h = sz * 0.10
    # Three span bars at different lengths and offsets
    spans = [(0.10, 0.80, 0.22), (0.22, 0.56, 0.40), (0.38, 0.42, 0.58)]
    for x_start, width, y_top in spans:
        p.drawRoundedRect(QRectF(sz * x_start, sz * y_top, sz * width, bar_h),
                          bar_h * 0.3, bar_h * 0.3)
    # Vertical timeline
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawLine(QPointF(sz * 0.08, sz * 0.14), QPointF(sz * 0.08, sz * 0.86))
    # Tick marks on timeline
    for y_t in [sz * 0.26, sz * 0.44, sz * 0.62]:
        p.drawLine(QPointF(sz * 0.05, y_t), QPointF(sz * 0.11, y_t))


# ── Data Structures / Memory icon functions ──────────────────────────────────

def _ico_registry(p: QPainter, sz: float, bg: QColor) -> None:
    """Key + label card — means 'look up / store named entry'."""
    w = max(1.3, sz * 0.07)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Card outline
    p.drawRoundedRect(QRectF(sz * 0.10, sz * 0.20, sz * 0.80, sz * 0.60),
                      sz * 0.05, sz * 0.05)
    # Key symbol (ring + shaft)
    p.setBrush(Qt.BrushStyle.NoBrush)
    key_cx, key_cy = sz * 0.30, sz * 0.42
    p.drawEllipse(QPointF(key_cx, key_cy), sz * 0.10, sz * 0.10)
    p.drawLine(QPointF(key_cx + sz * 0.10, key_cy), QPointF(key_cx + sz * 0.28, key_cy))
    p.drawLine(QPointF(key_cx + sz * 0.22, key_cy), QPointF(key_cx + sz * 0.22, key_cy + sz * 0.08))
    # Value label lines
    for ly in [sz * 0.42, sz * 0.56, sz * 0.68]:
        p.drawLine(QPointF(sz * 0.50, ly), QPointF(sz * 0.82, ly))


def _ico_stack_push(p: QPainter, sz: float, bg: QColor) -> None:
    """Stack of plates with downward arrow (push) — means 'push onto stack'."""
    w = max(1.3, sz * 0.07)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Three stack layers
    for i, y in enumerate([sz * 0.54, sz * 0.67, sz * 0.80]):
        alpha = 255 - i * 50
        bar_color = QColor(255, 255, 255, alpha)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(bar_color))
        margin = sz * (0.08 + i * 0.04)
        p.drawRoundedRect(QRectF(margin, y - sz * 0.05, sz - 2 * margin, sz * 0.10),
                          sz * 0.02, sz * 0.02)
    # Down arrow (push new item)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    ax = sz * 0.50
    p.drawLine(QPointF(ax, sz * 0.10), QPointF(ax, sz * 0.48))
    p.drawLine(QPointF(ax - sz * 0.12, sz * 0.38), QPointF(ax, sz * 0.48))
    p.drawLine(QPointF(ax + sz * 0.12, sz * 0.38), QPointF(ax, sz * 0.48))


def _ico_stack_pop(p: QPainter, sz: float, bg: QColor) -> None:
    """Stack of plates with upward arrow (pop) — means 'pop from stack'."""
    w = max(1.3, sz * 0.07)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Three stack layers
    for i, y in enumerate([sz * 0.54, sz * 0.67, sz * 0.80]):
        alpha = 255 - i * 50
        bar_color = QColor(255, 255, 255, alpha)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(bar_color))
        margin = sz * (0.08 + i * 0.04)
        p.drawRoundedRect(QRectF(margin, y - sz * 0.05, sz - 2 * margin, sz * 0.10),
                          sz * 0.02, sz * 0.02)
    # Up arrow (pop)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    ax = sz * 0.50
    p.drawLine(QPointF(ax, sz * 0.48), QPointF(ax, sz * 0.10))
    p.drawLine(QPointF(ax - sz * 0.12, sz * 0.20), QPointF(ax, sz * 0.10))
    p.drawLine(QPointF(ax + sz * 0.12, sz * 0.20), QPointF(ax, sz * 0.10))


def _ico_queue_enqueue(p: QPainter, sz: float, bg: QColor) -> None:
    """Horizontal queue with item entering from the right — means 'enqueue'."""
    w = max(1.3, sz * 0.07)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Queue tube
    p.drawRect(QRectF(sz * 0.10, sz * 0.38, sz * 0.56, sz * 0.24))
    # Items inside queue (two slots)
    for i in range(2):
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor("white")))
        p.drawRect(QRectF(sz * (0.14 + i * 0.22), sz * 0.42, sz * 0.16, sz * 0.16))
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
    # New item + arrow entering from the right
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    p.drawRect(QRectF(sz * 0.72, sz * 0.42, sz * 0.16, sz * 0.16))
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawLine(QPointF(sz * 0.68, sz * 0.50), QPointF(sz * 0.72, sz * 0.50))
    p.drawLine(QPointF(sz * 0.62, sz * 0.44), QPointF(sz * 0.68, sz * 0.50))
    p.drawLine(QPointF(sz * 0.62, sz * 0.56), QPointF(sz * 0.68, sz * 0.50))


def _ico_queue_dequeue(p: QPainter, sz: float, bg: QColor) -> None:
    """Horizontal queue with item leaving from the left — means 'dequeue'."""
    w = max(1.3, sz * 0.07)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Queue tube
    p.drawRect(QRectF(sz * 0.34, sz * 0.38, sz * 0.56, sz * 0.24))
    # Items inside queue (two slots)
    for i in range(2):
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor("white")))
        p.drawRect(QRectF(sz * (0.38 + i * 0.22), sz * 0.42, sz * 0.16, sz * 0.16))
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
    # Dequeued item + arrow leaving from the left
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    p.drawRect(QRectF(sz * 0.12, sz * 0.42, sz * 0.16, sz * 0.16))
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawLine(QPointF(sz * 0.28, sz * 0.50), QPointF(sz * 0.34, sz * 0.50))
    p.drawLine(QPointF(sz * 0.28, sz * 0.50), QPointF(sz * 0.22, sz * 0.44))
    p.drawLine(QPointF(sz * 0.28, sz * 0.50), QPointF(sz * 0.22, sz * 0.56))


def _ico_local_memory(p: QPainter, sz: float, bg: QColor) -> None:
    """Brain outline — means 'store / recall from memory'."""
    w = max(1.5, sz * 0.08)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Brain outline via cubic Bezier approximation
    brain = QPainterPath()
    brain.moveTo(sz * 0.50, sz * 0.88)
    # Left hemisphere
    brain.cubicTo(sz * 0.20, sz * 0.88, sz * 0.10, sz * 0.70, sz * 0.12, sz * 0.52)
    brain.cubicTo(sz * 0.08, sz * 0.34, sz * 0.18, sz * 0.18, sz * 0.36, sz * 0.14)
    brain.cubicTo(sz * 0.42, sz * 0.12, sz * 0.46, sz * 0.14, sz * 0.50, sz * 0.16)
    # Right hemisphere
    brain.cubicTo(sz * 0.54, sz * 0.14, sz * 0.58, sz * 0.12, sz * 0.64, sz * 0.14)
    brain.cubicTo(sz * 0.82, sz * 0.18, sz * 0.92, sz * 0.34, sz * 0.88, sz * 0.52)
    brain.cubicTo(sz * 0.90, sz * 0.70, sz * 0.80, sz * 0.88, sz * 0.50, sz * 0.88)
    p.drawPath(brain)
    # Centre sulcus (vertical divider)
    p.drawLine(QPointF(sz * 0.50, sz * 0.16), QPointF(sz * 0.50, sz * 0.88))
    # Two gyri curves per hemisphere
    p.drawArc(QRectF(sz * 0.16, sz * 0.36, sz * 0.22, sz * 0.20), 0, 180 * 16)
    p.drawArc(QRectF(sz * 0.62, sz * 0.36, sz * 0.22, sz * 0.20), 0, 180 * 16)


# ── System / Shell / Hardware icon functions ──────────────────────────────────

def _ico_shell_command(p: QPainter, sz: float, bg: QColor) -> None:
    """Terminal window with $ prompt — means 'execute shell command'."""
    w = max(1.2, sz * 0.07)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Terminal outer rect
    p.drawRoundedRect(QRectF(sz * 0.08, sz * 0.14, sz * 0.84, sz * 0.62),
                      sz * 0.06, sz * 0.06)
    # Title bar divider
    p.drawLine(QPointF(sz * 0.08, sz * 0.28), QPointF(sz * 0.92, sz * 0.28))
    # Three traffic-light dots in title bar
    p.setBrush(QBrush(QColor("white")))
    p.setPen(Qt.PenStyle.NoPen)
    for dot_x in [sz * 0.18, sz * 0.27, sz * 0.36]:
        p.drawEllipse(QPointF(dot_x, sz * 0.21), sz * 0.03, sz * 0.03)
    # Prompt: $ symbol
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawLine(QPointF(sz * 0.16, sz * 0.42), QPointF(sz * 0.22, sz * 0.42))
    p.drawLine(QPointF(sz * 0.22, sz * 0.42), QPointF(sz * 0.28, sz * 0.48))
    p.drawLine(QPointF(sz * 0.28, sz * 0.48), QPointF(sz * 0.22, sz * 0.54))
    p.drawLine(QPointF(sz * 0.22, sz * 0.54), QPointF(sz * 0.16, sz * 0.54))
    # Cursor line after prompt
    p.drawLine(QPointF(sz * 0.32, sz * 0.48), QPointF(sz * 0.60, sz * 0.48))
    # Blinking cursor
    p.setBrush(QBrush(QColor("white")))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRect(QRectF(sz * 0.61, sz * 0.42, sz * 0.06, sz * 0.12))
    # Second cmd line (dimmer — partial)
    p.setPen(QPen(QColor(255, 255, 255, 140), w))
    p.drawLine(QPointF(sz * 0.16, sz * 0.62), QPointF(sz * 0.46, sz * 0.62))


def _ico_tty_serial(p: QPainter, sz: float, bg: QColor) -> None:
    """D-sub / DB9 serial connector — means 'serial port / TTY / Arduino'."""
    w = max(1.2, sz * 0.07)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Connector trapezoidal shell
    shell = QPolygonF([
        QPointF(sz * 0.14, sz * 0.26),
        QPointF(sz * 0.86, sz * 0.26),
        QPointF(sz * 0.78, sz * 0.74),
        QPointF(sz * 0.22, sz * 0.74),
    ])
    p.drawPolygon(shell)
    # 5 top-row pins
    p.setBrush(QBrush(QColor("white")))
    p.setPen(Qt.PenStyle.NoPen)
    for i in range(5):
        cx = sz * (0.24 + i * 0.13)
        p.drawEllipse(QPointF(cx, sz * 0.38), sz * 0.04, sz * 0.04)
    # 4 bottom-row pins (offset)
    for i in range(4):
        cx = sz * (0.305 + i * 0.13)
        p.drawEllipse(QPointF(cx, sz * 0.58), sz * 0.04, sz * 0.04)
    # Cable line below connector
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawLine(QPointF(sz * 0.50, sz * 0.74), QPointF(sz * 0.50, sz * 0.90))


def _ico_spreadsheet(p: QPainter, sz: float, bg: QColor) -> None:
    """Spreadsheet grid with column header row — means 'CSV/Excel/TSV data'."""
    w = max(1.1, sz * 0.06)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Outer rect
    ox, oy, ow, oh = sz * 0.10, sz * 0.12, sz * 0.80, sz * 0.76
    p.drawRect(QRectF(ox, oy, ow, oh))
    # Header row fill
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    p.drawRect(QRectF(ox, oy, ow, sz * 0.16))
    # Column separators (3 vertical lines → 4 columns)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    for i in range(1, 4):
        cx = ox + ow * i / 4
        p.drawLine(QPointF(cx, oy), QPointF(cx, oy + oh))
    # Row separators (3 horizontal lines)
    for j in range(1, 4):
        ry = oy + sz * 0.16 + (oh - sz * 0.16) * j / 4
        p.drawLine(QPointF(ox, ry), QPointF(ox + ow, ry))
    # Header letter labels (A B C D) — tiny squares standing in as letters
    p.setPen(QPen(bg, w))
    col_labels = ["A", "B", "C", "D"]
    font = QFont()
    font.setPixelSize(max(5, int(sz * 0.13)))
    font.setBold(True)
    p.setFont(font)
    for i, lbl in enumerate(col_labels):
        cx = ox + ow * i / 4
        p.drawText(QRectF(cx + 1, oy + 1, ow / 4 - 2, sz * 0.14),
                   Qt.AlignmentFlag.AlignCenter, lbl)


# ── Networking / Sockets icon functions ───────────────────────────────────────

def _ico_socket_node(p: QPainter, sz: float, bg: QColor) -> None:
    """RJ45 network plug — means 'TCP/UDP socket connection'."""
    w = max(1.3, sz * 0.07)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Plug body
    px1, py1, pw, ph = sz * 0.22, sz * 0.30, sz * 0.56, sz * 0.34
    p.drawRoundedRect(QRectF(px1, py1, pw, ph), sz * 0.04, sz * 0.04)
    # Latch tab on top
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    p.drawRoundedRect(QRectF(sz * 0.36, sz * 0.22, sz * 0.28, sz * 0.10),
                      sz * 0.03, sz * 0.03)
    # 4 contact pins at bottom of plug
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    for i in range(4):
        cx = sz * (0.30 + i * 0.13)
        p.drawLine(QPointF(cx, py1 + ph - sz * 0.06), QPointF(cx, py1 + ph))
    # Cable cord below plug
    p.drawLine(QPointF(sz * 0.50, py1 + ph), QPointF(sz * 0.50, sz * 0.88))
    p.drawLine(QPointF(sz * 0.38, sz * 0.88), QPointF(sz * 0.62, sz * 0.88))


def _ico_websocket(p: QPainter, sz: float, bg: QColor) -> None:
    """Bidirectional streaming arrows with WS label — means 'WebSocket real-time'."""
    w = max(1.5, sz * 0.08)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Up arrow (send)
    p.drawLine(QPointF(sz * 0.30, sz * 0.66), QPointF(sz * 0.30, sz * 0.22))
    p.drawLine(QPointF(sz * 0.20, sz * 0.34), QPointF(sz * 0.30, sz * 0.22))
    p.drawLine(QPointF(sz * 0.40, sz * 0.34), QPointF(sz * 0.30, sz * 0.22))
    # Down arrow (receive)
    p.drawLine(QPointF(sz * 0.70, sz * 0.34), QPointF(sz * 0.70, sz * 0.78))
    p.drawLine(QPointF(sz * 0.60, sz * 0.66), QPointF(sz * 0.70, sz * 0.78))
    p.drawLine(QPointF(sz * 0.80, sz * 0.66), QPointF(sz * 0.70, sz * 0.78))
    # Lightning bolt (real-time indicator) between arrows
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    bolt = QPolygonF([
        QPointF(sz * 0.54, sz * 0.30),
        QPointF(sz * 0.46, sz * 0.50),
        QPointF(sz * 0.52, sz * 0.50),
        QPointF(sz * 0.44, sz * 0.72),
        QPointF(sz * 0.56, sz * 0.48),
        QPointF(sz * 0.50, sz * 0.48),
    ])
    p.drawPolygon(bolt)


def _ico_webhook_trigger(p: QPainter, sz: float, bg: QColor) -> None:
    """Inbound lightning bolt striking a target — means 'triggered by external event'."""
    w = max(1.5, sz * 0.08)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    # Target rings
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    cx, cy = sz * 0.66, sz * 0.62
    for r_mult in [0.22, 0.14, 0.07]:
        p.drawEllipse(QPointF(cx, cy), sz * r_mult, sz * r_mult)
    # Center dot
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    p.drawEllipse(QPointF(cx, cy), sz * 0.04, sz * 0.04)
    # Lightning bolt coming from upper-left
    p.setBrush(QBrush(QColor("white")))
    bolt = QPolygonF([
        QPointF(sz * 0.28, sz * 0.12),
        QPointF(sz * 0.14, sz * 0.38),
        QPointF(sz * 0.24, sz * 0.38),
        QPointF(sz * 0.10, sz * 0.64),
        QPointF(sz * 0.32, sz * 0.36),
        QPointF(sz * 0.22, sz * 0.36),
    ])
    p.setPen(Qt.PenStyle.NoPen)
    p.drawPolygon(bolt)


# ── AI / LLM Utilities icon functions ────────────────────────────────────────

def _ico_context_compact(p: QPainter, sz: float, bg: QColor) -> None:
    """Tall text block squeezed through a funnel to a short block — means 'compact context'."""
    w = max(1.3, sz * 0.07)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Input text lines (tall block, left)
    for ly in [sz * 0.18, sz * 0.28, sz * 0.38, sz * 0.48, sz * 0.58]:
        p.drawLine(QPointF(sz * 0.10, ly), QPointF(sz * 0.38, ly))
    # Compression funnel (V-shape pointing right)
    p.drawLine(QPointF(sz * 0.38, sz * 0.18), QPointF(sz * 0.58, sz * 0.38))
    p.drawLine(QPointF(sz * 0.38, sz * 0.58), QPointF(sz * 0.58, sz * 0.38))
    # Output text lines (short block, right)
    for ly in [sz * 0.30, sz * 0.42, sz * 0.54]:
        p.drawLine(QPointF(sz * 0.62, ly), QPointF(sz * 0.88, ly))
    # Arrow from funnel to output
    p.drawLine(QPointF(sz * 0.58, sz * 0.38), QPointF(sz * 0.62, sz * 0.38))


def _ico_conversation_history(p: QPainter, sz: float, bg: QColor) -> None:
    """Alternating left and right speech bubbles — means 'conversation thread'."""
    w = max(1.2, sz * 0.07)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Top bubble (user — left-aligned)
    bx1, by1, bw, bh = sz * 0.10, sz * 0.10, sz * 0.54, sz * 0.24
    p.drawRoundedRect(QRectF(bx1, by1, bw, bh), sz * 0.06, sz * 0.06)
    p.drawLine(QPointF(bx1 + sz * 0.08, by1 + bh), QPointF(bx1 + sz * 0.02, by1 + bh + sz * 0.08))
    # Top bubble content lines
    p.drawLine(QPointF(bx1 + sz * 0.06, by1 + sz * 0.07), QPointF(bx1 + bw - sz * 0.06, by1 + sz * 0.07))
    p.drawLine(QPointF(bx1 + sz * 0.06, by1 + sz * 0.14), QPointF(bx1 + bw - sz * 0.10, by1 + sz * 0.14))
    # Bottom bubble (assistant — right-aligned)
    bx2, by2 = sz * 0.36, sz * 0.54
    p.drawRoundedRect(QRectF(bx2, by2, bw, bh), sz * 0.06, sz * 0.06)
    p.drawLine(QPointF(bx2 + bw - sz * 0.08, by2 + bh), QPointF(bx2 + bw + sz * 0.02, by2 + bh + sz * 0.08))
    p.drawLine(QPointF(bx2 + sz * 0.06, by2 + sz * 0.07), QPointF(bx2 + bw - sz * 0.06, by2 + sz * 0.07))
    p.drawLine(QPointF(bx2 + sz * 0.06, by2 + sz * 0.14), QPointF(bx2 + bw - sz * 0.10, by2 + sz * 0.14))


# ── Text / Data Processing icon functions ─────────────────────────────────────

def _ico_regex(p: QPainter, sz: float, bg: QColor) -> None:
    """Regex slashes /.*/ with dot and star — means 'pattern match / regex'."""
    w = max(1.8, sz * 0.10)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Left slash /
    p.drawLine(QPointF(sz * 0.22, sz * 0.76), QPointF(sz * 0.36, sz * 0.24))
    # Right slash /
    p.drawLine(QPointF(sz * 0.64, sz * 0.76), QPointF(sz * 0.78, sz * 0.24))
    # Dot . between slashes (bottom-left area)
    p.setBrush(QBrush(QColor("white")))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QPointF(sz * 0.44, sz * 0.66), sz * 0.05, sz * 0.05)
    # Star * between slashes (top area)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    star_cx, star_cy = sz * 0.50, sz * 0.34
    for angle in range(0, 360, 60):
        a = math.radians(angle)
        p.drawLine(
            QPointF(star_cx + sz * 0.04 * math.cos(a), star_cy + sz * 0.04 * math.sin(a)),
            QPointF(star_cx + sz * 0.10 * math.cos(a), star_cy + sz * 0.10 * math.sin(a)),
        )


def _ico_template_render(p: QPainter, sz: float, bg: QColor) -> None:
    """{{ }} mustache braces with arrow to rendered output — means 'Jinja2 template'."""
    w = max(1.5, sz * 0.08)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Left {{ brace pair
    for ox in [sz * 0.06, sz * 0.14]:
        p.drawLine(QPointF(ox + sz * 0.06, sz * 0.22), QPointF(ox, sz * 0.32))
        p.drawLine(QPointF(ox, sz * 0.32), QPointF(ox + sz * 0.06, sz * 0.42))
    # Right }} brace pair
    for ox in [sz * 0.44, sz * 0.36]:
        p.drawLine(QPointF(ox, sz * 0.22), QPointF(ox + sz * 0.06, sz * 0.32))
        p.drawLine(QPointF(ox + sz * 0.06, sz * 0.32), QPointF(ox, sz * 0.42))
    # Content placeholder line inside braces
    p.drawLine(QPointF(sz * 0.22, sz * 0.32), QPointF(sz * 0.34, sz * 0.32))
    # Arrow →
    p.drawLine(QPointF(sz * 0.52, sz * 0.32), QPointF(sz * 0.64, sz * 0.32))
    p.drawLine(QPointF(sz * 0.56, sz * 0.26), QPointF(sz * 0.64, sz * 0.32))
    p.drawLine(QPointF(sz * 0.56, sz * 0.38), QPointF(sz * 0.64, sz * 0.32))
    # Rendered output (text lines)
    for ly in [sz * 0.54, sz * 0.66, sz * 0.78]:
        p.drawLine(QPointF(sz * 0.12, ly), QPointF(sz * 0.88, ly))


def _ico_json_parse(p: QPainter, sz: float, bg: QColor) -> None:
    """{ } curly braces with parse arrows — means 'JSON parse / serialize'."""
    w = max(1.8, sz * 0.10)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Left { brace
    p.drawLine(QPointF(sz * 0.34, sz * 0.20), QPointF(sz * 0.26, sz * 0.28))
    p.drawLine(QPointF(sz * 0.26, sz * 0.28), QPointF(sz * 0.20, sz * 0.34))
    p.drawLine(QPointF(sz * 0.20, sz * 0.34), QPointF(sz * 0.26, sz * 0.40))
    p.drawLine(QPointF(sz * 0.26, sz * 0.40), QPointF(sz * 0.34, sz * 0.48))
    # Right } brace
    p.drawLine(QPointF(sz * 0.66, sz * 0.20), QPointF(sz * 0.74, sz * 0.28))
    p.drawLine(QPointF(sz * 0.74, sz * 0.28), QPointF(sz * 0.80, sz * 0.34))
    p.drawLine(QPointF(sz * 0.80, sz * 0.34), QPointF(sz * 0.74, sz * 0.40))
    p.drawLine(QPointF(sz * 0.74, sz * 0.40), QPointF(sz * 0.66, sz * 0.48))
    # Two-way arrow below braces (parse ↔ serialize)
    p.drawLine(QPointF(sz * 0.20, sz * 0.66), QPointF(sz * 0.80, sz * 0.66))
    p.drawLine(QPointF(sz * 0.20, sz * 0.66), QPointF(sz * 0.28, sz * 0.60))
    p.drawLine(QPointF(sz * 0.20, sz * 0.66), QPointF(sz * 0.28, sz * 0.72))
    p.drawLine(QPointF(sz * 0.80, sz * 0.66), QPointF(sz * 0.72, sz * 0.60))
    p.drawLine(QPointF(sz * 0.80, sz * 0.66), QPointF(sz * 0.72, sz * 0.72))


def _ico_list_ops(p: QPainter, sz: float, bg: QColor) -> None:
    """Sorted list lines with filter funnel — means 'filter / sort / slice list'."""
    w = max(1.3, sz * 0.07)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Funnel (filter) on the left
    p.drawLine(QPointF(sz * 0.10, sz * 0.20), QPointF(sz * 0.42, sz * 0.20))
    p.drawLine(QPointF(sz * 0.10, sz * 0.20), QPointF(sz * 0.22, sz * 0.40))
    p.drawLine(QPointF(sz * 0.42, sz * 0.20), QPointF(sz * 0.30, sz * 0.40))
    p.drawLine(QPointF(sz * 0.22, sz * 0.40), QPointF(sz * 0.30, sz * 0.40))
    p.drawLine(QPointF(sz * 0.26, sz * 0.40), QPointF(sz * 0.26, sz * 0.56))
    # Sort arrows on right (ascending indicator)
    p.drawLine(QPointF(sz * 0.58, sz * 0.28), QPointF(sz * 0.58, sz * 0.72))
    p.drawLine(QPointF(sz * 0.50, sz * 0.36), QPointF(sz * 0.58, sz * 0.28))
    p.drawLine(QPointF(sz * 0.66, sz * 0.36), QPointF(sz * 0.58, sz * 0.28))
    # Three descending-length list lines
    for i, line_w in enumerate([0.30, 0.22, 0.14]):
        ly = sz * (0.52 + i * 0.14)
        p.drawLine(QPointF(sz * 0.12, ly), QPointF(sz * (0.12 + line_w * 2.2), ly))


def _ico_string_ops(p: QPainter, sz: float, bg: QColor) -> None:
    """Quoted string "Aa" with scissors — means 'string operations / transform'."""
    w = max(1.5, sz * 0.08)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Opening quote mark
    p.drawLine(QPointF(sz * 0.12, sz * 0.18), QPointF(sz * 0.12, sz * 0.28))
    p.drawLine(QPointF(sz * 0.12, sz * 0.28), QPointF(sz * 0.18, sz * 0.34))
    # "Aa" text representation (two capital A shapes)
    # Large A
    p.drawLine(QPointF(sz * 0.22, sz * 0.62), QPointF(sz * 0.32, sz * 0.28))
    p.drawLine(QPointF(sz * 0.32, sz * 0.28), QPointF(sz * 0.42, sz * 0.62))
    p.drawLine(QPointF(sz * 0.25, sz * 0.50), QPointF(sz * 0.39, sz * 0.50))
    # Small a (circle + stem)
    p.drawEllipse(QPointF(sz * 0.55, sz * 0.52), sz * 0.08, sz * 0.08)
    p.drawLine(QPointF(sz * 0.63, sz * 0.44), QPointF(sz * 0.63, sz * 0.60))
    # Closing quote mark
    p.drawLine(QPointF(sz * 0.76, sz * 0.34), QPointF(sz * 0.82, sz * 0.28))
    p.drawLine(QPointF(sz * 0.82, sz * 0.28), QPointF(sz * 0.82, sz * 0.18))
    # Scissors blades (bottom)
    p.drawLine(QPointF(sz * 0.24, sz * 0.80), QPointF(sz * 0.50, sz * 0.72))
    p.drawLine(QPointF(sz * 0.24, sz * 0.68), QPointF(sz * 0.50, sz * 0.76))
    p.setBrush(QBrush(QColor("white")))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QPointF(sz * 0.20, sz * 0.74), sz * 0.06, sz * 0.06)


# ── Resilience / Flow Utilities icon functions ────────────────────────────────

def _ico_retry(p: QPainter, sz: float, bg: QColor) -> None:
    """Circular arrow with warning triangle — means 'retry on failure'."""
    w = max(1.5, sz * 0.08)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Circular retry arrow (open at top-right, smaller to leave room for warning)
    p.drawArc(QRectF(sz * 0.10, sz * 0.10, sz * 0.48, sz * 0.48),
              45 * 16, 270 * 16)
    # Arrow tip
    tip_x, tip_y = sz * 0.52, sz * 0.20
    p.drawLine(QPointF(tip_x, tip_y), QPointF(tip_x + sz * 0.08, tip_y - sz * 0.06))
    p.drawLine(QPointF(tip_x, tip_y), QPointF(tip_x + sz * 0.10, tip_y + sz * 0.04))
    # Warning triangle (bottom-right)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    tri = QPolygonF([
        QPointF(sz * 0.74, sz * 0.56),
        QPointF(sz * 0.54, sz * 0.90),
        QPointF(sz * 0.94, sz * 0.90),
    ])
    p.drawPolygon(tri)
    # ! inside warning triangle
    p.setPen(QPen(bg, w * 0.9, Qt.PenStyle.SolidLine,
                  Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    p.drawLine(QPointF(sz * 0.74, sz * 0.64), QPointF(sz * 0.74, sz * 0.76))
    p.setBrush(QBrush(bg))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QPointF(sz * 0.74, sz * 0.83), sz * 0.03, sz * 0.03)


def _ico_rate_limiter(p: QPainter, sz: float, bg: QColor) -> None:
    """Speedometer dial with needle — means 'rate limit / throttle'."""
    w = max(1.5, sz * 0.08)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    cx, cy, r = sz * 0.50, sz * 0.58, sz * 0.38
    # Dial arc (220 degrees: from ~200° to ~-20° = left to right across bottom)
    p.drawArc(QRectF(cx - r, cy - r, r * 2, r * 2), 200 * 16, -240 * 16)
    # Tick marks at 7 positions along the arc
    for i in range(7):
        angle_deg = 200 - i * 40
        a = math.radians(angle_deg)
        tick_outer = r
        tick_inner = r - sz * 0.08
        p.drawLine(
            QPointF(cx + tick_inner * math.cos(a), cy - tick_inner * math.sin(a)),
            QPointF(cx + tick_outer * math.cos(a), cy - tick_outer * math.sin(a)),
        )
    # Needle pointing to ~2/3 (warning zone)
    needle_angle = math.radians(200 - 160)  # 160/240 of the arc
    nx = cx + (r - sz * 0.08) * math.cos(needle_angle)
    ny = cy - (r - sz * 0.08) * math.sin(needle_angle)
    p.setPen(QPen(QColor("white"), w * 1.3, Qt.PenStyle.SolidLine,
                  Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    p.drawLine(QPointF(cx, cy), QPointF(nx, ny))
    # Center pivot
    p.setBrush(QBrush(QColor("white")))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QPointF(cx, cy), sz * 0.05, sz * 0.05)


# ── Messaging / Notifications icon functions ──────────────────────────────────

def _ico_email_send(p: QPainter, sz: float, bg: QColor) -> None:
    """Envelope with outbound arrow — means 'send email'."""
    w = max(1.3, sz * 0.07)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Envelope body
    ex, ey, ew, eh = sz * 0.10, sz * 0.26, sz * 0.60, sz * 0.44
    p.drawRect(QRectF(ex, ey, ew, eh))
    # Envelope flap (V-fold)
    p.drawLine(QPointF(ex, ey), QPointF(ex + ew / 2, ey + eh * 0.52))
    p.drawLine(QPointF(ex + ew, ey), QPointF(ex + ew / 2, ey + eh * 0.52))
    # Outbound arrow (right of envelope)
    p.drawLine(QPointF(sz * 0.74, sz * 0.48), QPointF(sz * 0.92, sz * 0.48))
    p.drawLine(QPointF(sz * 0.84, sz * 0.40), QPointF(sz * 0.92, sz * 0.48))
    p.drawLine(QPointF(sz * 0.84, sz * 0.56), QPointF(sz * 0.92, sz * 0.48))


def _ico_email_read(p: QPainter, sz: float, bg: QColor) -> None:
    """Open envelope with letter rising out — means 'read / receive email'."""
    w = max(1.3, sz * 0.07)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Envelope body
    ex, ey, ew, eh = sz * 0.12, sz * 0.44, sz * 0.70, sz * 0.44
    p.drawRect(QRectF(ex, ey, ew, eh))
    # Open flap (flipped up)
    p.drawLine(QPointF(ex, ey), QPointF(ex + ew / 2, ey - eh * 0.40))
    p.drawLine(QPointF(ex + ew, ey), QPointF(ex + ew / 2, ey - eh * 0.40))
    # Letter / paper sticking up out of envelope
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    p.drawRect(QRectF(ex + ew * 0.24, sz * 0.18, ew * 0.52, sz * 0.30))
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Lines on the letter
    for ly in [sz * 0.24, sz * 0.31, sz * 0.38]:
        p.drawLine(QPointF(ex + ew * 0.32, ly), QPointF(ex + ew * 0.68, ly))


def _ico_notification(p: QPainter, sz: float, bg: QColor) -> None:
    """Bell with notification badge dot — means 'send notification'."""
    w = max(1.5, sz * 0.08)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Bell body (dome shape)
    bell = QPainterPath()
    bell.moveTo(sz * 0.26, sz * 0.74)
    bell.lineTo(sz * 0.18, sz * 0.74)
    bell.cubicTo(sz * 0.18, sz * 0.30, sz * 0.30, sz * 0.20, sz * 0.50, sz * 0.20)
    bell.cubicTo(sz * 0.70, sz * 0.20, sz * 0.82, sz * 0.30, sz * 0.82, sz * 0.74)
    bell.lineTo(sz * 0.74, sz * 0.74)
    p.drawPath(bell)
    # Bell base line
    p.drawLine(QPointF(sz * 0.18, sz * 0.74), QPointF(sz * 0.82, sz * 0.74))
    # Bell clapper
    p.drawArc(QRectF(sz * 0.40, sz * 0.74, sz * 0.20, sz * 0.12), 0, -180 * 16)
    # Stem at top
    p.drawLine(QPointF(sz * 0.50, sz * 0.10), QPointF(sz * 0.50, sz * 0.20))
    # Notification badge (filled circle, top-right)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("white")))
    p.drawEllipse(QPointF(sz * 0.76, sz * 0.24), sz * 0.12, sz * 0.12)


# ── Security / Configuration icon functions ───────────────────────────────────

def _ico_secret(p: QPainter, sz: float, bg: QColor) -> None:
    """Closed padlock — means 'secret / credential / secure value'."""
    w = max(1.5, sz * 0.08)
    pen = QPen(QColor("white"), w, Qt.PenStyle.SolidLine,
               Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    # Lock body
    bx, by, bw, bh = sz * 0.22, sz * 0.46, sz * 0.56, sz * 0.44
    p.drawRoundedRect(QRectF(bx, by, bw, bh), sz * 0.07, sz * 0.07)
    # Shackle (arc)
    shackle_r = sz * 0.18
    p.drawArc(QRectF(bx + bw / 2 - shackle_r, by - shackle_r * 1.2,
                     shackle_r * 2, shackle_r * 2),
              0, 180 * 16)
    # Keyhole
    p.setBrush(QBrush(QColor("white")))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QPointF(bx + bw / 2, by + bh * 0.38), sz * 0.07, sz * 0.07)
    p.setPen(Qt.PenStyle.NoPen)
    kh = QPolygonF([
        QPointF(bx + bw / 2 - sz * 0.04, by + bh * 0.46),
        QPointF(bx + bw / 2 + sz * 0.04, by + bh * 0.46),
        QPointF(bx + bw / 2 + sz * 0.02, by + bh * 0.68),
        QPointF(bx + bw / 2 - sz * 0.02, by + bh * 0.68),
    ])
    p.drawPolygon(kh)


# Dispatch map: type_id → drawing function (p, sz, bg) → None
_ICON_DRAW: dict[str, Callable[..., None]] = {
    "start_node":                _ico_start,
    "stop_node":                 _ico_stop,
    "basic_node":                _ico_gear,
    "router_node":               _ico_fork,
    "llm_prompt_node":           _ico_chat_bubble,
    "json_llm_node":             _ico_json_llm,
    "classifier_node":           _ico_funnel,
    "python_tool_node":          _ico_terminal,
    "file_reader_node":          _ico_document,
    "file_writer_node":          _ico_file_writer,
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
    # ── AI / Reasoning ────────────────────────────────────────────────────────
    "chain_of_thought_node":     _ico_chain_of_thought,
    "majority_vote_node":        _ico_majority_vote,
    "supervisor_node":           _ico_supervisor,
    "debate_advocate_node":      _ico_debate_advocate,
    "debate_judge_node":         _ico_debate_judge,
    # ── Web / Search ──────────────────────────────────────────────────────────
    "web_search_node":           _ico_web_search,
    "web_scrape_node":           _ico_web_scrape,
    "api_call_node":             _ico_api_call,
    # ── Data / Vector / Embeddings ────────────────────────────────────────────
    "text_chunk_node":           _ico_text_chunk,
    "embed_node":                _ico_embed,
    "vector_index_node":         _ico_vector_index,
    "vector_retrieve_node":      _ico_vector_retrieve,
    # ── Database / SQL ────────────────────────────────────────────────────────
    "db_schema_node":            _ico_db_schema,
    "nl_to_sql_node":            _ico_nl_to_sql,
    "sql_execute_node":          _ico_sql_execute,
    # ── Voice / Audio ─────────────────────────────────────────────────────────
    "speech_to_text_node":       _ico_speech_to_text,
    "text_to_speech_node":       _ico_text_to_speech,
    # ── Document / Vision ─────────────────────────────────────────────────────
    "pdf_extract_node":          _ico_pdf_extract,
    "image_vision_node":         _ico_image_vision,
    "data_validate_node":        _ico_data_validate,
    # ── Code / Execution ──────────────────────────────────────────────────────
    "code_gen_node":             _ico_code_gen,
    "code_exec_node":            _ico_code_exec,
    "test_gen_node":             _ico_test_gen,
    # ── Data Processing ───────────────────────────────────────────────────────
    "map_node":                  _ico_map_node,
    "reduce_node":               _ico_reduce_node,
    "condition_node":            _ico_condition,
    "loop_counter_node":         _ico_loop_counter,
    "transform_node":            _ico_transform,
    "merge_node":                _ico_merge,
    # ── Calendar ──────────────────────────────────────────────────────────────
    "calendar_read_node":        _ico_calendar_read,
    "calendar_write_node":       _ico_calendar_write,
    # ── MCP / Agent Protocol ──────────────────────────────────────────────────
    "mcp_tool_node":             _ico_mcp_tool,
    "a2a_send_node":             _ico_a2a_send,
    "a2a_receive_node":          _ico_a2a_receive,
    # ── Observability / Utility ───────────────────────────────────────────────
    "log_node":                  _ico_log_node,
    "timer_node":                _ico_timer_node,
    "cache_node":                _ico_cache_node,
    "trace_node":                _ico_trace_node,
    # ── Data Structures / Memory ──────────────────────────────────────────────
    "registry_node":             _ico_registry,
    "stack_push_node":           _ico_stack_push,
    "stack_pop_node":            _ico_stack_pop,
    "queue_enqueue_node":        _ico_queue_enqueue,
    "queue_dequeue_node":        _ico_queue_dequeue,
    "local_memory_node":         _ico_local_memory,
    # ── System / Shell / Hardware ─────────────────────────────────────────────
    "shell_command_node":        _ico_shell_command,
    "tty_serial_node":           _ico_tty_serial,
    "spreadsheet_node":          _ico_spreadsheet,
    # ── Networking / Sockets ──────────────────────────────────────────────────
    "socket_node":               _ico_socket_node,
    "websocket_node":            _ico_websocket,
    "webhook_trigger_node":      _ico_webhook_trigger,
    # ── AI / LLM Utilities ────────────────────────────────────────────────────
    "context_compact_node":      _ico_context_compact,
    "conversation_history_node": _ico_conversation_history,
    # ── Text / Data Processing ────────────────────────────────────────────────
    "regex_node":                _ico_regex,
    "template_render_node":      _ico_template_render,
    "json_parse_node":           _ico_json_parse,
    "list_ops_node":             _ico_list_ops,
    "string_ops_node":           _ico_string_ops,
    # ── Resilience / Flow Utilities ───────────────────────────────────────────
    "retry_node":                _ico_retry,
    "rate_limiter_node":         _ico_rate_limiter,
    # ── Messaging / Notifications ─────────────────────────────────────────────
    "email_send_node":           _ico_email_send,
    "email_read_node":           _ico_email_read,
    "notification_node":         _ico_notification,
    # ── Security / Configuration ──────────────────────────────────────────────
    "secret_node":               _ico_secret,
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

    # Type-specific shape — all functions share (p, sz, bg) signature
    draw_fn = _ICON_DRAW.get(type_id)
    if draw_fn is not None:
        draw_fn(p, float(size), bg)
    else:
        # Fallback: two-letter initials for unknown / custom node types
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

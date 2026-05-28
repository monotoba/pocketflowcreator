"""canvas — graph editor widgets.

This package replaces the monolithic ``app/canvas.py`` module.  All names that
were previously importable as ``pocketflow_creator.app.canvas.<name>`` remain
available from this package, so no external import needs to change.
"""
from __future__ import annotations

from pocketflow_creator.app.canvas.icons import (
    NODE_TYPE_COLOR,
    _ICON_DRAW,
    _PALETTE_ITEMS_EX,
    make_node_icon,
)
from pocketflow_creator.app.canvas.items import (
    _DARK_COLORS,
    _HEADER_H,
    _HEIGHT,
    _LIGHT_COLORS,
    _PORT_R,
    _PORT_ROW_H,
    _WIDTH,
    _node_height,
    EdgeItem,
    NodeItem,
)
from pocketflow_creator.app.canvas.scene import GraphScene
from pocketflow_creator.app.canvas.view import GraphView
from pocketflow_creator.app.canvas.palette import (
    _MIME_NODE_SNIPPET,
    _MIME_NODE_TYPE,
    _ROLE_SNIPPET,
    _load_snippets,
    PaletteWidget,
)

__all__ = [
    # icons
    "NODE_TYPE_COLOR",
    "_ICON_DRAW",
    "_PALETTE_ITEMS_EX",
    "make_node_icon",
    # items
    "_DARK_COLORS",
    "_HEADER_H",
    "_HEIGHT",
    "_LIGHT_COLORS",
    "_PORT_R",
    "_PORT_ROW_H",
    "_WIDTH",
    "_node_height",
    "EdgeItem",
    "NodeItem",
    # scene
    "GraphScene",
    # view
    "GraphView",
    # palette
    "_MIME_NODE_SNIPPET",
    "_MIME_NODE_TYPE",
    "_ROLE_SNIPPET",
    "_load_snippets",
    "PaletteWidget",
]

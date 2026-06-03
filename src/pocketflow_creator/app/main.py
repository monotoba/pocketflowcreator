from __future__ import annotations

import ast
import copy
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import yaml

try:
    from PySide6.QtCore import QLocale, QPointF, QRectF, QSettings, QSize, Qt, QTranslator, QUrl
    from PySide6.QtGui import (
        QAction,
        QBrush,
        QColor,
        QDesktopServices,
        QImage,
        QKeySequence,
        QPainter,
        QUndoStack,
    )
    from PySide6.QtWidgets import (
        QApplication,
        QButtonGroup,
        QCheckBox,
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QDockWidget,
        QFileDialog,
        QFormLayout,
        QGroupBox,
        QHBoxLayout,
        QInputDialog,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMainWindow,
        QMenu,
        QMessageBox,
        QPlainTextEdit,
        QPushButton,
        QRadioButton,
        QSplitter,
        QTableWidget,
        QTableWidgetItem,
        QTabWidget,
        QTextBrowser,
        QToolBar,
        QTreeWidget,
        QTreeWidgetItem,
        QVBoxLayout,
        QWidget,
    )

    from pocketflow_creator.app.canvas import (
        EdgeItem,
        GraphScene,
        GraphView,
        NodeItem,
        PaletteWidget,
        make_node_icon,
    )
    from pocketflow_creator.app.commands import GraphSnapshotCommand
    from pocketflow_creator.app.editors import PythonHighlighter, YamlHighlighter
    from pocketflow_creator.app.help_browser import HelpBrowser
    from pocketflow_creator.app.node_type_wizard import NodeTypeWizard
except Exception:  # pragma: no cover - PySide6/EGL unavailable in headless CI
    QApplication = None  # type: ignore[assignment,misc]
    QMainWindow = object  # type: ignore[assignment,misc]

from pocketflow_creator.app import code_manager, run_controller
from pocketflow_creator.app.dialogs.auto_arrange_dialog import AutoArrangeDialog
from pocketflow_creator.app.dialogs.customize_toolbar_dialog import CustomizeToolbarDialog
from pocketflow_creator.app.dialogs.provider_manager_dialog import exec_provider_manager
from pocketflow_creator.app.dialogs.shared_store_designer_dialog import open_shared_store_designer
from pocketflow_creator.app.settings_keys import (
    _APP,
    _ORG,
    _SKEY_DARK_MODE,
    _SKEY_LAYOUT_GEOMETRY,
    _SKEY_LAYOUT_SPLITTER,
    _SKEY_LAYOUT_STATE,
    _SKEY_LOCALE,
    _SKEY_RECENT,
    _SKEY_THEME,
    _SKEY_TOOLBAR_ORDER,
)
from pocketflow_creator.builtin_node_types import BUILTIN_NODE_TYPES, get_nodes_by_category
from pocketflow_creator.generation.dataflow_report import generate_dataflow_report
from pocketflow_creator.generation.exporter import Exporter
from pocketflow_creator.generation.python_generator import PythonGenerator
from pocketflow_creator.generation.report import generate_project_report
from pocketflow_creator.graph_io import GraphLoader, GraphSaver
from pocketflow_creator.model.graph_model import EdgeModel, GraphModel, NodeModel
from pocketflow_creator.model.node_type import NodeTypeDefinition
from pocketflow_creator.model.project import ProjectModel
from pocketflow_creator.node_package_loader import (
    discover_addon_nodes,
    discover_user_nodes,
    get_addon_node_groups,
    get_all_addon_nodes,
    get_all_user_nodes,
    get_user_nodes_dir,
)
from pocketflow_creator.project_io import ProjectLoader, ProjectSaver
from pocketflow_creator.runtime.runner import FlowRunner, RunStep, RunTrace, StepController
from pocketflow_creator.validation.graph_validator import GraphValidator

_MAX_RECENT = 5
_VERSION = "0.2.0"
_TEMP_PROJECT_DIR = ".pocketflow_creator_temp"
_PNG_BACKGROUND_DARK = 0xFF1A1A1A  # ARGB dark background for PNG export


def _node_skeleton_text(type_id: str, base_class: str) -> str:
    class_name = "".join(p.capitalize() for p in type_id.replace("-", "_").split("_"))
    resolved = base_class if base_class else "Node"
    return (
        f"from __future__ import annotations\n\n\n"
        f"class {class_name}({resolved}):\n"
        f"    \"\"\"{type_id}\"\"\"\n\n"
        f"    def prep(self, shared: dict) -> object:\n"
        f"        return None\n\n"
        f"    def exec(self, prep_res: object) -> object:\n"
        f"        return None\n\n"
        f"    def post(self, shared: dict, prep_res: object, exec_res: object) -> str:\n"
        f"        return 'default'\n"
    )
_EDITOR_TABS: frozenset[str] = frozenset({"Python", "Markdown", "YAML"})
_ROLE_PATH = Qt.ItemDataRole.UserRole  # type: ignore[attr-defined]
_ROLE_KIND = Qt.ItemDataRole(Qt.ItemDataRole.UserRole.value + 1)  # type: ignore[attr-defined]


class MainWindow(QMainWindow):
    """RAD-style main window for PocketFlow Creator."""

    def __init__(self) -> None:
        super().__init__()
        self._project: ProjectModel | None = None
        self._is_temp_project: bool = False
        self._graphs: dict[str, GraphModel] = {}
        self._active_graph_rel: str | None = None
        self._bottom_editors: dict[str, QPlainTextEdit] = {}
        self._bottom_tab_paths: dict[str, Path | None] = {}
        self._active_highlighters: dict[str, object] = {}
        self._undo_stack = QUndoStack(self)
        self._recent: list[Path] = []
        self._current_node: NodeModel | None = None
        self._current_node_item: NodeItem | None = None
        self._current_edge: EdgeModel | None = None
        self._pre_drag_graph: GraphModel | None = None
        self._inspector_snapshot: GraphModel | None = None
        self._debug_controller: StepController | None = None
        self._debug_thread: object = None  # QThread when active
        self._breakpoints: set[str] = set()
        _settings = QSettings(_ORG, _APP)
        # Migrate old bool setting → string if needed
        _stored = _settings.value(_SKEY_THEME, None)
        if _stored is None:
            _old = _settings.value(_SKEY_DARK_MODE, None)
            _stored = "dark" if _old is True or _old == "true" else (
                "light" if _old is False or _old == "false" else "system"
            )
        self._theme_mode: str = str(_stored)
        self._dark_mode: bool = self._resolve_dark()
        self._stop_action: QAction  # assigned in _build_menu_bar
        self._resume_action: QAction  # assigned in _build_menu_bar
        # Assigned by their respective _build_* methods:
        self._explorer_tree: QTreeWidget
        self._bottom_tab_widget: QTabWidget
        self._explorer_dock: QDockWidget
        self._palette_dock: QDockWidget
        self._inspector_dock: QDockWidget
        self._bottom_dock: QDockWidget
        self._markdown_preview: QTextBrowser
        self._md_splitter: QSplitter
        self._recent_menu: QMenu
        self._inspector: QTreeWidget
        self._graph_view: GraphView
        self._graph_scene = GraphScene()
        self.setWindowTitle(self.tr("PocketFlow Creator"))
        self.resize(1400, 900)
        self._build_menu_bar()
        # Discover add-on and user node packages before building toolbar/palette.
        _addon_defns, self._addon_node_load_errors = discover_addon_nodes()
        _user_defns, self._user_node_load_errors = discover_user_nodes()
        self._build_node_toolbar()
        self._build_central_area()
        self._build_docks()
        self._graph_scene.node_item_selected.connect(self._on_node_item_selected)
        self._graph_scene.edge_item_selected.connect(self._on_edge_item_selected)
        self._graph_scene.selection_cleared.connect(self._on_selection_cleared)
        self._graph_scene.node_item_double_clicked.connect(self._on_node_double_clicked)
        self._graph_scene.node_created.connect(self._on_node_created)
        self._graph_scene.node_deleted.connect(self._on_node_deleted)
        self._graph_scene.edge_deleted.connect(self._on_edge_deleted)
        self._graph_scene.edge_creation_requested.connect(self._on_edge_creation_requested)
        self._graph_scene.set_start_node_requested.connect(self._on_set_start_node)
        self._graph_scene.node_drag_started.connect(self._on_node_drag_started)
        self._graph_scene.node_move_finished.connect(self._on_node_move_finished)
        self._graph_scene.node_open_code_requested.connect(self._on_node_double_clicked)
        self._graph_scene.node_rename_requested.connect(self._on_node_rename_requested)
        self._graph_scene.node_toggle_breakpoint_requested.connect(self._on_node_toggle_breakpoint_requested)
        self._graph_scene.node_duplicate_requested.connect(self._on_node_duplicate_requested)
        self._graph_scene.node_delete_requested.connect(self._on_node_delete_requested)
        self._inspector.itemChanged.connect(self._on_inspector_item_changed)
        self._explorer_tree.itemDoubleClicked.connect(
            self._on_explorer_item_double_clicked
        )
        self._bottom_editors["YAML"].textChanged.connect(self._on_yaml_editor_changed)
        self._bottom_editors["Markdown"].textChanged.connect(
            self._on_markdown_editor_changed
        )
        self._recent = self._load_recent()
        self._update_recent_menu()
        self._apply_theme()
        self._cleanup_temp_project()  # remove any leftover from a previous session
        self._create_untitled_flow()
        self._restore_layout()  # apply saved window geometry and dock state

    # ------------------------------------------------------------------ menus

    def _build_menu_bar(self) -> None:
        file_menu = self.menuBar().addMenu(self.tr("File"))
        act = file_menu.addAction(self.tr("New Project..."), self._on_new_project)
        act.setShortcut(QKeySequence.StandardKey.New)
        file_menu.addAction(self.tr("New From Template..."), self._on_new_from_template)
        act = file_menu.addAction(self.tr("Open Project..."), self._on_open_project)
        act.setShortcut(QKeySequence.StandardKey.Open)
        file_menu.addSeparator()
        self._recent_menu = file_menu.addMenu(self.tr("Recent Projects"))
        file_menu.addSeparator()
        act = file_menu.addAction(self.tr("Save"), self._on_save)
        act.setShortcut(QKeySequence.StandardKey.Save)
        act = file_menu.addAction(self.tr("Save As..."), self._on_save_as)
        act.setShortcut(QKeySequence.StandardKey.SaveAs)
        act = file_menu.addAction(self.tr("Save All"), self._on_save_all)
        act.setShortcut(QKeySequence("Ctrl+Shift+S"))
        file_menu.addSeparator()
        act = file_menu.addAction(
            self.tr("Export PocketFlow Project..."), self._on_export_project
        )
        act.setShortcut(QKeySequence("Ctrl+E"))
        file_menu.addAction(self.tr("Project Settings..."), self._on_project_settings)
        file_menu.addSeparator()
        act = file_menu.addAction(self.tr("Exit"), self.close)
        act.setShortcut(QKeySequence.StandardKey.Quit)

        edit_menu = self.menuBar().addMenu(self.tr("Edit"))
        undo_act = edit_menu.addAction(self.tr("Undo"), self._on_undo)
        undo_act.setShortcut(QKeySequence.StandardKey.Undo)
        redo_act = edit_menu.addAction(self.tr("Redo"), self._on_redo)
        redo_act.setShortcut(QKeySequence.StandardKey.Redo)
        edit_menu.addSeparator()
        cut_act = edit_menu.addAction(self.tr("Cut"))
        cut_act.setShortcut(QKeySequence.StandardKey.Cut)
        copy_act = edit_menu.addAction(self.tr("Copy"))
        copy_act.setShortcut(QKeySequence.StandardKey.Copy)
        paste_act = edit_menu.addAction(self.tr("Paste"))
        paste_act.setShortcut(QKeySequence.StandardKey.Paste)
        edit_menu.addAction(self.tr("Duplicate"))
        del_act = edit_menu.addAction(self.tr("Delete"), self._on_delete_selected)
        del_act.setShortcut(QKeySequence.StandardKey.Delete)
        find_act = edit_menu.addAction(self.tr("Find..."))
        find_act.setShortcut(QKeySequence.StandardKey.Find)

        view_menu = self.menuBar().addMenu(self.tr("View"))
        for name in [
            self.tr("Project Explorer"),
            self.tr("Component Palette"),
            self.tr("Object Inspector"),
        ]:
            view_menu.addAction(name)
        act = view_menu.addAction(self.tr("Zoom In"), self._on_zoom_in)
        act.setShortcut(QKeySequence("Ctrl++"))
        act = view_menu.addAction(self.tr("Zoom Out"), self._on_zoom_out)
        act.setShortcut(QKeySequence("Ctrl+-"))
        act = view_menu.addAction(self.tr("Zoom to Fit"), self._on_zoom_to_fit)
        act.setShortcut(QKeySequence("Ctrl+0"))
        act = view_menu.addAction(self.tr("Zoom to Node"), self._on_zoom_to_node)
        act.setShortcut(QKeySequence("Ctrl+Shift+Z"))
        act = view_menu.addAction(self.tr("Auto Arrange…"), self._on_auto_arrange)
        act.setShortcut(QKeySequence("Ctrl+Shift+L"))

        project_menu = self.menuBar().addMenu(self.tr("Project"))
        act = project_menu.addAction(self.tr("Validate Project"), self._on_validate_project)
        act.setShortcut(QKeySequence("Ctrl+Shift+V"))
        act = project_menu.addAction(self.tr("Generate Code"), self._on_generate_code)
        act.setShortcut(QKeySequence("Ctrl+G"))
        project_menu.addAction(self.tr("Open Project Folder"), self._on_open_project_folder)
        project_menu.addAction(self.tr("Export Graph Image..."), self._on_export_graph_image)
        project_menu.addAction(
            self.tr("Export Project Report..."), self._on_export_project_report
        )
        project_menu.addAction(
            self.tr("Data Flow Report"), self._on_dataflow_report
        )
        project_menu.addAction(self.tr("Provider Profiles..."))

        flow_menu = self.menuBar().addMenu(self.tr("Flow"))
        flow_menu.addAction(self.tr("New Flow..."), self._create_untitled_flow)
        for name in [
            self.tr("New Subflow..."),
            self.tr("Validate Active Flow"),
        ]:
            flow_menu.addAction(name)

        node_menu = self.menuBar().addMenu(self.tr("Node"))
        node_menu.addAction(self.tr("New Custom Node Type..."), self._on_new_custom_node_type)
        node_menu.addAction(self.tr("Generate Node Skeleton"), self._on_generate_node_skeleton)
        act = node_menu.addAction(self.tr("Toggle Breakpoint"), self._on_toggle_breakpoint)
        act.setShortcut(QKeySequence("F9"))
        node_menu.addAction(self.tr("Validate Selected Node"))

        run_menu = self.menuBar().addMenu(self.tr("Run"))
        act = run_menu.addAction(self.tr("Run Active Flow"), self._on_run_active_flow)
        act.setShortcut(QKeySequence("F5"))
        act = run_menu.addAction(self.tr("Debug Active Flow"), self._on_debug_active_flow)
        act.setShortcut(QKeySequence("Shift+F5"))
        act = run_menu.addAction(self.tr("Run Tests"), self._on_run_tests)
        act.setShortcut(QKeySequence("Ctrl+T"))
        run_menu.addSeparator()
        self._stop_action = run_menu.addAction(self.tr("Stop"), self._on_stop_debug)
        self._stop_action.setEnabled(False)
        self._resume_action = run_menu.addAction(self.tr("Resume"), self._on_resume_debug)
        self._resume_action.setEnabled(False)

        tools_menu = self.menuBar().addMenu(self.tr("Tools"))
        tools_menu.addAction(self.tr("Provider Manager..."), self._on_provider_manager)
        tools_menu.addAction(self.tr("Tool Registry..."), self._on_tool_registry)
        tools_menu.addAction(
            self.tr("Shared Store Inspector..."), self._on_shared_store_inspector
        )
        tools_menu.addAction(self.tr("Node Type Library..."), self._on_node_type_library)
        tools_menu.addAction(self.tr("Options..."), self._on_options)

        window_menu = self.menuBar().addMenu(self.tr("Window"))
        window_menu.addAction(self.tr("Save Layout"), self._on_save_layout)
        window_menu.addAction(self.tr("Reset Layout"), self._on_reset_layout)
        window_menu.addAction(self.tr("Default Layout"), self._on_default_layout)
        window_menu.addSeparator()
        _next = window_menu.addAction(self.tr("Next Tab"), self._on_next_tab)
        _next.setShortcut(QKeySequence("Ctrl+Tab"))
        _prev = window_menu.addAction(self.tr("Previous Tab"), self._on_prev_tab)
        _prev.setShortcut(QKeySequence("Ctrl+Shift+Tab"))

        help_menu = self.menuBar().addMenu(self.tr("Help"))
        _help_act = help_menu.addAction(self.tr("PocketFlow Creator Help"), self._on_help)
        _help_act.setShortcut(QKeySequence(Qt.Key.Key_F1))
        help_menu.addAction(self.tr("Tutorials"), self._on_help_tutorials)
        help_menu.addAction(self.tr("Getting to Know Nodes"), self._on_help_gtkn)
        help_menu.addAction(self.tr("PocketFlow Node Reference"), self._on_help_node_ref)
        help_menu.addSeparator()
        help_menu.addAction(self.tr("About PocketFlow"), self._on_about_pocketflow)
        help_menu.addAction(self.tr("About PocketFlow Creator"), self._on_about)

    # --------------------------------------------------------------- layout

    # ------------------------------------------------------------------
    # Toolbar stylesheet — regenerated on every theme change so colours
    # are always correct for dark, light, and system colour schemes.
    # ------------------------------------------------------------------

    @staticmethod
    def _node_toolbar_stylesheet(dark: bool) -> str:
        """Return a QSS string for the node-type toolbar.

        Regular node buttons
        --------------------
        - Normal  : transparent border (icon-only look)
        - Hover   : subtle tinted border + background
        - Pressed : brighter tinted border + background

        Overflow extension button  (``QToolButton#qt_toolbar_ext_button``)
        -------------------------------------------------------------------
        Always visible so the user knows there are more nodes off-screen.
        Uses a permanently drawn border and a ``▸▸`` label so it is obvious
        even before the pointer moves near it.
        """
        if dark:
            btn_hover_border   = "rgba(255, 255, 255, 0.55)"
            btn_hover_bg       = "rgba(255, 255, 255, 0.12)"
            btn_pressed_border = "rgba(255, 255, 255, 0.80)"
            btn_pressed_bg     = "rgba(255, 255, 255, 0.25)"
            ext_border         = "rgba(255, 255, 255, 0.35)"
            ext_bg             = "rgba(255, 255, 255, 0.08)"
            ext_hover_border   = "rgba(255, 255, 255, 0.65)"
            ext_hover_bg       = "rgba(255, 255, 255, 0.18)"
            ext_color          = "rgba(255, 255, 255, 0.85)"
        else:
            btn_hover_border   = "rgba(0, 0, 0, 0.30)"
            btn_hover_bg       = "rgba(0, 0, 0, 0.08)"
            btn_pressed_border = "rgba(0, 0, 0, 0.50)"
            btn_pressed_bg     = "rgba(0, 0, 0, 0.15)"
            ext_border         = "rgba(0, 0, 0, 0.28)"
            ext_bg             = "rgba(0, 0, 0, 0.06)"
            ext_hover_border   = "rgba(0, 0, 0, 0.50)"
            ext_hover_bg       = "rgba(0, 0, 0, 0.12)"
            ext_color          = "rgba(0, 0, 0, 0.75)"

        return f"""
            QToolButton {{
                border: 2px solid transparent;
                border-radius: 7px;
                padding: 3px;
                margin: 1px;
            }}
            QToolButton:hover {{
                border: 2px solid {btn_hover_border};
                background: {btn_hover_bg};
            }}
            QToolButton:pressed {{
                border: 2px solid {btn_pressed_border};
                background: {btn_pressed_bg};
            }}

            /* ── Overflow / extension button ──────────────────────────── */
            /* objectName set by Qt: "qt_toolbar_ext_button"               */
            QToolButton#qt_toolbar_ext_button {{
                border: 1px solid {ext_border};
                border-radius: 5px;
                background: {ext_bg};
                color: {ext_color};
                font-size: 9px;
                font-weight: bold;
                min-width: 16px;
                padding: 2px 3px;
                margin: 2px 1px;
                qproperty-text: "▸▸";
            }}
            QToolButton#qt_toolbar_ext_button:hover {{
                border: 1px solid {ext_hover_border};
                background: {ext_hover_bg};
            }}
            QToolButton#qt_toolbar_ext_button:pressed {{
                border: 1px solid {btn_pressed_border};
                background: {btn_pressed_bg};
            }}
        """

    # ── Toolbar super-group definitions ──────────────────────────────────────
    # Categories in the same super-group are separated by a thin Qt separator.
    # Between super-groups a wider transparent spacer widget is inserted so the
    # groups visually stand apart without cluttering the bar with extra lines.
    _TOOLBAR_SUPER_GROUPS: list[tuple[str, set[str]]] = [
        ("Flow / Core",  {"Flow Control", "Core"}),
        ("AI",           {"AI", "AI/Reasoning", "AI/LLM Utilities"}),
        ("Human",        {"Human-in-the-Loop"}),
        ("Data",         {"Data/IO", "Data Processing", "Text/Data Processing",
                          "Data/Vector", "Data Structures/Memory"}),
        ("Code",         {"Code", "Code/Execution"}),
        ("Processing",   {"Processing", "Async"}),
        ("Integrations", {"Web/Search", "Database/SQL", "Voice/Audio",
                          "Document/Vision", "Calendar", "MCP/Agent Protocol",
                          "Observability/Utility", "System/Shell", "Networking",
                          "Resilience", "Messaging", "Security"}),
    ]

    @staticmethod
    def _toolbar_super_group(category: str) -> str:
        """Return the super-group label for *category*, or the category itself."""
        for label, cats in MainWindow._TOOLBAR_SUPER_GROUPS:
            if category in cats:
                return label
        return category   # uncategorised built-ins get their own implicit group

    def _build_node_toolbar(self) -> None:
        tb = QToolBar(self.tr("Node Types"), self)
        tb.setObjectName("nodeTypeToolBar")
        tb.setMovable(False)
        tb.setIconSize(QSize(28, 28))
        tb.setStyleSheet(self._node_toolbar_stylesheet(self._dark_mode))
        self.addToolBar(tb)
        self._node_toolbar = tb

        # Helpers ─────────────────────────────────────────────────────────────
        def _add_gap(width: int = 32) -> None:
            """Insert a transparent fixed-width spacer to separate super-groups."""
            spacer = QWidget()
            spacer.setFixedSize(width, 32)  # explicit height so toolbar doesn't collapse it
            spacer.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            tb.addWidget(spacer)

        # Determine display order — saved order first, falling back to default.
        default_order = [
            type_id
            for _cat, nodes in get_nodes_by_category()
            for type_id, _nt in nodes
        ]
        saved = QSettings(_ORG, _APP).value(_SKEY_TOOLBAR_ORDER, None)
        using_default_order: bool
        if isinstance(saved, list):
            known = set(default_order)
            order: list[str] = [t for t in saved if t in known]
            for t in default_order:
                if t not in order:
                    order.append(t)
            using_default_order = False
        else:
            order = default_order
            using_default_order = True

        # ── Built-in nodes ────────────────────────────────────────────────────
        # With the default order, insert a thin separator between categories
        # within the same super-group and a wider gap between super-groups.
        self._toolbar_actions: dict[str, QAction] = {}
        prev_category: str | None = None
        prev_super: str | None = None
        for type_id in order:
            nt = BUILTIN_NODE_TYPES.get(type_id)
            if nt is None:
                continue
            if using_default_order and nt.category != prev_category:
                super_grp = self._toolbar_super_group(nt.category)
                if prev_super is None:
                    pass  # first item, no separator needed
                elif super_grp != prev_super:
                    _add_gap()          # wider gap between super-groups
                else:
                    tb.addSeparator()   # thin line within a super-group
                prev_category = nt.category
                prev_super = super_grp
            icon = make_node_icon(type_id, 32)
            act = tb.addAction(icon, nt.display_name)
            act.setToolTip(f"{nt.display_name}  [{nt.category}]")
            act.triggered.connect(
                lambda checked=False, tid=type_id: self._drop_node_at_center(tid)
            )
            self._toolbar_actions[type_id] = act

        # ── Add-on scientific / engineering nodes ─────────────────────────────
        addon_nodes_dict = get_all_addon_nodes()
        if addon_nodes_dict:
            _add_gap(48)    # prominent break before the add-on section
            prev_addon_cat: str | None = None
            for _cat, nodes_in_cat in get_addon_node_groups():
                for type_id, nt in nodes_in_cat:
                    if nt.category != prev_addon_cat:
                        if prev_addon_cat is not None:
                            tb.addSeparator()
                        prev_addon_cat = nt.category
                    icon = make_node_icon(type_id, 32)
                    act = tb.addAction(icon, nt.display_name)
                    act.setToolTip(f"{nt.display_name}  [{nt.category}] ⚗ Add-on")
                    act.triggered.connect(
                        lambda checked=False, tid=type_id: self._drop_node_at_center(tid)
                    )
                    self._toolbar_actions[type_id] = act

        # ── User-installed custom nodes ───────────────────────────────────────
        user_nodes = get_all_user_nodes()
        if user_nodes:
            _add_gap(48)    # prominent break before the custom section
            prev_user_cat: str | None = None
            for type_id, nt in user_nodes.items():
                if nt.category != prev_user_cat:
                    if prev_user_cat is not None:
                        tb.addSeparator()
                    prev_user_cat = nt.category
                icon = make_node_icon(type_id, 32)
                act = tb.addAction(icon, nt.display_name)
                act.setToolTip(f"{nt.display_name}  [{nt.category}] ★ Custom")
                act.triggered.connect(
                    lambda checked=False, tid=type_id: self._drop_node_at_center(tid)
                )
                self._toolbar_actions[type_id] = act

        # Right-click on the toolbar → "Customize Toolbar…"
        tb.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        tb.customContextMenuRequested.connect(self._on_toolbar_context_menu)

    def _drop_node_at_center(self, type_id: str) -> None:
        """Add a node of type_id at the visible centre of the graph view."""
        if not hasattr(self, "_graph_view"):
            return
        center = self._graph_view.mapToScene(
            self._graph_view.viewport().rect().center()
        )
        self._graph_scene.create_node_at(type_id, center)

    def _on_toolbar_context_menu(self) -> None:
        menu = QMenu(self)
        menu.addAction(self.tr("Customize Toolbar…"), self._on_customize_toolbar)
        menu.exec(self._node_toolbar.mapToGlobal(
            self._node_toolbar.rect().center()
        ))

    def _on_customize_toolbar(self) -> None:
        """Open the Customize Toolbar dialog and apply / save the result."""
        current_order = [
            type_id
            for type_id in self._toolbar_actions
        ]
        display_names = {
            type_id: nt.display_name
            for type_id, nt in BUILTIN_NODE_TYPES.items()
        }
        default_order = list(BUILTIN_NODE_TYPES.keys())

        dlg = CustomizeToolbarDialog(
            current_order, display_names, default_order, self
        )
        if dlg.exec() != CustomizeToolbarDialog.DialogCode.Accepted:
            return

        new_order = dlg.ordered_type_ids()

        # Rebuild toolbar actions in the new order
        tb = self._node_toolbar
        # Remove all existing node actions
        for act in list(self._toolbar_actions.values()):
            tb.removeAction(act)
        self._toolbar_actions.clear()

        for type_id in new_order:
            nt = BUILTIN_NODE_TYPES.get(type_id)
            if nt is None:
                continue
            icon = make_node_icon(type_id, 32)
            act = tb.addAction(icon, nt.display_name)
            act.setToolTip(nt.display_name)
            act.triggered.connect(
                lambda checked=False, tid=type_id: self._drop_node_at_center(tid)
            )
            self._toolbar_actions[type_id] = act

        # Persist the new order
        QSettings(_ORG, _APP).setValue(_SKEY_TOOLBAR_ORDER, new_order)

    def _build_central_area(self) -> None:
        self._graph_view = GraphView(self._graph_scene)
        self.setCentralWidget(self._graph_view)
        self._zoom_label = QLabel("100%")
        self._zoom_label.setFixedWidth(54)
        self.statusBar().addPermanentWidget(self._zoom_label)
        self._graph_view.zoom_changed.connect(self._on_zoom_changed)

    def _build_docks(self) -> None:
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._build_project_explorer())
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._build_component_palette())
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._build_object_inspector())
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self._build_bottom_dock())

    def _build_project_explorer(self) -> QDockWidget:
        dock = QDockWidget(self.tr("Project Explorer"), self)
        dock.setObjectName("projectExplorerDock")
        self._explorer_dock = dock
        self._explorer_tree = QTreeWidget()
        self._explorer_tree.setHeaderHidden(True)
        dock.setWidget(self._explorer_tree)
        return dock

    def _build_component_palette(self) -> QDockWidget:
        dock = QDockWidget(self.tr("Component Palette"), self)
        dock.setObjectName("componentPaletteDock")
        self._palette_dock = dock
        dock.setWidget(PaletteWidget())
        return dock

    def _build_object_inspector(self) -> QDockWidget:
        dock = QDockWidget(self.tr("Object Inspector"), self)
        dock.setObjectName("objectInspectorDock")
        self._inspector_dock = dock
        self._inspector = QTreeWidget()
        self._inspector.setHeaderLabels([self.tr("Property"), self.tr("Value")])
        self._inspector.setAlternatingRowColors(True)
        self._inspector.header().setStretchLastSection(True)
        dock.setWidget(self._inspector)
        return dock

    def _build_bottom_dock(self) -> QDockWidget:
        dock = QDockWidget(self.tr("Output"), self)
        dock.setObjectName("outputDock")
        self._bottom_dock = dock
        self._bottom_tab_widget = QTabWidget()
        plain_tabs = [
            ("Problems", self.tr("No validation has been run.")),
            ("Run Log", self.tr("No active run.")),
            ("Shared Store", "{}"),
            ("Data Flow", self.tr("Open a graph and run Project > Data Flow Report.")),
            ("Prompt Preview", self.tr("Select an LLM node to preview its prompt.")),
            ("Generated Code", self.tr("Generated code appears here.")),
            ("Python", self.tr("Open a Python file to edit custom code.")),
            ("YAML", self.tr("Open metadata to edit YAML.")),
            ("Test Results", self.tr("Tests have not been run.")),
        ]
        for name, text in plain_tabs:
            editor = QPlainTextEdit()
            editor.setPlainText(text)
            self._bottom_tab_widget.addTab(editor, self.tr(name))
            self._bottom_editors[name] = editor
            self._bottom_tab_paths[name] = None

        # Markdown tab: editor on left, live HTML preview on right
        self._md_splitter = QSplitter(Qt.Orientation.Horizontal)
        self._md_splitter.setObjectName("mdSplitter")
        md_editor = QPlainTextEdit()
        md_editor.setPlainText(self.tr("Open a prompt file to edit Markdown."))
        self._markdown_preview = QTextBrowser()
        self._markdown_preview.setPlainText(self.tr("Preview appears here."))
        self._md_splitter.addWidget(md_editor)
        self._md_splitter.addWidget(self._markdown_preview)
        self._md_splitter.setSizes([1, 1])
        md_splitter = self._md_splitter  # keep local alias for addTab below
        self._bottom_tab_widget.addTab(md_splitter, self.tr("Markdown"))
        self._bottom_editors["Markdown"] = md_editor
        self._bottom_tab_paths["Markdown"] = None

        dock.setWidget(self._bottom_tab_widget)
        return dock

    # ------------------------------------------------------- layout persistence

    def _save_layout(self) -> None:
        """Persist window geometry, dock arrangement, and splitter sizes to QSettings."""
        settings = QSettings(_ORG, _APP)
        settings.setValue(_SKEY_LAYOUT_GEOMETRY, self.saveGeometry())
        settings.setValue(_SKEY_LAYOUT_STATE, self.saveState())
        settings.setValue(_SKEY_LAYOUT_SPLITTER, self._md_splitter.saveState())

    def _restore_layout(self) -> None:
        """Restore window geometry, dock arrangement, and splitter sizes from QSettings."""
        settings = QSettings(_ORG, _APP)
        geometry = settings.value(_SKEY_LAYOUT_GEOMETRY)
        state = settings.value(_SKEY_LAYOUT_STATE)
        splitter = settings.value(_SKEY_LAYOUT_SPLITTER)
        if geometry:
            self.restoreGeometry(geometry)
        if state:
            self.restoreState(state)
        if splitter:
            self._md_splitter.restoreState(splitter)

    def _on_save_layout(self) -> None:
        self._save_layout()
        self.statusBar().showMessage(self.tr("Layout saved."))

    def _on_reset_layout(self) -> None:
        """Remove saved layout from QSettings; next launch will use factory defaults."""
        settings = QSettings(_ORG, _APP)
        settings.remove(_SKEY_LAYOUT_GEOMETRY)
        settings.remove(_SKEY_LAYOUT_STATE)
        settings.remove(_SKEY_LAYOUT_SPLITTER)
        self.statusBar().showMessage(self.tr("Saved layout cleared — restart to apply defaults."))

    def _apply_default_layout(self) -> None:
        """Physically move all docks back to their factory positions right now."""
        # Re-dock every widget to its original area (also un-floats any floating docks)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._explorer_dock)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._palette_dock)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._inspector_dock)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self._bottom_dock)
        # Make sure all docks are visible
        for dock in (self._explorer_dock, self._palette_dock,
                     self._inspector_dock, self._bottom_dock):
            dock.setVisible(True)
        self.resize(1400, 900)
        self._md_splitter.setSizes([1, 1])

    def _on_default_layout(self) -> None:
        """Apply factory layout immediately and clear any saved layout."""
        settings = QSettings(_ORG, _APP)
        settings.remove(_SKEY_LAYOUT_GEOMETRY)
        settings.remove(_SKEY_LAYOUT_STATE)
        settings.remove(_SKEY_LAYOUT_SPLITTER)
        self._apply_default_layout()
        self.statusBar().showMessage(self.tr("Layout restored to factory defaults."))

    def closeEvent(self, event: Any) -> None:  # type: ignore[override]
        """Auto-save layout on close so the next session opens with the same arrangement."""
        self._save_layout()
        super().closeEvent(event)

    def _on_next_tab(self) -> None:
        tw = self._bottom_tab_widget
        tw.setCurrentIndex((tw.currentIndex() + 1) % tw.count())

    def _on_prev_tab(self) -> None:
        tw = self._bottom_tab_widget
        tw.setCurrentIndex((tw.currentIndex() - 1) % tw.count())

    # ------------------------------------------------------- explorer refresh

    def _refresh_explorer(self) -> None:
        self._explorer_tree.clear()
        if self._project is None:
            return
        root_item = QTreeWidgetItem([self._project.name])

        def _cat(label: str, items: list[str]) -> QTreeWidgetItem:
            node = QTreeWidgetItem([label])
            for rel in items:
                child = QTreeWidgetItem([Path(rel).name])
                child.setData(0, _ROLE_PATH, self._project.root / rel)  # type: ignore[union-attr]
                child.setData(0, _ROLE_KIND, "file")
                node.addChild(child)
            return node

        root_item.addChild(_cat("Graphs", self._project.graphs))
        root_item.addChild(_cat("Prompts", self._project.prompts))
        root_item.addChild(_cat("Node Types", self._project.node_types))
        root_item.addChild(QTreeWidgetItem(["Tools"]))
        if self._project.shared_store_schema:
            ss_item = QTreeWidgetItem(["Shared Store"])
            ss_path = self._project.root / self._project.shared_store_schema
            ss_item.setData(0, _ROLE_PATH, ss_path)
            ss_item.setData(0, _ROLE_KIND, "shared_store_schema")
            root_item.addChild(ss_item)
        root_item.addChild(QTreeWidgetItem(["Source"]))
        root_item.addChild(QTreeWidgetItem(["Tests"]))
        root_item.addChild(QTreeWidgetItem(["Exports"]))
        self._explorer_tree.addTopLevelItem(root_item)
        root_item.setExpanded(True)

    def _switch_bottom_tab(self, name: str) -> None:
        """Activate *name* tab in the Output dock, making the dock visible if closed."""
        # Ensure the dock is open and raised (handles closed, hidden, and tabbed-behind cases)
        self._bottom_dock.setVisible(True)
        self._bottom_dock.raise_()
        for i in range(self._bottom_tab_widget.count()):
            if self._bottom_tab_widget.tabText(i) == name:
                self._bottom_tab_widget.setCurrentIndex(i)
                break

    # -------------------------------------------------------- recent projects

    def _load_recent(self) -> list[Path]:
        settings = QSettings(_ORG, _APP)
        raw = settings.value(_SKEY_RECENT, [])
        if isinstance(raw, str):
            items: list[str] = [raw]
        elif isinstance(raw, list):
            items = raw
        else:
            items = []
        return [Path(p) for p in items if Path(p).exists()][:_MAX_RECENT]

    def _add_recent(self, path: Path) -> None:
        recent = [p for p in self._recent if p != path]
        recent.insert(0, path)
        self._recent = recent[:_MAX_RECENT]
        settings = QSettings(_ORG, _APP)
        settings.setValue(_SKEY_RECENT, [str(p) for p in self._recent])
        self._update_recent_menu()

    def _update_recent_menu(self) -> None:
        self._recent_menu.clear()
        if not self._recent:
            self._recent_menu.addAction("(none)").setEnabled(False)
            return
        for path in self._recent:
            self._recent_menu.addAction(
                path.name, lambda p=path: self._load_project_from_path(p)
            )

    # -------------------------------------------------- temp-project helpers

    def _temp_project_root(self) -> Path:
        return Path(tempfile.gettempdir()) / _TEMP_PROJECT_DIR

    def _cleanup_temp_project(self) -> None:
        temp_root = self._temp_project_root()
        if temp_root.exists():
            shutil.rmtree(temp_root, ignore_errors=True)

    # -------------------------------------------------- helpers

    def _create_untitled_flow(self) -> None:
        """Create a temp-project-backed untitled flow so all features work immediately."""
        self._cleanup_temp_project()
        temp_root = self._temp_project_root()
        temp_root.mkdir(parents=True, exist_ok=True)
        (temp_root / "graphs").mkdir(exist_ok=True)
        graph_rel = "graphs/main.pfcgraph.yaml"
        graph = GraphModel(id="main", title="Untitled Flow", nodes=[], edges=[])
        GraphSaver().save(graph, temp_root / graph_rel)
        self._project = ProjectModel(
            name="Untitled",
            package_name="untitled",
            root=temp_root,
            graphs=[graph_rel],
        )
        ProjectSaver().save(self._project)
        self._is_temp_project = True
        self._graphs = {graph_rel: graph}
        self._active_graph_rel = graph_rel
        self._undo_stack.clear()
        self._graph_scene.load_graph(graph)
        self.setWindowTitle(self.tr("PocketFlow Creator — Untitled (unsaved)"))
        self.statusBar().showMessage(
            self.tr("New flow ready. Use File > Save As to save it as a project.")
        )

    def _ensure_active_graph(self) -> None:
        """Guarantee _active_graph_rel is set.

        If there is no active graph (project or untitled), one is created in memory.
        If a project is open but has no graph file, one is written to disk.
        """
        if self._active_graph_rel is not None:
            return
        if self._project is None or self._is_temp_project:
            self._create_untitled_flow()
            return
        # Project open but no active graph — create a default graph file
        graph_rel = "graphs/main.pfcgraph.yaml"
        graph = GraphModel(
            id="main",
            title=f"{self._project.name} — Main Flow",
            nodes=[],
            edges=[],
        )
        try:
            GraphSaver().save(graph, self._project.root / graph_rel)
            if graph_rel not in self._project.graphs:
                self._project.graphs.append(graph_rel)
            ProjectSaver().save(self._project)
        except Exception:
            pass  # Keep in memory even if the file write fails
        self._graphs[graph_rel] = graph
        self._active_graph_rel = graph_rel

    # -------------------------------------------------- file action handlers

    def _on_new_project(self) -> None:
        name, ok = QInputDialog.getText(self, "New Project", "Project name:")
        if not ok or not name.strip():
            return
        directory = QFileDialog.getExistingDirectory(self, "Choose Project Location")
        if not directory:
            return
        name = name.strip()
        package = name.lower().replace(" ", "_").replace("-", "_")
        root = Path(directory) / name
        self._cleanup_temp_project()
        self._is_temp_project = False
        self._project = ProjectModel(name=name, package_name=package, root=root)
        self._graphs = {}
        self._active_graph_rel = None
        try:
            root.mkdir(parents=True, exist_ok=True)
            graphs_dir = root / "graphs"
            graphs_dir.mkdir(exist_ok=True)
            graph_rel = "graphs/main.pfcgraph.yaml"
            graph = GraphModel(id="main", title=f"{name} — Main Flow", nodes=[], edges=[])
            GraphSaver().save(graph, root / graph_rel)
            self._project.graphs.append(graph_rel)
            ProjectSaver().save(self._project)
            self._graphs[graph_rel] = graph
            self._active_graph_rel = graph_rel
            self._undo_stack.clear()
            self._graph_scene.load_graph(graph)
            self._graph_view.zoom_to_fit()
            self._add_recent(self._project.project_file)
        except Exception as exc:
            QMessageBox.warning(self, "New Project Warning", f"Could not write project:\n{exc}")
        self._refresh_explorer()
        self.setWindowTitle(f"PocketFlow Creator — {name}")
        self.statusBar().showMessage(f"New project: {name}")

    def _on_new_from_template(self) -> None:
        templates_root = Path(__file__).parent.parent / "project_templates"
        entries: list[tuple[str, str, Path]] = []
        for tdir in sorted(templates_root.iterdir()):
            info_path = tdir / "template_info.yaml"
            if not tdir.is_dir() or not info_path.exists():
                continue
            try:
                info = yaml.safe_load(info_path.read_text(encoding="utf-8")) or {}
            except yaml.YAMLError:
                continue
            entries.append(
                (str(info.get("name", tdir.name)), str(info.get("description", "")), tdir)
            )

        if not entries:
            QMessageBox.information(self, "No Templates", "No project templates found.")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("New From Template")
        dlg.resize(480, 320)
        layout = QVBoxLayout(dlg)
        layout.addWidget(QLabel("Select a template:"))
        template_list = QListWidget()
        for name, description, _ in entries:
            item = QListWidgetItem(name)
            item.setToolTip(description)
            template_list.addItem(item)
        template_list.setCurrentRow(0)
        layout.addWidget(template_list)
        desc_label = QLabel(entries[0][1] if entries else "")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        template_list.currentRowChanged.connect(
            lambda r: desc_label.setText(entries[r][1] if 0 <= r < len(entries) else "")
        )
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        row = template_list.currentRow()
        if row < 0:
            return
        _, _, template_dir = entries[row]

        name, ok = QInputDialog.getText(self, "Project Name", "Project name:")
        if not ok or not name.strip():
            return
        name = name.strip()
        directory = QFileDialog.getExistingDirectory(self, "Choose Project Location")
        if not directory:
            return

        package = name.lower().replace(" ", "_").replace("-", "_")
        dest = Path(directory) / name
        try:
            shutil.copytree(template_dir, dest, ignore=shutil.ignore_patterns("template_info.yaml"))
        except FileExistsError:
            QMessageBox.warning(self, "Error", f"Directory already exists: {dest}")
            return

        # Rename and patch project YAML
        proj_src = dest / "project.pfcproj.yaml"
        proj_dest = dest / f"{name}.pfcproj.yaml"
        if proj_src.exists():
            raw = yaml.safe_load(proj_src.read_text(encoding="utf-8")) or {}
            raw["name"] = name
            raw["package_name"] = package
            proj_dest.write_text(
                yaml.dump(raw, default_flow_style=False, allow_unicode=True), encoding="utf-8"
            )
            proj_src.unlink()

        try:
            self._load_project_from_path(proj_dest)
        except Exception as exc:
            QMessageBox.warning(
                self, "Template Warning", f"Project created but could not load:\n{exc}"
            )

    def _on_open_project(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "", "PocketFlow Projects (*.pfcproj.yaml)"
        )
        if not path_str:
            return
        self._load_project_from_path(Path(path_str))

    def _load_project_from_path(self, path: Path) -> None:
        try:
            self._cleanup_temp_project()
            self._is_temp_project = False
            self._project = ProjectLoader().load(path)
            self._graphs = {}
            self._active_graph_rel = None
            loader = GraphLoader()
            for rel in self._project.graphs:
                gpath = self._project.root / rel
                if gpath.exists():
                    try:
                        self._graphs[rel] = loader.load(gpath)
                    except Exception as exc:
                        QMessageBox.warning(
                            self, "Load Warning", f"Could not load {rel}:\n{exc}"
                        )
            if not self._graphs:
                # Project has no graphs (blank template or all files failed) — create a default
                graph_rel = "graphs/main.pfcgraph.yaml"
                graph = GraphModel(
                    id="main",
                    title=f"{self._project.name} — Main Flow",
                    nodes=[],
                    edges=[],
                )
                try:
                    GraphSaver().save(graph, self._project.root / graph_rel)
                    if graph_rel not in self._project.graphs:
                        self._project.graphs.append(graph_rel)
                    ProjectSaver().save(self._project)
                    self._graphs[graph_rel] = graph
                except Exception:
                    pass  # Non-fatal — graph stays in memory even if save fails
            if self._graphs:
                self._active_graph_rel = next(iter(self._graphs.keys()))
                self._undo_stack.clear()
                saved_style = self._project.auto_arrange.get("connector_style", "straight")
                self._graph_scene.set_connector_style(saved_style)
                self._graph_scene.load_graph(self._graphs[self._active_graph_rel])
                self._graph_view.zoom_to_fit()
            self._refresh_explorer()
            self._add_recent(path)
            self.setWindowTitle(f"PocketFlow Creator — {self._project.name}")
            self.statusBar().showMessage(f"Opened: {self._project.name}")
        except Exception as exc:
            QMessageBox.critical(self, "Open Failed", str(exc))

    def _on_save_as(self) -> None:
        """Save the current flow (including temp projects) to a named project location."""
        default_name = self._project.name if self._project and not self._is_temp_project else ""
        name, ok = QInputDialog.getText(
            self, self.tr("Save Project As"), self.tr("Project name:"), text=default_name
        )
        if not ok or not name.strip():
            return
        directory = QFileDialog.getExistingDirectory(self, self.tr("Choose Project Location"))
        if not directory:
            return
        name = name.strip()
        package = name.lower().replace(" ", "_").replace("-", "_")
        new_root = Path(directory) / name
        if new_root.exists():
            btn = QMessageBox.question(
                self,
                self.tr("Overwrite?"),
                self.tr("'%1' already exists. Overwrite?").replace("%1", str(new_root)),
            )
            if btn != QMessageBox.StandardButton.Yes:
                return
            shutil.rmtree(new_root, ignore_errors=True)
        try:
            if self._project is not None:
                shutil.copytree(self._project.root, new_root)
            else:
                new_root.mkdir(parents=True, exist_ok=True)
            old_temp = self._project.root if self._is_temp_project else None
            self._project = ProjectModel(
                name=name,
                package_name=package,
                root=new_root,
                graphs=list(self._project.graphs) if self._project else ["graphs/main.pfcgraph.yaml"],
            )
            ProjectSaver().save(self._project)
            # Re-key _graphs with same relative paths (they are unchanged)
            self._is_temp_project = False
            if old_temp:
                shutil.rmtree(old_temp, ignore_errors=True)
            self._add_recent(self._project.project_file)
            self.setWindowTitle(f"PocketFlow Creator — {name}")
            self._refresh_explorer()
            self.statusBar().showMessage(self.tr("Project saved as: %1").replace("%1", name))
        except Exception as exc:
            QMessageBox.critical(self, self.tr("Save As Failed"), str(exc))

    def _on_save(self) -> None:
        if self._is_temp_project:
            self._on_save_as()
            return
        if self._project is None:
            self.statusBar().showMessage("No project open.")
            return
        try:
            ProjectSaver().save(self._project)
            saver = GraphSaver()
            for rel, graph in self._graphs.items():
                saver.save(graph, self._project.root / rel)
        except Exception as exc:
            QMessageBox.critical(self, "Save Failed", str(exc))
            return
        current = self._bottom_tab_widget.tabText(self._bottom_tab_widget.currentIndex())
        if current in _EDITOR_TABS:
            editor = self._bottom_editors[current]
            if editor.hasFocus() and self._bottom_tab_paths.get(current) is not None:
                self._save_editor_file(current)
                return
        self.statusBar().showMessage("Saved.")

    def _on_save_all(self) -> None:
        if self._is_temp_project:
            self._on_save_as()
            return
        if self._project is None:
            self.statusBar().showMessage("No project open.")
            return
        try:
            ProjectSaver().save(self._project)
            saver = GraphSaver()
            for rel, graph in self._graphs.items():
                saver.save(graph, self._project.root / rel)
            for tab_name in _EDITOR_TABS:
                if self._bottom_tab_paths.get(tab_name) is not None:
                    self._save_editor_file(tab_name)
            self.statusBar().showMessage("All files saved.")
        except Exception as exc:
            QMessageBox.critical(self, "Save Failed", str(exc))

    def _on_project_settings(self) -> None:
        if self._project is None:
            self.statusBar().showMessage("No project open.")
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("Project Settings")
        form = QFormLayout(dlg)
        name_edit = QLineEdit(self._project.name)
        pkg_edit = QLineEdit(self._project.package_name)
        prov_edit = QLineEdit(self._project.default_provider)
        model_edit = QLineEdit(self._project.default_model)
        form.addRow("Name:", name_edit)
        form.addRow("Package name:", pkg_edit)
        form.addRow("Default provider:", prov_edit)
        form.addRow("Default model:", model_edit)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        form.addRow(buttons)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        self._project.name = name_edit.text().strip() or self._project.name
        self._project.package_name = pkg_edit.text().strip() or self._project.package_name
        prov = prov_edit.text().strip()
        self._project.default_provider = prov or self._project.default_provider
        mdl = model_edit.text().strip()
        self._project.default_model = mdl or self._project.default_model
        self._refresh_explorer()

    # ------------------------------------------------- project action handlers

    def _on_validate_project(self) -> None:
        if self._project is None:
            self.statusBar().showMessage("No project open.")
            return
        validator = GraphValidator()
        lines: list[str] = []
        error_ids: set[str] = set()
        for rel, graph in self._graphs.items():
            for issue in validator.validate(graph):
                lines.append(
                    f"[{issue.severity.upper()}] {rel}:{issue.object_id}  {issue.message}"
                )
                error_ids.add(issue.object_id)
        text = "\n".join(lines) if lines else "No issues found."
        self._bottom_editors["Problems"].setPlainText(text)
        self._switch_bottom_tab("Problems")
        self._graph_scene.apply_validation(error_ids)
        self.statusBar().showMessage(f"Validation: {len(lines)} issue(s).")

    def _on_generate_code(self) -> None:
        if not self._graphs:
            self.statusBar().showMessage("No graphs to generate from.")
            return
        gen = PythonGenerator()
        parts: list[str] = []
        for rel, graph in self._graphs.items():
            parts.append(f"# === {rel} ===")
            parts.append(gen.generate_nodes_py(graph))
            parts.append(gen.generate_flow_py(graph))
        self._bottom_editors["Generated Code"].setPlainText("\n".join(parts))
        self._switch_bottom_tab("Generated Code")
        self.statusBar().showMessage("Code generated.")

    def _on_open_project_folder(self) -> None:
        if self._project is None:
            self.statusBar().showMessage("No project open.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._project.root)))

    def _on_export_project(self) -> None:
        if self._project is None:
            self.statusBar().showMessage("No project open.")
            return
        if not self._graphs:
            self.statusBar().showMessage("No graphs to export.")
            return

        # Warn if the project will export API keys in plain text
        providers = self._project.providers
        if providers.include_api_keys and any(p.api_key for p in providers.profiles):
            warn_dlg = QDialog(self)
            warn_dlg.setWindowTitle("API Key Security Warning")
            warn_layout = QVBoxLayout(warn_dlg)
            warn_layout.addWidget(QLabel(
                "<b>This project contains API keys that will be exported in plain text.</b><br><br>"
                "Anyone who receives the exported files will have access to your credentials.<br>"
                "Consider unchecking <i>Include API keys in project file</i> in the Provider Manager."
            ))
            chk = QCheckBox("I understand and accept responsibility for sharing these API keys.")
            warn_layout.addWidget(chk)
            bbox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            bbox.accepted.connect(warn_dlg.accept)
            bbox.rejected.connect(warn_dlg.reject)
            warn_layout.addWidget(bbox)
            bbox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
            chk.toggled.connect(lambda checked: bbox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(checked))
            if warn_dlg.exec() != QDialog.DialogCode.Accepted:
                return

        try:
            result = Exporter().export(self._project, self._graphs)
        except Exception as exc:
            QMessageBox.critical(self, "Export Failed", str(exc))
            return
        skipped = len(result.skipped)
        written = len(result.written)
        msg = f"Export complete: {written} file(s) written."
        if skipped:
            msg += f"\n{skipped} file(s) skipped (custom/ guard — existing user code preserved)."
        QMessageBox.information(self, "Export PocketFlow Project", msg)
        self.statusBar().showMessage(f"Exported to exports/{self._project.package_name}/")

    def _on_export_graph_image(self) -> None:
        if not self._graphs:
            self.statusBar().showMessage("No graphs to export.")
            return
        path_str, _ = QFileDialog.getSaveFileName(
            self, "Export Graph Image", "", "PNG Image (*.png);;SVG Image (*.svg)"
        )
        if not path_str:
            return
        path = Path(path_str)
        try:
            rect: QRectF = self._graph_scene.itemsBoundingRect()
            if rect.isEmpty():
                rect = QRectF(0, 0, 800, 600)
            if path.suffix.lower() == ".svg":
                from PySide6.QtSvg import QSvgGenerator

                gen = QSvgGenerator()
                gen.setFileName(str(path))
                gen.setSize(rect.size().toSize())
                gen.setViewBox(rect)
                painter = QPainter(gen)
                self._graph_scene.render(painter, source=rect)
                painter.end()
            else:
                img = QImage(rect.size().toSize(), QImage.Format.Format_ARGB32)
                img.fill(_PNG_BACKGROUND_DARK)
                painter = QPainter(img)
                self._graph_scene.render(painter, source=rect)
                painter.end()
                img.save(str(path))
            self.statusBar().showMessage(f"Graph image saved: {path.name}")
        except Exception as exc:
            QMessageBox.critical(self, "Export Failed", str(exc))

    def _on_export_project_report(self) -> None:
        if self._project is None:
            self.statusBar().showMessage("No project open.")
            return
        report = generate_project_report(self._project, self._graphs)
        path_str, _ = QFileDialog.getSaveFileName(
            self, "Export Project Report", str(self._project.root), "Markdown (*.md)"
        )
        if not path_str:
            return
        path = Path(path_str)
        try:
            path.write_text(report, encoding="utf-8")
            self.statusBar().showMessage(f"Report saved: {path.name}")
        except Exception as exc:
            QMessageBox.critical(self, "Export Failed", str(exc))

    def _on_dataflow_report(self) -> None:
        if not self._graphs:
            self.statusBar().showMessage("No graph open.")
            return
        graph = next(iter(self._graphs.values()))
        # Auto-resolve start node exactly as the run handler does
        if not graph.start_node or not any(n.id == graph.start_node for n in graph.nodes):
            resolved = self._resolve_start_node(graph)
            if resolved:
                graph.start_node = resolved
        registry = self._load_node_type_registry() if self._project else {}
        all_types = {**BUILTIN_NODE_TYPES, **registry}
        report = generate_dataflow_report(graph, all_types)
        self._bottom_editors["Data Flow"].setPlainText(report)
        self._switch_bottom_tab("Data Flow")
        self.statusBar().showMessage("Data Flow Report generated.")

    # ----------------------------------------------- run menu handlers

    def _on_run_active_flow(self) -> None:
        if not self._graphs:
            self.statusBar().showMessage("No graphs to run.")
            return
        graph = next(iter(self._graphs.values()))
        rel = next(iter(self._graphs.keys()))
        # Auto-detect start node if not set
        if not graph.start_node:
            resolved = self._resolve_start_node(graph)
            if resolved:
                graph.start_node = resolved
                self._graph_scene.mark_start_node(resolved)
        if not graph.nodes:
            self.statusBar().showMessage("Add at least one node before running.")
            return

        known_graphs = {k: v for k, v in self._graphs.items() if k != rel}
        project_name = self._project.name if self._project else graph.title
        project_root = self._project.root if self._project else None

        self._bottom_editors["Run Log"].setPlainText(f"Running {graph.title}…\n")
        self._switch_bottom_tab("Run Log")
        self.statusBar().showMessage("Run started…")

        _runner_ref: list[FlowRunner] = []  # filled after start_run returns

        def _on_run_complete(result: object) -> None:
            self._run_signals = None  # release the pin
            if isinstance(result, Exception):
                QMessageBox.critical(self, "Run Failed", str(result))
                self.statusBar().showMessage("Run failed.")
                return
            if not isinstance(result, RunTrace):
                return
            trace = result
            lines: list[str] = [f"Run: {graph.title}  ({len(trace.steps)} step(s))\n"]
            for step in trace.steps:
                lines.append(f"  [{step.node_id}] {step.node_title}  → {step.action}")
                if step.response:
                    lines.append(f"      response: {step.response}")
            self._bottom_editors["Run Log"].setPlainText("\n".join(lines))
            shared_text = "\n".join(
                f"{k}: {v}"
                for k, v in (trace.steps[-1].shared_after if trace.steps else {}).items()
            )
            self._bottom_editors["Shared Store"].setPlainText(shared_text or "{}")
            if project_root and _runner_ref:
                try:
                    out = _runner_ref[0].save_trace(trace, project_root / "run_reports")
                    self.statusBar().showMessage(f"Run complete — trace saved: {out.name}")
                    return
                except Exception:
                    pass
            self.statusBar().showMessage("Run complete.")

        self._run_signals, _run = run_controller.start_run(
            graph=graph,
            known_graphs=known_graphs or None,
            project_name=project_name,
            project_root=project_root,
            parent=self,
            on_complete=_on_run_complete,
            project=self._project,
        )
        _runner_ref.append(_run)

    def _on_run_tests(self) -> None:
        if self._is_temp_project:
            self._bottom_editors["Test Results"].setPlainText(
                "No tests to run.\n\nSave the project first (File > Save As), then add a "
                "tests/ directory with pytest test files."
            )
            self._switch_bottom_tab("Test Results")
            return
        if self._project is None:
            self.statusBar().showMessage("No project open.")
            return
        self._bottom_editors["Test Results"].setPlainText("Running tests…")
        self._switch_bottom_tab("Test Results")
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", "--tb=short", "-q"],
                capture_output=True,
                text=True,
                cwd=str(self._project.root),
                timeout=120,
            )
            output = (proc.stdout + proc.stderr).strip() or "(no output)"
        except subprocess.TimeoutExpired:
            output = "pytest timed out after 120 s."
        except Exception as exc:
            output = f"Could not run pytest: {exc}"
        self._bottom_editors["Test Results"].setPlainText(output)
        self.statusBar().showMessage("Tests finished.")

    def _on_debug_active_flow(self) -> None:
        if not self._graphs:
            self.statusBar().showMessage("No graphs to debug.")
            return
        _debug_rel = next(iter(self._graphs.keys()))
        graph = self._graphs[_debug_rel]
        if not graph.start_node:
            resolved = self._resolve_start_node(graph)
            if resolved:
                graph.start_node = resolved
                self._graph_scene.mark_start_node(resolved)
        if not graph.nodes:
            self.statusBar().showMessage("Add at least one node before debugging.")
            return
        _debug_known = {k: v for k, v in self._graphs.items() if k != _debug_rel}

        ctrl = StepController()
        self._debug_controller = ctrl
        self._bottom_editors["Run Log"].setPlainText("Debug run started…\n")
        self._switch_bottom_tab("Run Log")

        def _on_step(step: RunStep) -> None:
            lines = self._bottom_editors["Run Log"].toPlainText()
            lines += f"  [{step.node_id}] {step.node_title} → {step.action}\n"
            if step.response:
                lines += f"      response: {step.response}\n"
            self._bottom_editors["Run Log"].setPlainText(lines)
            shared_text = "\n".join(f"{k}: {v}" for k, v in step.shared_after.items())
            self._bottom_editors["Shared Store"].setPlainText(shared_text or "{}")
            if step.node_id in self._breakpoints:
                self.statusBar().showMessage(
                    f"Paused at [{step.node_id}] — click Resume to continue."
                )

        def _on_finished() -> None:
            self._dbg_signals = None  # release the pin
            self._stop_action.setEnabled(False)
            self._resume_action.setEnabled(False)
            self.statusBar().showMessage("Debug run finished.")

        self._dbg_signals = run_controller.start_debug(
            graph=graph,
            known_graphs=_debug_known or None,
            project_name=self._project.name if self._project else "",
            project_root=self._project.root if self._project else None,
            ctrl=ctrl,
            breakpoints=self._breakpoints,
            parent=self,
            on_step=_on_step,
            on_finished=_on_finished,
            project=self._project,
        )
        self._stop_action.setEnabled(True)
        self._resume_action.setEnabled(True)
        self.statusBar().showMessage("Debug run started.")

    def _on_stop_debug(self) -> None:
        if self._debug_controller is not None:
            self._debug_controller.stop()
            self._debug_controller = None
        self._stop_action.setEnabled(False)
        self._resume_action.setEnabled(False)
        self.statusBar().showMessage("Debug run stopped.")

    def _on_resume_debug(self) -> None:
        if self._debug_controller is not None:
            self._debug_controller.resume()
        self.statusBar().showMessage("Resumed.")

    # ----------------------------------------------- help handlers

    def _open_help(self, page: str = "index.md") -> None:
        dlg = HelpBrowser(page, self)
        dlg.exec()

    def _on_help(self) -> None:
        self._open_help("index.md")

    def _on_help_tutorials(self) -> None:
        self._open_help("tutorials/index.md")

    def _on_help_gtkn(self) -> None:
        self._open_help("tutorials/gtkn_index.md")

    def _on_help_node_ref(self) -> None:
        self._open_help("quick_ref.md")

    def _on_about_pocketflow(self) -> None:
        self._open_help("about_pocketflow.md")

    def _add_help_button(
        self, button_box: QDialogButtonBox, context_id: str
    ) -> None:
        """Add a ? button that opens context help without closing the dialog."""
        btn = button_box.addButton("?", QDialogButtonBox.ButtonRole.HelpRole)
        btn.clicked.connect(lambda: self._open_help(f"context/{context_id}.md"))

    def _on_about(self) -> None:
        QMessageBox.about(
            self,
            "About PocketFlow Creator",
            f"PocketFlow Creator  v{_VERSION}\n\n"
            "A RAD (Rapid Application Development) visual designer for building\n"
            "PocketFlow LLM workflows and agentic applications.\n\n"
            "Design flows on a live canvas, run them against Ollama or a mock\n"
            "provider, inspect shared-store state step-by-step, and export a\n"
            "runnable Python package — all from one IDE-like GUI.\n\n"
            "Built with Python 3.10+ and PySide6 (Qt 6).\n\n"
            "PocketFlow Creator is not affiliated with or endorsed by the\n"
            "PocketFlow project.  PocketFlow is MIT-licensed and developed by\n"
            "Zachary Huang / The Pocket (github.com/The-Pocket/PocketFlow).\n\n"
            "© 2026 Monotoba  —  MIT License\n"
            "https://github.com/Monotoba/PocketFlowCreator",
        )

    # ----------------------------------------------- node menu handlers

    def _on_new_custom_node_type(self) -> None:
        if self._project is None:
            self.statusBar().showMessage("No project open.")
            return
        dlg = NodeTypeWizard(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        defn = dlg.result_definition()
        node_types_dir = self._project.root / "node_types"
        node_types_dir.mkdir(parents=True, exist_ok=True)
        yaml_path = node_types_dir / f"{defn['node_type_id']}.yaml"
        yaml_path.write_text(
            yaml.dump(defn, default_flow_style=False, allow_unicode=True), encoding="utf-8"
        )
        skeleton_path = self._project.root / "custom" / f"{defn['node_type_id']}.py"
        skeleton_path.parent.mkdir(parents=True, exist_ok=True)
        if not skeleton_path.exists():
            skeleton_path.write_text(
                _node_skeleton_text(defn["node_type_id"], defn.get("base_class", "Node")),
                encoding="utf-8",
            )
        rel = f"node_types/{defn['node_type_id']}.yaml"
        if rel not in self._project.node_types:
            self._project.node_types.append(rel)
        self._refresh_explorer()
        self.statusBar().showMessage(f"Created node type: {defn['node_type_id']}")

    def _on_toggle_breakpoint(self) -> None:
        if self._current_node is None or self._current_node_item is None:
            self.statusBar().showMessage("Select a node on the canvas first.")
            return
        nid = self._current_node.id
        if nid in self._breakpoints:
            self._breakpoints.discard(nid)
            self._current_node_item.set_breakpoint(False)
            self.statusBar().showMessage(f"Breakpoint cleared: {nid}")
        else:
            self._breakpoints.add(nid)
            self._current_node_item.set_breakpoint(True)
            self.statusBar().showMessage(f"Breakpoint set: {nid}")

    def _on_generate_node_skeleton(self) -> None:
        if self._project is None or self._current_node is None:
            self.statusBar().showMessage("Select a node on the canvas first.")
            return
        node = self._current_node
        type_id = node.type_id
        skeleton_path = self._project.root / "custom" / f"{type_id}.py"
        skeleton_path.parent.mkdir(parents=True, exist_ok=True)
        if skeleton_path.exists():
            self.statusBar().showMessage(f"Skeleton already exists: {skeleton_path.name}")
            return
        skeleton_path.write_text(_node_skeleton_text(type_id, type_id), encoding="utf-8")
        self._open_file_in_editor(skeleton_path)
        self.statusBar().showMessage(f"Generated skeleton: {skeleton_path.name}")

    # ----------------------------------------------- prompt preview

    def _update_prompt_preview(self, node: NodeModel) -> None:
        if "llm" not in node.type_id.lower():
            return
        props = node.properties or {}
        prompt_type = str(props.get("prompt_type", "string"))
        raw = str(props.get("prompt_file", ""))
        if not raw:
            self._bottom_editors["Prompt Preview"].setPlainText(
                f"[{node.title}] No prompt set."
            )
            self._switch_bottom_tab("Prompt Preview")
            return
        if prompt_type == "path":
            project_root = self._project.root if self._project else None
            content = FlowRunner._resolve_prompt(props, project_root)
        else:
            content = raw
        self._bottom_editors["Prompt Preview"].setPlainText(content)
        self._switch_bottom_tab("Prompt Preview")

    # ---------------------------------------------- canvas signal handlers

    def _on_node_item_selected(self, item: object) -> None:
        if not isinstance(item, NodeItem):
            return
        self._current_node_item = item
        self._current_node = item.node
        self._populate_inspector_for_node(item.node)
        self._update_prompt_preview(item.node)

    def _on_edge_item_selected(self, item: object) -> None:
        if not isinstance(item, EdgeItem):
            return
        self._current_node = None
        self._current_node_item = None
        self._current_edge = item.edge
        edge = self._current_edge

        # Collect available actions from the source node
        src_actions: list[str] = ["default"]
        if self._active_graph_rel:
            graph = self._graphs.get(self._active_graph_rel)
            if graph:
                src = next((n for n in graph.nodes if n.id == edge.from_node), None)
                if src and src.actions:
                    src_actions = list(src.actions)

        self._inspector.blockSignals(True)
        self._inspector.clear()
        for label, value in [
            ("ID",   edge.id),
            ("From", edge.from_node),
            ("To",   edge.to_node),
        ]:
            self._inspector.addTopLevelItem(QTreeWidgetItem([label, value]))

        action_row = QTreeWidgetItem(["Action", ""])
        self._inspector.addTopLevelItem(action_row)
        self._inspector.blockSignals(False)

        # Embed combo box — must be added after the row is in the tree
        combo = QComboBox()
        combo.addItems(src_actions)
        if edge.action not in src_actions:
            combo.insertItem(0, edge.action)
        combo.setCurrentText(edge.action)

        _edge_before: list[GraphModel | None] = [None]
        if self._active_graph_rel:
            _g = self._graphs.get(self._active_graph_rel)
            _edge_before[0] = copy.deepcopy(_g) if _g is not None else None

        def _action_changed(text: str) -> None:
            edge.action = text or "default"
            if self._active_graph_rel and _edge_before[0] is not None:
                _g2 = self._graphs.get(self._active_graph_rel)
                if _g2 is not None:
                    rel = self._active_graph_rel
                    after = copy.deepcopy(_g2)
                    cmd = GraphSnapshotCommand(
                        "Change Edge Action", self._graphs, rel,
                        _edge_before[0], after, self._graph_scene,
                    )
                    self._undo_stack.push(cmd)
                    _edge_before[0] = after

        combo.currentTextChanged.connect(_action_changed)
        self._inspector.setItemWidget(action_row, 1, combo)

    def _on_selection_cleared(self) -> None:
        self._current_node = None
        self._current_node_item = None
        self._current_edge = None
        self._inspector.clear()

    @staticmethod
    def _coerce_property(value: str, declared_type: str) -> object:
        if declared_type in ("integer", "int"):
            try:
                return int(value)
            except ValueError:
                return value
        if declared_type in ("number", "float"):
            try:
                return float(value)
            except ValueError:
                return value
        if declared_type == "boolean":
            return value.lower() in ("true", "1", "yes")
        return value

    def _live_validate(self) -> None:
        if not self._graphs:
            return
        graph = next(iter(self._graphs.values()))
        issues = GraphValidator().validate(graph)
        error_ids = {i.object_id for i in issues if i.severity == "error"}
        self._graph_scene.apply_validation(error_ids)

    def _on_inspector_item_changed(self, item: QTreeWidgetItem, col: int) -> None:
        if col != 1:
            return
        if self._current_node is None or self._current_node_item is None:
            return
        node = self._current_node
        label = item.text(0)
        value = item.text(1)
        parent = item.parent()

        if parent is None:
            if label == "Title":
                node.title = value
                self._current_node_item.update()
            elif label == "Actions":
                node.actions = [a.strip() for a in value.split(",") if a.strip()]
            elif label == "Reads":
                node.reads = [r.strip() for r in value.split(",") if r.strip()]
            elif label == "Writes":
                node.writes = [w.strip() for w in value.split(",") if w.strip()]
        else:
            parent_text = parent.text(0)
            if parent_text == "[Subflow]" and label == "subflow_ref":
                node.properties["subflow_ref"] = value
            elif parent_text.startswith("[") and parent_text.endswith("]"):
                declared_type = str(item.data(1, Qt.ItemDataRole.UserRole) or "string")
                node.properties[label] = self._coerce_property(value, declared_type)

        self._live_validate()
        if self._active_graph_rel and self._inspector_snapshot is not None:
            graph = self._graphs.get(self._active_graph_rel)
            if graph is not None:
                rel = self._active_graph_rel
                before = self._inspector_snapshot
                after = copy.deepcopy(graph)
                cmd = GraphSnapshotCommand(
                    "Edit Property", self._graphs, rel, before, after, self._graph_scene
                )
                self._undo_stack.push(cmd)
                self._inspector_snapshot = after

    def _load_node_type_registry(self) -> dict[str, NodeTypeDefinition]:
        registry: dict[str, NodeTypeDefinition] = dict(BUILTIN_NODE_TYPES)
        if self._project is None:
            return registry
        for rel in self._project.node_types:
            path = self._project.root / rel
            if not path.exists():
                continue
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    defn = NodeTypeDefinition.from_mapping(data)
                    registry[defn.node_type_id] = defn
            except Exception:
                pass
        return registry

    def _style_editable(self, item: QTreeWidgetItem, col: int = 1) -> None:
        """Apply a visual cue so users can see which inspector cells are editable."""
        if self._dark_mode:
            item.setBackground(col, QBrush(QColor("#1e3d5c")))
            item.setForeground(col, QBrush(QColor("#9ecfff")))
        else:
            item.setBackground(col, QBrush(QColor("#eef4ff")))
            item.setForeground(col, QBrush(QColor("#003080")))
        item.setToolTip(col, "Click to edit")

    def _populate_inspector_for_node(self, node: NodeModel) -> None:
        if self._active_graph_rel:
            graph = self._graphs.get(self._active_graph_rel)
            self._inspector_snapshot = copy.deepcopy(graph) if graph is not None else None
        self._inspector.blockSignals(True)
        self._inspector.clear()
        rows: list[tuple[str, str, bool]] = [
            ("ID", node.id, False),
            ("Type", node.type_id, False),
            ("Title", node.title, True),
            ("Position X", str(node.position.get("x", 0.0)), False),
            ("Position Y", str(node.position.get("y", 0.0)), False),
            ("Actions", ", ".join(node.actions), True),
            ("Reads", ", ".join(node.reads), True),
            ("Writes", ", ".join(node.writes), True),
        ]
        for label, value, editable in rows:
            row = QTreeWidgetItem([label, value])
            if editable:
                row.setFlags(row.flags() | Qt.ItemFlag.ItemIsEditable)
                self._style_editable(row)
            self._inspector.addTopLevelItem(row)

        # T-B05: subflow_ref selector for subflow nodes
        if node.type_id == "subflow_node":
            subflow_section = QTreeWidgetItem(["[Subflow]", ""])
            subflow_section.setFlags(subflow_section.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            ref_row = QTreeWidgetItem(
                ["subflow_ref", str(node.properties.get("subflow_ref", ""))]
            )
            ref_row.setFlags(ref_row.flags() | Qt.ItemFlag.ItemIsEditable)
            self._style_editable(ref_row)
            subflow_section.addChild(ref_row)
            if self._project:
                for graph_path in self._project.graphs:
                    hint = QTreeWidgetItem([f"  available: {graph_path}", ""])
                    hint.setFlags(hint.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                    subflow_section.addChild(hint)
            self._inspector.addTopLevelItem(subflow_section)
            subflow_section.setExpanded(True)

        # T-603: show inherited type definition properties
        registry = self._load_node_type_registry()
        defn = registry.get(node.type_id)
        if defn is not None:
            type_section = QTreeWidgetItem([f"[{defn.display_name}]", ""])
            type_section.setFlags(type_section.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            # Track rows that need an embedded combo after the section is in the tree.
            combo_rows: list[tuple[QTreeWidgetItem, list[str], str, str]] = []
            for prop_name, prop_meta in defn.properties.items():
                meta = prop_meta if isinstance(prop_meta, dict) else {}
                default = str(meta.get("default", ""))
                inst_val = str(node.properties.get(prop_name, default))
                prop_type = str(meta.get("type", "string"))
                choices: list[str] = [str(c) for c in meta.get("choices", [])]  # type: ignore[union-attr]
                prop_row = QTreeWidgetItem([prop_name, "" if choices else inst_val])
                prop_row.setData(1, Qt.ItemDataRole.UserRole, prop_type)
                if choices:
                    combo_rows.append((prop_row, choices, inst_val, prop_name))
                else:
                    prop_row.setFlags(prop_row.flags() | Qt.ItemFlag.ItemIsEditable)
                    self._style_editable(prop_row)
                type_section.addChild(prop_row)
            if defn.base_class and defn.base_class != node.type_id:
                type_section.addChild(QTreeWidgetItem(["base_class", defn.base_class]))
            self._inspector.addTopLevelItem(type_section)
            type_section.setExpanded(True)
            # Embed QComboBox widgets now that section is in the tree.
            for prop_row, choices, inst_val, prop_name in combo_rows:
                combo = QComboBox()
                combo.addItems(choices)
                combo.setCurrentIndex(max(combo.findText(inst_val), 0))

                def _make_handler(n: NodeModel, pn: str, cb: QComboBox) -> None:
                    def _changed(text: str) -> None:
                        n.properties[pn] = text
                        self._live_validate()
                        if pn == "prompt_type":
                            self._update_prompt_preview(n)
                    cb.currentTextChanged.connect(_changed)

                _make_handler(node, prop_name, combo)
                self._inspector.setItemWidget(prop_row, 1, combo)

        # Provider override dropdown — shown for all LLM-type nodes
        _LLM_TYPE_IDS = {"llm_prompt_node", "json_llm_node", "classifier_node",
                         "judge_node", "agent_node"}
        is_llm_node = (node.type_id in _LLM_TYPE_IDS or "llm" in node.type_id.lower()
                       or node.type_id in {"classifier_node", "judge_node", "agent_node"})
        if is_llm_node and self._project is not None:
            prov_section = QTreeWidgetItem(["[Provider]", ""])
            prov_section.setFlags(prov_section.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            prov_row = QTreeWidgetItem(["provider", ""])
            prov_section.addChild(prov_row)
            self._inspector.addTopLevelItem(prov_section)
            prov_section.setExpanded(True)
            self._inspector.blockSignals(False)

            prov_combo = QComboBox()
            profiles = self._project.providers.profiles
            default_name = "Default"
            if profiles:
                default_profile = self._project.providers.default_profile
                if default_profile:
                    default_name = f"Default ({default_profile.name})"
            prov_combo.addItem(default_name, "")
            for p in profiles:
                prov_combo.addItem(p.name, p.id)

            current_id = str(node.properties.get("provider_id", ""))
            idx = prov_combo.findData(current_id)
            prov_combo.setCurrentIndex(max(idx, 0))

            def _provider_changed(text: str) -> None:
                selected_id = prov_combo.currentData() or ""
                if selected_id:
                    node.properties["provider_id"] = selected_id
                elif "provider_id" in node.properties:
                    del node.properties["provider_id"]
                self._live_validate()

            prov_combo.currentTextChanged.connect(_provider_changed)
            self._inspector.setItemWidget(prov_row, 1, prov_combo)
            return  # blockSignals already released above

        self._inspector.blockSignals(False)

    # ----------------------------------------- canvas signal handlers

    def _on_node_double_clicked(self, item: object) -> None:
        if not isinstance(item, NodeItem):
            return
        if self._project is None or self._active_graph_rel is None:
            self.statusBar().showMessage("No project open.")
            return
        code_path = code_manager.ensure_code_file(self._active_graph_rel, self._project.root)
        registry = self._load_node_type_registry()
        nt = registry.get(item.node.type_id)
        bc = nt.base_class if nt else ""
        line_no = code_manager.add_node(code_path, item.node, base_class=bc)
        self._open_file_in_editor(code_path)
        editor = self._bottom_editors["Python"]
        doc = editor.document()
        block = doc.findBlockByLineNumber(max(0, line_no - 1))
        cursor = editor.textCursor()
        cursor.setPosition(block.position())
        editor.setTextCursor(cursor)
        editor.ensureCursorVisible()
        self.statusBar().showMessage(f"Code: {code_path.name}  line {line_no}")

    def _on_node_created(self, item: object) -> None:
        if not isinstance(item, NodeItem):
            return
        self._ensure_active_graph()
        if self._active_graph_rel is None or self._project is None:
            return
        rel = self._active_graph_rel
        graph = self._graphs.get(rel)
        before = copy.deepcopy(graph) if graph is not None else None
        # Keep the live GraphModel in sync so save/validate see the new node
        if graph is not None and item.node not in graph.nodes:
            graph.nodes.append(item.node)
        code_path = code_manager.ensure_code_file(rel, self._project.root)
        registry = self._load_node_type_registry()
        nt = registry.get(item.node.type_id)
        bc = nt.base_class if nt else ""
        code_manager.add_node(code_path, item.node, base_class=bc)
        if graph is not None and before is not None:
            after = copy.deepcopy(graph)
            cmd = GraphSnapshotCommand("Add Node", self._graphs, rel, before, after, self._graph_scene)
            self._undo_stack.push(cmd)

    def _on_delete_selected(self) -> None:
        if self._active_graph_rel is None:
            self._graph_scene.delete_selected()
            return
        graph = self._graphs.get(self._active_graph_rel)
        before = copy.deepcopy(graph) if graph is not None else None
        self._graph_scene.delete_selected()
        # _on_node_deleted / _on_edge_deleted fire synchronously above — graph is updated
        if graph is not None and before is not None:
            after = copy.deepcopy(graph)
            if (len(after.nodes) != len(before.nodes) or len(after.edges) != len(before.edges)):
                cmd = GraphSnapshotCommand(
                    "Delete", self._graphs, self._active_graph_rel,
                    before, after, self._graph_scene,
                )
                self._undo_stack.push(cmd)

    def _on_node_deleted(self, node_id: object) -> None:
        if not isinstance(node_id, str) or self._active_graph_rel is None:
            return
        graph = self._graphs.get(self._active_graph_rel)
        if graph is not None:
            graph.nodes = [n for n in graph.nodes if n.id != node_id]
            graph.edges = [
                e for e in graph.edges
                if e.from_node != node_id and e.to_node != node_id
            ]
        if self._project is not None:
            code_path = code_manager.get_code_file(self._active_graph_rel, self._project.root)
            if code_path.exists():
                code_manager.remove_node(code_path, node_id)

    def _on_edge_deleted(self, edge_id: object) -> None:
        if not isinstance(edge_id, str) or self._active_graph_rel is None:
            return
        graph = self._graphs.get(self._active_graph_rel)
        if graph is not None:
            graph.edges = [e for e in graph.edges if e.id != edge_id]

    def _on_edge_creation_requested(self, src: object, tgt: object, action: object = "default") -> None:
        if not isinstance(src, NodeItem) or not isinstance(tgt, NodeItem):
            return
        self._ensure_active_graph()
        if self._active_graph_rel is None:
            return
        rel = self._active_graph_rel
        edge = EdgeModel(
            id=f"edge_{uuid.uuid4().hex[:8]}",
            from_node=src.node.id,
            to_node=tgt.node.id,
            action=str(action) if action else "default",
        )
        graph = self._graphs.get(rel)
        before = copy.deepcopy(graph) if graph is not None else None
        if graph is not None:
            graph.edges.append(edge)
        self._graph_scene.add_edge(src, tgt, edge)
        if graph is not None and before is not None:
            after = copy.deepcopy(graph)
            cmd = GraphSnapshotCommand("Add Edge", self._graphs, rel, before, after, self._graph_scene)
            self._undo_stack.push(cmd)

    def _on_set_start_node(self, item: object) -> None:
        if not isinstance(item, NodeItem):
            return
        if self._active_graph_rel is None:
            return
        graph = self._graphs.get(self._active_graph_rel)
        if graph is None:
            return
        graph.start_node = item.node.id
        self._graph_scene.mark_start_node(item.node.id)
        self.statusBar().showMessage(f"Start node set: {item.node.title}")

    def _on_node_rename_requested(self, item: object) -> None:
        if not isinstance(item, NodeItem):
            return
        if self._active_graph_rel is None:
            return
        graph = self._graphs.get(self._active_graph_rel)
        if graph is None:
            return
        new_title, ok = QInputDialog.getText(
            self, "Rename Node", "New title:", text=item.node.title
        )
        if not ok or not new_title.strip():
            return
        before = copy.deepcopy(graph)
        item.node.title = new_title.strip()
        item.update()  # repaint canvas tile
        after = copy.deepcopy(graph)
        if self._current_node is item.node:
            self._populate_inspector_for_node(item.node)
        cmd = GraphSnapshotCommand(
            "Rename", self._graphs, self._active_graph_rel, before, after, self._graph_scene
        )
        self._undo_stack.push(cmd)
        self.statusBar().showMessage(f"Renamed to: {item.node.title}")

    def _on_node_toggle_breakpoint_requested(self, item: object) -> None:
        if not isinstance(item, NodeItem):
            return
        nid = item.node.id
        if nid in self._breakpoints:
            self._breakpoints.discard(nid)
            item.set_breakpoint(False)
            self.statusBar().showMessage(f"Breakpoint cleared: {item.node.title}")
        else:
            self._breakpoints.add(nid)
            item.set_breakpoint(True)
            self.statusBar().showMessage(f"Breakpoint set: {item.node.title}")

    def _on_node_duplicate_requested(self, item: object) -> None:
        if not isinstance(item, NodeItem):
            return
        if self._active_graph_rel is None:
            return
        src = item.node
        offset = 30.0
        self._graph_scene.create_node_at(
            src.type_id,
            QPointF(src.position["x"] + offset, src.position["y"] + offset),
            title=src.title,
            actions=list(src.actions),
            properties=dict(src.properties),
            reads=list(src.reads),
            writes=list(src.writes),
        )

    def _on_node_delete_requested(self, item: object) -> None:
        if not isinstance(item, NodeItem):
            return
        self._graph_scene.clearSelection()
        item.setSelected(True)
        self._on_delete_selected()

    @staticmethod
    def _resolve_start_node(graph: GraphModel) -> str | None:
        """Return the best start node id for a graph, or None if no nodes exist."""
        if not graph.nodes:
            return None
        if graph.start_node and any(n.id == graph.start_node for n in graph.nodes):
            return graph.start_node
        # Prefer a node explicitly typed as start_node
        for node in graph.nodes:
            if node.type_id == "start_node":
                return node.id
        # Fall back to first node with no incoming edges
        targets = {e.to_node for e in graph.edges}
        for node in graph.nodes:
            if node.id not in targets:
                return node.id
        return graph.nodes[0].id

    def _on_auto_arrange(self) -> None:
        if self._active_graph_rel is None:
            return
        graph = self._graphs.get(self._active_graph_rel)
        if graph is None:
            return
        project = self._project
        settings: dict = dict(project.auto_arrange) if project else {}
        dlg = AutoArrangeDialog(settings, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        new_settings = dlg.get_settings()
        before = copy.deepcopy(graph)
        style = new_settings["connector_style"]
        algo = new_settings["algorithm"]
        h_gap = new_settings["h_gap"]
        v_gap = new_settings["v_gap"]
        max_cols = new_settings["max_cols"]
        self._graph_scene.set_connector_style(style)
        if algo == "grid":
            self._graph_scene.layout_grid(max_cols=max_cols, h_gap=h_gap, v_gap=v_gap)
        elif algo == "force":
            self._graph_scene.layout_force(h_gap=h_gap, v_gap=v_gap)
        else:
            self._graph_scene.auto_layout(h_gap=h_gap, v_gap=v_gap)
        after = copy.deepcopy(graph)
        rel = self._active_graph_rel
        cmd = GraphSnapshotCommand(
            "Auto Arrange", self._graphs, rel, before, after, self._graph_scene
        )
        self._undo_stack.push(cmd)
        if project:
            project.auto_arrange = new_settings
        self._graph_view.zoom_to_fit()

    def _resolve_dark(self) -> bool:
        """Return True if the effective theme is dark, based on _theme_mode."""
        if self._theme_mode == "dark":
            return True
        if self._theme_mode == "light":
            return False
        # "system" — query Qt's style hints; fall back to palette luminance
        try:
            hints = QApplication.styleHints()
            scheme = hints.colorScheme()  # type: ignore[attr-defined]
            return str(scheme).endswith("Dark")
        except AttributeError:
            palette = QApplication.palette()
            return palette.color(palette.ColorRole.Window).lightness() < 128

    def _apply_theme(self) -> None:
        self._dark_mode = self._resolve_dark()
        self._graph_scene.set_dark(self._dark_mode)
        if self._dark_mode:
            self._graph_view.setStyleSheet("background: #1a1a1a;")
        else:
            self._graph_view.setStyleSheet("")
        self._graph_view.viewport().update()
        # Re-apply the toolbar stylesheet so extension-button colours stay correct
        if hasattr(self, "_node_toolbar"):
            self._node_toolbar.setStyleSheet(
                self._node_toolbar_stylesheet(self._dark_mode)
            )

    # Ordered (locale_code, display_name) pairs for the language selector.
    _LANGUAGES: list[tuple[str, str]] = [
        ("system", "System default"),
        ("en", "English"),
        ("es", "Español"),
        ("fr", "Français"),
        ("de", "Deutsch"),
        ("zh", "中文"),
        ("ja", "日本語"),
    ]

    def _on_options(self) -> None:
        settings = QSettings(_ORG, _APP)
        dlg = QDialog(self)
        dlg.setWindowTitle(self.tr("Options"))
        layout = QVBoxLayout(dlg)

        # ── Appearance ──────────────────────────────────────────────────────
        appearance_group = QGroupBox(self.tr("Appearance"))
        group_layout = QVBoxLayout(appearance_group)

        btn_group = QButtonGroup(dlg)
        radio_system = QRadioButton(self.tr("System (follow OS setting)"))
        radio_light = QRadioButton(self.tr("Light"))
        radio_dark = QRadioButton(self.tr("Dark"))
        for rb in (radio_system, radio_light, radio_dark):
            btn_group.addButton(rb)
            group_layout.addWidget(rb)

        if self._theme_mode == "light":
            radio_light.setChecked(True)
        elif self._theme_mode == "dark":
            radio_dark.setChecked(True)
        else:
            radio_system.setChecked(True)

        layout.addWidget(appearance_group)

        # ── Language ─────────────────────────────────────────────────────────
        lang_group = QGroupBox(self.tr("Language"))
        lang_layout = QVBoxLayout(lang_group)
        lang_label = QLabel(self.tr("Restart the application to apply a language change."))
        lang_label.setWordWrap(True)
        lang_combo = QComboBox()
        current_locale = str(settings.value(_SKEY_LOCALE, "system"))
        current_index = 0
        for i, (code, display) in enumerate(self._LANGUAGES):
            lang_combo.addItem(display, code)
            if code == current_locale:
                current_index = i
        lang_combo.setCurrentIndex(current_index)
        lang_layout.addWidget(lang_label)
        lang_layout.addWidget(lang_combo)
        layout.addWidget(lang_group)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._add_help_button(buttons, "options")
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        if radio_light.isChecked():
            self._theme_mode = "light"
        elif radio_dark.isChecked():
            self._theme_mode = "dark"
        else:
            self._theme_mode = "system"

        settings.setValue(_SKEY_THEME, self._theme_mode)
        settings.setValue(_SKEY_LOCALE, lang_combo.currentData())
        self._apply_theme()
        self.statusBar().showMessage(self.tr("Options saved."))

    def _clear_selection_state(self) -> None:
        """Reset inspector and selection tracking after undo/redo."""
        self._current_node = None
        self._current_node_item = None
        self._current_edge = None
        self._inspector_snapshot = None
        self._inspector.clear()

    def _on_undo(self) -> None:
        self._undo_stack.undo()
        self._clear_selection_state()

    def _on_redo(self) -> None:
        self._undo_stack.redo()
        self._clear_selection_state()

    def _on_node_drag_started(self, node_id: str) -> None:
        if self._active_graph_rel is None:
            return
        graph = self._graphs.get(self._active_graph_rel)
        self._pre_drag_graph = copy.deepcopy(graph) if graph is not None else None

    def _on_node_move_finished(self, node_id: str) -> None:
        if self._active_graph_rel is None or self._pre_drag_graph is None:
            return
        graph = self._graphs.get(self._active_graph_rel)
        if graph is None:
            return
        rel = self._active_graph_rel
        after = copy.deepcopy(graph)
        cmd = GraphSnapshotCommand(
            "Move Node", self._graphs, rel, self._pre_drag_graph, after, self._graph_scene
        )
        self._undo_stack.push(cmd)
        self._pre_drag_graph = None

    def _on_zoom_changed(self, scale: float) -> None:
        self._zoom_label.setText(f"{int(round(scale * 100))}%")

    def _on_zoom_in(self) -> None:
        self._graph_view.zoom_in()

    def _on_zoom_out(self) -> None:
        self._graph_view.zoom_out()

    def _on_zoom_to_fit(self) -> None:
        self._graph_view.zoom_to_fit()

    def _on_zoom_to_node(self) -> None:
        if self._current_node_item is not None:
            self._graph_view.zoom_to_item(self._current_node_item)

    # ----------------------------------------- explorer double-click handlers

    def _on_explorer_item_double_clicked(self, item: QTreeWidgetItem, col: int) -> None:
        kind = item.data(0, _ROLE_KIND)
        path = item.data(0, _ROLE_PATH)
        if not isinstance(path, Path):
            return
        if kind == "shared_store_schema":
            self._open_shared_store_designer(path)
        elif kind == "file" and path.exists():
            self._open_file_in_editor(path)

    def _open_file_in_editor(self, path: Path) -> None:
        suffix = path.suffix.lower()
        if suffix == ".py":
            tab_name = "Python"
        elif suffix in (".md", ".markdown"):
            tab_name = "Markdown"
        elif suffix in (".yaml", ".yml"):
            tab_name = "YAML"
        else:
            return
        try:
            content = path.read_text(encoding="utf-8")
        except Exception as exc:
            QMessageBox.warning(self, "Open Failed", str(exc))
            return
        editor = self._bottom_editors[tab_name]
        editor.setPlainText(content)
        self._bottom_tab_paths[tab_name] = path
        self._apply_highlighter(tab_name, editor)
        self._switch_bottom_tab(tab_name)
        self.statusBar().showMessage(f"Opened: {path.name}")

    def _apply_highlighter(self, tab_name: str, editor: QPlainTextEdit) -> None:
        old = self._active_highlighters.get(tab_name)
        if old is not None and hasattr(old, "setDocument"):
            old.setDocument(None)  # type: ignore[attr-defined]
        if tab_name == "Python":
            self._active_highlighters[tab_name] = PythonHighlighter(editor.document())
        elif tab_name == "YAML":
            self._active_highlighters[tab_name] = YamlHighlighter(editor.document())
        else:
            self._active_highlighters.pop(tab_name, None)

    def _save_editor_file(self, tab_name: str) -> None:
        path = self._bottom_tab_paths.get(tab_name)
        if path is None:
            return
        try:
            path.write_text(self._bottom_editors[tab_name].toPlainText(), encoding="utf-8")
            self.statusBar().showMessage(f"Saved: {path.name}")
        except Exception as exc:
            QMessageBox.critical(self, "Save Failed", str(exc))
            return
        if tab_name == "Python":
            self._sync_graph_from_code(path)

    def _sync_graph_from_code(self, code_path: Path) -> None:
        """Remove canvas nodes whose NODE_START marker no longer exists in the code file."""
        if self._project is None or self._active_graph_rel is None:
            return
        expected = code_manager.get_code_file(self._active_graph_rel, self._project.root)
        if code_path.resolve() != expected.resolve():
            return  # saved file is not the active graph's code file
        try:
            text = code_path.read_text(encoding="utf-8")
        except OSError:
            return
        present = set(re.findall(r"# --- NODE_START: (\S+) ---", text))
        for node_id in list(self._graph_scene._node_items):
            if node_id not in present:
                self._graph_scene.delete_node_by_id(node_id)
                removed = self._graphs.get(self._active_graph_rel)
                if removed is not None:
                    removed.nodes = [n for n in removed.nodes if n.id != node_id]

    def _on_yaml_editor_changed(self) -> None:
        text = self._bottom_editors["YAML"].toPlainText()
        try:
            yaml.safe_load(text)
            self.statusBar().showMessage("YAML: valid")
        except yaml.YAMLError as exc:
            first_line = str(exc).split("\n")[0]
            self.statusBar().showMessage(f"YAML: {first_line}")

    def _on_markdown_editor_changed(self) -> None:
        text = self._bottom_editors["Markdown"].toPlainText()
        self._markdown_preview.setMarkdown(text)

    # ----------------------------------------------- tools menu handlers

    def _on_provider_manager(self) -> None:
        providers = self._project.providers if self._project else None
        updated = exec_provider_manager(self, self._open_help, providers=providers)
        if updated is not None:
            if self._project:
                self._project.providers = updated
            self.statusBar().showMessage("Provider settings saved.")

    def _on_tool_registry(self) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle(self.tr("Tool Registry"))
        dlg.resize(700, 420)
        layout = QVBoxLayout(dlg)

        table = QTableWidget(0, 3)
        table.setHorizontalHeaderLabels(
            [self.tr("Function"), self.tr("File"), self.tr("Description")]
        )
        table.horizontalHeader().setStretchLastSection(True)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(table)

        tools_found: list[tuple[str, str, str]] = []

        if self._project is not None:
            tools_dir = self._project.root / "tools"
            if tools_dir.is_dir():
                for py_file in sorted(tools_dir.glob("*.py")):
                    try:
                        source = py_file.read_text(encoding="utf-8")
                        tree = ast.parse(source, filename=str(py_file))
                    except SyntaxError:
                        continue
                    for node in ast.walk(tree):
                        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            continue
                        decorator_names = []
                        for dec in node.decorator_list:
                            if isinstance(dec, ast.Name):
                                decorator_names.append(dec.id)
                            elif isinstance(dec, ast.Attribute):
                                decorator_names.append(dec.attr)
                        if "tool" not in decorator_names:
                            continue
                        docstring = ast.get_docstring(node) or ""
                        first_line = docstring.splitlines()[0] if docstring else ""
                        tools_found.append((node.name, py_file.name, first_line))

        if tools_found:
            table.setRowCount(len(tools_found))
            for row, (name, fname, desc) in enumerate(tools_found):
                table.setItem(row, 0, QTableWidgetItem(name))
                table.setItem(row, 1, QTableWidgetItem(fname))
                table.setItem(row, 2, QTableWidgetItem(desc))
        else:
            no_project = self._project is None
            msg = (
                self.tr("No project open.")
                if no_project
                else self.tr(
                    "No @tool functions found.\n\n"
                    "Add Python files with @tool-decorated functions to the"
                    " project's tools/ directory."
                )
            )
            layout.insertWidget(0, QLabel(msg))

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self._add_help_button(buttons, "tool_registry")
        buttons.accepted.connect(dlg.accept)
        layout.addWidget(buttons)
        dlg.exec()

    def _on_node_type_library(self) -> None:
        """Open the Node Type Library dialog.

        Shows all built-in and installed custom nodes.  Allows importing a
        single-file ``.py`` node package into ``~/.pocketflow_creator/nodes/``
        so it is available immediately (palette refresh) and on every future
        launch.  Also supports the legacy YAML import for project-local types.
        """
        from pocketflow_creator.node_package_loader import (
            PackageLoadError,
            get_package_meta,
            load_node_package,
            register_user_node,
        )

        # ── Build the dialog ──────────────────────────────────────────────
        dlg = QDialog(self)
        dlg.setWindowTitle("Node Type Library")
        dlg.resize(820, 520)
        layout = QVBoxLayout(dlg)

        # Tab widget: Built-ins | Installed Custom | Load Errors
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # ── Tab 1: built-in nodes ─────────────────────────────────────────
        builtin_table = QTableWidget(len(BUILTIN_NODE_TYPES), 3)
        builtin_table.setHorizontalHeaderLabels(["Node Type ID", "Display Name", "Category"])
        builtin_table.horizontalHeader().setStretchLastSection(True)
        builtin_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        builtin_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        for r, defn in enumerate(BUILTIN_NODE_TYPES.values()):
            builtin_table.setItem(r, 0, QTableWidgetItem(defn.node_type_id))
            builtin_table.setItem(r, 1, QTableWidgetItem(defn.display_name))
            builtin_table.setItem(r, 2, QTableWidgetItem(defn.category))
        builtin_table.resizeColumnsToContents()
        tabs.addTab(builtin_table, f"Built-in ({len(BUILTIN_NODE_TYPES)})")

        # ── Tab 2: add-on scientific / engineering node packages ─────────
        addon_nodes = get_all_addon_nodes()
        addon_table = QTableWidget(len(addon_nodes), 5)
        addon_table.setHorizontalHeaderLabels(
            ["Display Name", "Category", "Version", "Description", "Website"]
        )
        addon_table.horizontalHeader().setStretchLastSection(True)
        addon_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        addon_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        for r, defn in enumerate(sorted(addon_nodes.values(), key=lambda d: (d.category, d.display_name))):
            m = get_package_meta(defn.node_type_id)
            addon_table.setItem(r, 0, QTableWidgetItem(defn.display_name))
            addon_table.setItem(r, 1, QTableWidgetItem(defn.category))
            addon_table.setItem(r, 2, QTableWidgetItem(m.get("version", "")))
            addon_table.setItem(r, 3, QTableWidgetItem(defn.description or ""))
            addon_table.setItem(r, 4, QTableWidgetItem(m.get("website", "")))
        addon_table.resizeColumnsToContents()
        tabs.addTab(addon_table, f"Scientific & Engineering ({len(addon_nodes)})")

        # ── Tab 3: installed custom node packages ─────────────────────────
        custom_layout = QVBoxLayout()
        custom_widget = QWidget()
        custom_widget.setLayout(custom_layout)

        user_nodes = get_all_user_nodes()
        custom_table = QTableWidget(len(user_nodes), 6)
        custom_table.setHorizontalHeaderLabels(
            ["Display Name", "Category", "Version", "Author", "License", "File"]
        )
        custom_table.horizontalHeader().setStretchLastSection(True)
        custom_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        custom_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        for r, defn in enumerate(user_nodes.values()):
            m = get_package_meta(defn.node_type_id)
            custom_table.setItem(r, 0, QTableWidgetItem(defn.display_name))
            custom_table.setItem(r, 1, QTableWidgetItem(defn.category))
            custom_table.setItem(r, 2, QTableWidgetItem(m.get("version", "")))
            custom_table.setItem(r, 3, QTableWidgetItem(m.get("author", "")))
            custom_table.setItem(r, 4, QTableWidgetItem(m.get("license", "")))
            src = Path(m.get("source_file", "")).name
            custom_table.setItem(r, 5, QTableWidgetItem(src))
        custom_table.resizeColumnsToContents()
        custom_layout.addWidget(custom_table)

        # Detail panel shown when a row is selected
        detail_label = QLabel("")
        detail_label.setWordWrap(True)
        detail_label.setStyleSheet("font-size: 11px; color: grey;")
        custom_layout.addWidget(detail_label)

        def _on_custom_row_selected() -> None:
            rows = custom_table.selectedItems()
            if not rows:
                detail_label.setText("")
                return
            r = custom_table.currentRow()
            defn = list(user_nodes.values())[r]
            m = get_package_meta(defn.node_type_id)
            desc = defn.description
            tags = ", ".join(m.get("tags", []))
            website = m.get("website", "")
            repo = m.get("repo", "")
            parts = []
            if desc:
                parts.append(desc)
            if tags:
                parts.append(f"Tags: {tags}")
            if website:
                parts.append(f"Website: {website}")
            if repo:
                parts.append(f"Repo: {repo}")
            detail_label.setText("  ·  ".join(parts))

        custom_table.itemSelectionChanged.connect(_on_custom_row_selected)

        # Button row for custom tab
        custom_btn_row = QHBoxLayout()
        install_py_btn = QPushButton("Install node package (.py)…")
        open_dir_btn = QPushButton("Open nodes folder")
        custom_btn_row.addWidget(install_py_btn)
        custom_btn_row.addWidget(open_dir_btn)
        custom_btn_row.addStretch()
        custom_layout.addLayout(custom_btn_row)
        tabs.addTab(custom_widget, f"Installed Custom ({len(user_nodes)})")

        # ── Tab 4: load errors ────────────────────────────────────────────
        errors = (
            getattr(self, "_addon_node_load_errors", []) +
            getattr(self, "_user_node_load_errors", [])
        )
        if errors:
            err_table = QTableWidget(len(errors), 2)
            err_table.setHorizontalHeaderLabels(["File", "Error"])
            err_table.horizontalHeader().setStretchLastSection(True)
            err_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            for r, (fname, msg) in enumerate(errors):
                err_table.setItem(r, 0, QTableWidgetItem(fname))
                err_table.setItem(r, 1, QTableWidgetItem(msg))
            err_table.resizeColumnsToContents()
            tabs.addTab(err_table, f"⚠ Errors ({len(errors)})")
            tabs.setCurrentIndex(2)  # draw attention to errors

        # ── Button actions ────────────────────────────────────────────────
        def _install_py() -> None:
            nodes_dir = get_user_nodes_dir()
            path_str, _ = QFileDialog.getOpenFileName(
                dlg,
                "Install Node Package",
                str(Path.home()),
                "Python Node Package (*.py)",
            )
            if not path_str:
                return
            src = Path(path_str)
            dest = nodes_dir / src.name
            if dest.exists():
                answer = QMessageBox.question(
                    dlg,
                    "Overwrite?",
                    f"{src.name} is already installed. Replace it?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if answer != QMessageBox.StandardButton.Yes:
                    return
            try:
                defn = load_node_package(src)
                import shutil as _shutil
                _shutil.copy2(src, dest)
                register_user_node(defn)
                # Refresh the palette (rebuild its widget)
                new_palette = __import__(
                    "pocketflow_creator.app.canvas.palette",
                    fromlist=["PaletteWidget"],
                ).PaletteWidget()
                self._palette_dock.setWidget(new_palette)
                QMessageBox.information(
                    dlg,
                    "Installed",
                    f"'{defn.display_name}' installed successfully.\n"
                    f"Restart the application to add it to the toolbar.",
                )
                dlg.accept()
            except PackageLoadError as exc:
                QMessageBox.critical(dlg, "Load Error", str(exc))

        def _open_dir() -> None:
            import subprocess as _sp
            d = str(get_user_nodes_dir())
            if sys.platform == "win32":
                _sp.Popen(["explorer", d])
            elif sys.platform == "darwin":
                _sp.Popen(["open", d])
            else:
                _sp.Popen(["xdg-open", d])

        install_py_btn.clicked.connect(_install_py)
        open_dir_btn.clicked.connect(_open_dir)

        # ── Dialog close button ───────────────────────────────────────────
        ok = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        ok.accepted.connect(dlg.accept)
        layout.addWidget(ok)
        dlg.exec()

    def _on_shared_store_inspector(self) -> None:
        self._switch_bottom_tab("Shared Store")
        self.statusBar().showMessage("Shared Store Inspector — populated during run.")

    def _open_shared_store_designer(self, path: Path) -> None:
        open_shared_store_designer(
            path=path,
            parent=self,
            open_help=self._open_help,
            on_saved=self.statusBar().showMessage,
        )


def run(argv: Sequence[str] | None = None) -> int:
    if QApplication is None:
        raise RuntimeError("PySide6 is not available. Install project dependencies first.")
    app = QApplication(list(argv or []))
    app.setApplicationName("PocketFlow Creator")
    app.setOrganizationName(_ORG)

    # Install locale-specific translator before building the main window
    _settings = QSettings(_ORG, _APP)
    locale_code = str(_settings.value(_SKEY_LOCALE, "system"))
    _trans_dir = str(Path(__file__).parent.parent / "translations")
    _locale = QLocale.system() if locale_code == "system" else QLocale(locale_code)
    _translator = QTranslator(app)
    if _translator.load(_locale, "pocketflow_creator", "_", _trans_dir):
        app.installTranslator(_translator)

    window = MainWindow()
    window.show()
    return app.exec()

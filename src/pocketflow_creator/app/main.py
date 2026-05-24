from __future__ import annotations

import shutil
from collections.abc import Sequence
from pathlib import Path

import yaml

try:
    from PySide6.QtCore import QLocale, QSettings, Qt, QTranslator, QUrl
    from PySide6.QtGui import (
        QBrush,
        QColor,
        QDesktopServices,
        QKeySequence,
        QUndoStack,
    )
    from PySide6.QtWidgets import (
        QApplication,
        QButtonGroup,
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
        QTreeWidget,
        QTreeWidgetItem,
        QVBoxLayout,
    )

    from pocketflow_creator.app.canvas import (
        EdgeItem,
        GraphScene,
        GraphView,
        NodeItem,
        PaletteWidget,
    )
    from pocketflow_creator.app.editors import PythonHighlighter, YamlHighlighter
except Exception:  # pragma: no cover - permits import in non-GUI test environments
    QApplication = None  # type: ignore[assignment,misc]

from pocketflow_creator.generation.exporter import Exporter
from pocketflow_creator.generation.python_generator import PythonGenerator
from pocketflow_creator.generation.report import generate_project_report
from pocketflow_creator.graph_io import GraphLoader, GraphSaver
from pocketflow_creator.model.graph_model import EdgeModel, GraphModel, NodeModel
from pocketflow_creator.model.node_type import NodeTypeDefinition
from pocketflow_creator.model.project import ProjectModel
from pocketflow_creator.project_io import ProjectLoader, ProjectSaver
from pocketflow_creator.runtime.providers import MockProvider, OllamaProvider
from pocketflow_creator.runtime.runner import FlowRunner, RunStep, StepController
from pocketflow_creator.validation.graph_validator import GraphValidator

_MAX_RECENT = 5
_VERSION = "0.1.0"


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
        self._debug_controller: StepController | None = None
        self._debug_thread: object = None  # QThread when active
        self._breakpoints: set[str] = set()
        _settings = QSettings("Monotoba", "PocketFlowCreator")
        # Migrate old bool setting → string if needed
        _stored = _settings.value("ui/theme", None)
        if _stored is None:
            _old = _settings.value("ui/dark_mode", None)
            _stored = "dark" if _old is True or _old == "true" else (
                "light" if _old is False or _old == "false" else "system"
            )
        self._theme_mode: str = str(_stored)
        self._dark_mode: bool = self._resolve_dark()
        self._stop_action: object  # QAction — assigned in _build_menu_bar
        self._resume_action: object  # QAction — assigned in _build_menu_bar
        # Assigned by their respective _build_* methods:
        self._explorer_tree: QTreeWidget
        self._bottom_tab_widget: QTabWidget
        self._markdown_preview: QTextBrowser
        self._recent_menu: QMenu
        self._inspector: QTreeWidget
        self._graph_view: GraphView
        self._graph_scene = GraphScene()
        self.setWindowTitle(self.tr("PocketFlow Creator"))
        self.resize(1400, 900)
        self._build_menu_bar()
        self._build_central_area()
        self._build_docks()
        self._graph_scene.node_item_selected.connect(self._on_node_item_selected)
        self._graph_scene.edge_item_selected.connect(self._on_edge_item_selected)
        self._graph_scene.selection_cleared.connect(self._on_selection_cleared)
        self._graph_scene.node_item_double_clicked.connect(self._on_node_double_clicked)
        self._graph_scene.node_created.connect(self._on_node_created)
        self._graph_scene.node_deleted.connect(self._on_node_deleted)
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
        self.statusBar().showMessage(self.tr("Ready"))

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
        undo_act = edit_menu.addAction(self.tr("Undo"), self._undo_stack.undo)
        undo_act.setShortcut(QKeySequence.StandardKey.Undo)
        redo_act = edit_menu.addAction(self.tr("Redo"), self._undo_stack.redo)
        redo_act.setShortcut(QKeySequence.StandardKey.Redo)
        edit_menu.addSeparator()
        cut_act = edit_menu.addAction(self.tr("Cut"))
        cut_act.setShortcut(QKeySequence.StandardKey.Cut)
        copy_act = edit_menu.addAction(self.tr("Copy"))
        copy_act.setShortcut(QKeySequence.StandardKey.Copy)
        paste_act = edit_menu.addAction(self.tr("Paste"))
        paste_act.setShortcut(QKeySequence.StandardKey.Paste)
        edit_menu.addAction(self.tr("Duplicate"))
        del_act = edit_menu.addAction(self.tr("Delete"))
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
        act = view_menu.addAction(self.tr("Zoom to Fit"), self._on_zoom_to_fit)
        act.setShortcut(QKeySequence("Ctrl+0"))
        act = view_menu.addAction(self.tr("Auto Layout"), self._on_auto_layout)
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
        project_menu.addAction(self.tr("Provider Profiles..."))

        flow_menu = self.menuBar().addMenu(self.tr("Flow"))
        for name in [
            self.tr("New Flow..."),
            self.tr("New Subflow..."),
            self.tr("Set Start Node"),
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
        for name in [
            self.tr("Reset Layout"),
            self.tr("Next Tab"),
            self.tr("Previous Tab"),
        ]:
            window_menu.addAction(name)

        help_menu = self.menuBar().addMenu(self.tr("Help"))
        _help_act = help_menu.addAction(self.tr("PocketFlow Creator Help"), self._on_help)
        _help_act.setShortcut(QKeySequence(Qt.Key.Key_F1))
        help_menu.addAction(self.tr("PocketFlow Quick Reference"), self._on_help_tutorials)
        help_menu.addAction(self.tr("About PocketFlow Creator"), self._on_about)

    # --------------------------------------------------------------- layout

    def _build_central_area(self) -> None:
        self._graph_view = GraphView(self._graph_scene)
        self.setCentralWidget(self._graph_view)

    def _build_docks(self) -> None:
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._build_project_explorer())
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._build_component_palette())
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._build_object_inspector())
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self._build_bottom_dock())

    def _build_project_explorer(self) -> QDockWidget:
        dock = QDockWidget(self.tr("Project Explorer"), self)
        self._explorer_tree = QTreeWidget()
        self._explorer_tree.setHeaderHidden(True)
        dock.setWidget(self._explorer_tree)
        return dock

    def _build_component_palette(self) -> QDockWidget:
        dock = QDockWidget(self.tr("Component Palette"), self)
        dock.setWidget(PaletteWidget())
        return dock

    def _build_object_inspector(self) -> QDockWidget:
        dock = QDockWidget(self.tr("Object Inspector"), self)
        self._inspector = QTreeWidget()
        self._inspector.setHeaderLabels([self.tr("Property"), self.tr("Value")])
        self._inspector.setAlternatingRowColors(True)
        self._inspector.header().setStretchLastSection(True)
        dock.setWidget(self._inspector)
        return dock

    def _build_bottom_dock(self) -> QDockWidget:
        dock = QDockWidget(self.tr("Output"), self)
        self._bottom_tab_widget = QTabWidget()
        plain_tabs = [
            ("Problems", self.tr("No validation has been run.")),
            ("Run Log", self.tr("No active run.")),
            ("Shared Store", "{}"),
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
        md_splitter = QSplitter(Qt.Orientation.Horizontal)
        md_editor = QPlainTextEdit()
        md_editor.setPlainText(self.tr("Open a prompt file to edit Markdown."))
        self._markdown_preview = QTextBrowser()
        self._markdown_preview.setPlainText(self.tr("Preview appears here."))
        md_splitter.addWidget(md_editor)
        md_splitter.addWidget(self._markdown_preview)
        md_splitter.setSizes([1, 1])
        self._bottom_tab_widget.addTab(md_splitter, self.tr("Markdown"))
        self._bottom_editors["Markdown"] = md_editor
        self._bottom_tab_paths["Markdown"] = None

        dock.setWidget(self._bottom_tab_widget)
        return dock

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
        for i in range(self._bottom_tab_widget.count()):
            if self._bottom_tab_widget.tabText(i) == name:
                self._bottom_tab_widget.setCurrentIndex(i)
                break

    # -------------------------------------------------------- recent projects

    def _load_recent(self) -> list[Path]:
        settings = QSettings("Monotoba", "PocketFlowCreator")
        raw = settings.value("recent_projects", [])
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
        settings = QSettings("Monotoba", "PocketFlowCreator")
        settings.setValue("recent_projects", [str(p) for p in self._recent])
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
        self._project = ProjectModel(name=name, package_name=package, root=root)
        self._graphs = {}
        try:
            root.mkdir(parents=True, exist_ok=True)
            ProjectSaver().save(self._project)
            self._add_recent(self._project.project_file)
        except Exception as exc:
            QMessageBox.warning(self, "New Project Warning", f"Could not write project:\n{exc}")
        self._refresh_explorer()
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
            self._project = ProjectLoader().load(path)
            self._graphs = {}
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
            if self._graphs:
                self._active_graph_rel = next(iter(self._graphs.keys()))
                self._graph_scene.load_graph(self._graphs[self._active_graph_rel])
                self._graph_view.zoom_to_fit()
            self._refresh_explorer()
            self._add_recent(path)
            self.statusBar().showMessage(f"Opened: {self._project.name}")
        except Exception as exc:
            QMessageBox.critical(self, "Open Failed", str(exc))

    def _on_save(self) -> None:
        if self._project is None:
            self.statusBar().showMessage("No project open.")
            return
        try:
            ProjectSaver().save(self._project)
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
        if self._project is None or not self._graphs:
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
            from PySide6.QtCore import QRectF
            from PySide6.QtGui import QImage, QPainter

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
                img.fill(0xFF1A1A1A)
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

    # ----------------------------------------------- run menu handlers

    def _on_run_active_flow(self) -> None:
        if self._project is None or not self._graphs:
            self.statusBar().showMessage("No graphs to run.")
            return
        graph = next(iter(self._graphs.values()))
        rel = next(iter(self._graphs.keys()))

        settings = QSettings("Monotoba", "PocketFlowCreator")
        prov_type = str(settings.value("run/provider", "mock"))
        if prov_type == "ollama":
            provider: MockProvider | OllamaProvider = OllamaProvider(
                base_url=str(settings.value("ollama/base_url", "http://localhost:11434")),
                default_model=str(settings.value("ollama/default_model", "qwen2.5-coder:14b")),
            )
        else:
            provider = MockProvider(
                response=str(settings.value("mock/response", "mock response"))
            )

        runner = FlowRunner()
        known_graphs = {k: v for k, v in self._graphs.items() if k != rel}
        try:
            trace = runner.run(
                graph, provider,
                project_name=self._project.name,
                known_graphs=known_graphs or None,
            )
        except Exception as exc:
            QMessageBox.critical(self, "Run Failed", str(exc))
            return

        lines: list[str] = [f"Run: {graph.title}  ({len(trace.steps)} step(s))\n"]
        for step in trace.steps:
            lines.append(f"  [{step.node_id}] {step.node_title}  → {step.action}")
            if step.response:
                lines.append(f"      response: {step.response}")
        self._bottom_editors["Run Log"].setPlainText("\n".join(lines))
        self._switch_bottom_tab("Run Log")

        shared_text = "\n".join(
            f"{k}: {v}" for k, v in (trace.steps[-1].shared_after if trace.steps else {}).items()
        )
        self._bottom_editors["Shared Store"].setPlainText(shared_text or "{}")

        if self._project.root:
            try:
                out = runner.save_trace(trace, self._project.root / "run_reports")
                self.statusBar().showMessage(f"Run complete — trace saved: {out.name}")
            except Exception:
                self.statusBar().showMessage("Run complete.")
        else:
            self.statusBar().showMessage("Run complete.")

        _ = rel  # keep for future per-graph selection

    def _on_run_tests(self) -> None:
        import subprocess
        import sys

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
        if self._project is None or not self._graphs:
            self.statusBar().showMessage("No graphs to debug.")
            return
        _debug_rel = next(iter(self._graphs.keys()))
        graph = self._graphs[_debug_rel]
        _debug_known = {k: v for k, v in self._graphs.items() if k != _debug_rel}
        settings = QSettings("Monotoba", "PocketFlowCreator")
        prov_type = str(settings.value("run/provider", "mock"))
        if prov_type == "ollama":
            provider: MockProvider | OllamaProvider = OllamaProvider(
                base_url=str(settings.value("ollama/base_url", "http://localhost:11434")),
                default_model=str(settings.value("ollama/default_model", "qwen2.5-coder:14b")),
            )
        else:
            provider = MockProvider(
                response=str(settings.value("mock/response", "mock response"))
            )

        ctrl = StepController()
        self._debug_controller = ctrl
        runner = FlowRunner()
        self._bottom_editors["Run Log"].setPlainText("Debug run started…\n")
        self._switch_bottom_tab("Run Log")

        def _on_step(step: object) -> None:
            if not isinstance(step, RunStep):
                return
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

        import threading as _threading

        collected: list[object] = []

        def _run_thread() -> None:
            trace = runner.run_debug(
                graph,
                provider,
                ctrl,
                breakpoints=self._breakpoints,
                on_step=_on_step,
                project_name=self._project.name if self._project else "",
                known_graphs=_debug_known or None,
            )
            collected.append(trace)

        t = _threading.Thread(target=_run_thread, daemon=True)
        self._debug_thread = t
        t.start()
        self._stop_action.setEnabled(True)  # type: ignore[attr-defined]
        self._resume_action.setEnabled(True)  # type: ignore[attr-defined]
        self.statusBar().showMessage("Debug run started.")

    def _on_stop_debug(self) -> None:
        if self._debug_controller is not None:
            self._debug_controller.stop()
            self._debug_controller = None
        self._stop_action.setEnabled(False)  # type: ignore[attr-defined]
        self._resume_action.setEnabled(False)  # type: ignore[attr-defined]
        self.statusBar().showMessage("Debug run stopped.")

    def _on_resume_debug(self) -> None:
        if self._debug_controller is not None:
            self._debug_controller.resume()
        self.statusBar().showMessage("Resumed.")

    # ----------------------------------------------- help handlers

    def _open_help(self, page: str = "index.md") -> None:
        from pocketflow_creator.app.help_browser import HelpBrowser

        dlg = HelpBrowser(page, self)
        dlg.exec()

    def _on_help(self) -> None:
        self._open_help("index.md")

    def _on_help_tutorials(self) -> None:
        self._open_help("tutorials/index.md")

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
            f"PocketFlow Creator v{_VERSION}\n\n"
            "RAD visual designer for PocketFlow LLM workflows.",
        )

    # ----------------------------------------------- node menu handlers

    def _on_new_custom_node_type(self) -> None:
        from pocketflow_creator.app.node_type_wizard import NodeTypeWizard

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
        import yaml as _yaml

        yaml_path.write_text(
            _yaml.dump(defn, default_flow_style=False, allow_unicode=True), encoding="utf-8"
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
        prompt_file = node.properties.get("prompt_file", "") if node.properties else ""
        if not prompt_file or self._project is None:
            self._bottom_editors["Prompt Preview"].setPlainText(
                f"[{node.title}] No prompt_file property set."
            )
            self._switch_bottom_tab("Prompt Preview")
            return
        full_path = self._project.root / str(prompt_file)
        try:
            content = full_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            content = f"(prompt file not found: {prompt_file})"
        except Exception as exc:
            content = f"(error reading {prompt_file}: {exc})"
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
        self._inspector.blockSignals(True)
        self._inspector.clear()
        for label, value in [
            ("ID", self._current_edge.id),
            ("From", self._current_edge.from_node),
            ("Action", self._current_edge.action),
            ("To", self._current_edge.to_node),
        ]:
            self._inspector.addTopLevelItem(QTreeWidgetItem([label, value]))
        self._inspector.blockSignals(False)

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
        from pocketflow_creator.validation.graph_validator import GraphValidator

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

    def _load_node_type_registry(self) -> dict[str, NodeTypeDefinition]:
        registry: dict[str, NodeTypeDefinition] = {}
        if self._project is None:
            return registry
        for rel in self._project.node_types:
            path = self._project.root / rel
            if not path.exists():
                continue
            try:
                import yaml as _yaml

                data = _yaml.safe_load(path.read_text(encoding="utf-8"))
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
            for prop_name, prop_meta in defn.properties.items():
                default = str(prop_meta.get("default", "")) if isinstance(prop_meta, dict) else ""
                inst_val = str(node.properties.get(prop_name, default))
                prop_type = (
                    prop_meta.get("type", "string") if isinstance(prop_meta, dict) else "string"
                )
                prop_row = QTreeWidgetItem([prop_name, inst_val])
                prop_row.setFlags(prop_row.flags() | Qt.ItemFlag.ItemIsEditable)
                prop_row.setData(1, Qt.ItemDataRole.UserRole, prop_type)
                self._style_editable(prop_row)
                type_section.addChild(prop_row)
            if defn.base_class and defn.base_class != node.type_id:
                type_section.addChild(QTreeWidgetItem(["base_class", defn.base_class]))
            self._inspector.addTopLevelItem(type_section)
            type_section.setExpanded(True)

        self._inspector.blockSignals(False)

    # ----------------------------------------- canvas signal handlers

    def _on_node_double_clicked(self, item: object) -> None:
        from pocketflow_creator.app import code_manager
        from pocketflow_creator.app.canvas import NodeItem

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
        from pocketflow_creator.app import code_manager
        from pocketflow_creator.app.canvas import NodeItem

        if not isinstance(item, NodeItem):
            return
        if self._project is None or self._active_graph_rel is None:
            return
        code_path = code_manager.ensure_code_file(self._active_graph_rel, self._project.root)
        registry = self._load_node_type_registry()
        nt = registry.get(item.node.type_id)
        bc = nt.base_class if nt else ""
        code_manager.add_node(code_path, item.node, base_class=bc)

    def _on_node_deleted(self, node_id: object) -> None:
        from pocketflow_creator.app import code_manager

        if not isinstance(node_id, str):
            return
        if self._project is None or self._active_graph_rel is None:
            return
        code_path = code_manager.get_code_file(self._active_graph_rel, self._project.root)
        if code_path.exists():
            code_manager.remove_node(code_path, node_id)

    def _on_auto_layout(self) -> None:
        self._graph_scene.auto_layout()
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
        settings = QSettings("Monotoba", "PocketFlowCreator")
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
        current_locale = str(settings.value("ui/locale", "system"))
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

        settings.setValue("ui/theme", self._theme_mode)
        settings.setValue("ui/locale", lang_combo.currentData())
        self._apply_theme()
        self.statusBar().showMessage(self.tr("Options saved."))

    def _on_zoom_to_fit(self) -> None:
        self._graph_view.zoom_to_fit()

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
        settings = QSettings("Monotoba", "PocketFlowCreator")
        dlg = QDialog(self)
        dlg.setWindowTitle("Provider Manager")
        layout = QVBoxLayout(dlg)

        ollama_group = QGroupBox("Ollama Provider")
        ollama_form = QFormLayout(ollama_group)
        ollama_url = QLineEdit(str(settings.value("ollama/base_url", "http://localhost:11434")))
        ollama_model = QLineEdit(str(settings.value("ollama/default_model", "qwen2.5-coder:14b")))
        ollama_form.addRow("Base URL:", ollama_url)
        ollama_form.addRow("Default model:", ollama_model)
        layout.addWidget(ollama_group)

        mock_group = QGroupBox("Mock Provider")
        mock_form = QFormLayout(mock_group)
        mock_response = QLineEdit(str(settings.value("mock/response", "mock response")))
        mock_form.addRow("Fixed response:", mock_response)
        layout.addWidget(mock_group)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._add_help_button(buttons, "provider_manager")
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        settings.setValue("ollama/base_url", ollama_url.text().strip())
        settings.setValue("ollama/default_model", ollama_model.text().strip())
        settings.setValue("mock/response", mock_response.text())
        self.statusBar().showMessage("Provider settings saved.")

    def _on_tool_registry(self) -> None:
        import ast as _ast

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
                        tree = _ast.parse(source, filename=str(py_file))
                    except SyntaxError:
                        continue
                    for node in _ast.walk(tree):
                        if not isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
                            continue
                        decorator_names = []
                        for dec in node.decorator_list:
                            if isinstance(dec, _ast.Name):
                                decorator_names.append(dec.id)
                            elif isinstance(dec, _ast.Attribute):
                                decorator_names.append(dec.attr)
                        if "tool" not in decorator_names:
                            continue
                        docstring = _ast.get_docstring(node) or ""
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
        if self._project is None:
            self.statusBar().showMessage("No project open.")
            return
        registry = self._load_node_type_registry()
        dlg = QDialog(self)
        dlg.setWindowTitle("Node Type Library")
        dlg.resize(640, 400)
        layout = QVBoxLayout(dlg)
        table = QTableWidget(len(registry), 4)
        table.setHorizontalHeaderLabels(["ID", "Display Name", "Category", "Base Class"])
        table.horizontalHeader().setStretchLastSection(True)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        for r, defn in enumerate(registry.values()):
            table.setItem(r, 0, QTableWidgetItem(defn.node_type_id))
            table.setItem(r, 1, QTableWidgetItem(defn.display_name))
            table.setItem(r, 2, QTableWidgetItem(defn.category))
            table.setItem(r, 3, QTableWidgetItem(defn.base_class))
        layout.addWidget(table)
        btn_row = QHBoxLayout()
        import_btn = QPushButton("Import from file…")
        btn_row.addWidget(import_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        def _import() -> None:
            path_str, _ = QFileDialog.getOpenFileName(
                dlg, "Import Node Type", "", "YAML (*.yaml *.yml)"
            )
            if not path_str:
                return
            import shutil

            dest = self._project.root / "node_types" / Path(path_str).name  # type: ignore[union-attr]
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path_str, dest)
            rel = f"node_types/{dest.name}"
            if rel not in self._project.node_types:  # type: ignore[union-attr]
                self._project.node_types.append(rel)  # type: ignore[union-attr]
            self._refresh_explorer()
            self.statusBar().showMessage(f"Imported: {dest.name}")
            dlg.accept()

        import_btn.clicked.connect(_import)
        ok = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        ok.accepted.connect(dlg.accept)
        layout.addWidget(ok)
        dlg.exec()

    def _on_shared_store_inspector(self) -> None:
        self._switch_bottom_tab("Shared Store")
        self.statusBar().showMessage("Shared Store Inspector — populated during run.")

    def _open_shared_store_designer(self, path: Path) -> None:
        raw: dict = {}
        if path.exists():
            try:
                loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    raw = loaded
            except yaml.YAMLError:
                pass

        flat: list[tuple[str, str, str, str]] = []
        for ns, keys in raw.items():
            if not isinstance(keys, dict):
                continue
            for key, props in keys.items():
                if not isinstance(props, dict):
                    continue
                type_str = str(props.get("type", ""))
                default_str = str(props["default"]) if "default" in props else ""
                flat.append((str(ns), str(key), type_str, default_str))

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Shared Store Designer — {path.name}")
        dlg.resize(640, 400)
        main_layout = QVBoxLayout(dlg)

        table = QTableWidget(len(flat), 4)
        table.setHorizontalHeaderLabels(["Namespace", "Key", "Type", "Default"])
        table.horizontalHeader().setStretchLastSection(True)
        for r, (ns, key, type_str, default_str) in enumerate(flat):
            table.setItem(r, 0, QTableWidgetItem(ns))
            table.setItem(r, 1, QTableWidgetItem(key))
            table.setItem(r, 2, QTableWidgetItem(type_str))
            table.setItem(r, 3, QTableWidgetItem(default_str))
        main_layout.addWidget(table)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add Row")
        remove_btn = QPushButton("Remove Row")
        btn_row.addWidget(add_btn)
        btn_row.addWidget(remove_btn)
        btn_row.addStretch()
        main_layout.addLayout(btn_row)

        def _add_row() -> None:
            r = table.rowCount()
            table.insertRow(r)
            for c in range(4):
                table.setItem(r, c, QTableWidgetItem(""))

        def _remove_row() -> None:
            row = table.currentRow()
            if row >= 0:
                table.removeRow(row)

        add_btn.clicked.connect(_add_row)
        remove_btn.clicked.connect(_remove_row)

        _VALID_TYPES = frozenset(
            {"string", "integer", "number", "boolean", "array", "object", "null"}
        )

        validation_label = QLabel("")
        validation_label.setWordWrap(True)
        main_layout.addWidget(validation_label)

        def _collect_schema() -> dict[str, dict[str, dict[str, object]]]:
            result: dict[str, dict[str, dict[str, object]]] = {}
            for r in range(table.rowCount()):
                ns_item = table.item(r, 0)
                key_item = table.item(r, 1)
                type_item = table.item(r, 2)
                default_item = table.item(r, 3)
                ns = ns_item.text().strip() if ns_item else ""
                key = key_item.text().strip() if key_item else ""
                type_str = type_item.text().strip() if type_item else ""
                default_str = default_item.text().strip() if default_item else ""
                if not ns or not key or not type_str:
                    continue
                if ns not in result:
                    result[ns] = {}
                entry: dict[str, object] = {"type": type_str}
                if default_str:
                    entry["default"] = default_str
                result[ns][key] = entry
            return result

        def _validate_schema() -> list[str]:
            errors: list[str] = []
            for r in range(table.rowCount()):
                ns_item = table.item(r, 0)
                key_item = table.item(r, 1)
                type_item = table.item(r, 2)
                ns = ns_item.text().strip() if ns_item else ""
                key = key_item.text().strip() if key_item else ""
                type_str = type_item.text().strip() if type_item else ""
                if not ns and not key and not type_str:
                    continue
                if not ns:
                    errors.append(f"Row {r + 1}: Namespace is required.")
                if not key:
                    errors.append(f"Row {r + 1}: Key is required.")
                if type_str and type_str not in _VALID_TYPES:
                    errors.append(
                        f"Row {r + 1}: '{type_str}' is not a valid JSON Schema type. "
                        f"Valid types: {', '.join(sorted(_VALID_TYPES))}"
                    )
            return errors

        def _on_validate() -> None:
            errs = _validate_schema()
            if errs:
                validation_label.setText("Validation errors:\n" + "\n".join(errs))
            else:
                validation_label.setText("Schema is valid.")

        validate_btn = QPushButton("Validate")
        validate_btn.clicked.connect(_on_validate)
        btn_row.addWidget(validate_btn)

        dialog_btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._add_help_button(dialog_btns, "shared_store")
        dialog_btns.accepted.connect(dlg.accept)
        dialog_btns.rejected.connect(dlg.reject)
        main_layout.addWidget(dialog_btns)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        errs = _validate_schema()
        if errs:
            QMessageBox.warning(self, "Validation Errors", "\n".join(errs))
            return

        schema = _collect_schema()
        try:
            path.write_text(
                yaml.dump(schema, default_flow_style=False, allow_unicode=True),
                encoding="utf-8",
            )
            self.statusBar().showMessage(f"Shared store schema saved: {path.name}")
        except Exception as exc:
            QMessageBox.critical(self, "Save Failed", str(exc))


def run(argv: Sequence[str] | None = None) -> int:
    if QApplication is None:
        raise RuntimeError("PySide6 is not available. Install project dependencies first.")
    app = QApplication(list(argv or []))
    app.setApplicationName("PocketFlow Creator")
    app.setOrganizationName("Monotoba")

    # Install locale-specific translator before building the main window
    _settings = QSettings("Monotoba", "PocketFlowCreator")
    locale_code = str(_settings.value("ui/locale", "system"))
    _trans_dir = str(Path(__file__).parent.parent / "translations")
    _locale = QLocale.system() if locale_code == "system" else QLocale(locale_code)
    _translator = QTranslator(app)
    if _translator.load(_locale, "pocketflow_creator", "_", _trans_dir):
        app.installTranslator(_translator)

    window = MainWindow()
    window.show()
    return app.exec()

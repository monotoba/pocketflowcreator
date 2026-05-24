from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import yaml

try:
    from PySide6.QtCore import QSettings, Qt, QUrl
    from PySide6.QtGui import QDesktopServices, QUndoStack
    from PySide6.QtWidgets import (
        QApplication,
        QDialog,
        QDialogButtonBox,
        QDockWidget,
        QFileDialog,
        QFormLayout,
        QGroupBox,
        QInputDialog,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMenu,
        QMessageBox,
        QPlainTextEdit,
        QSplitter,
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

from pocketflow_creator.generation.python_generator import PythonGenerator
from pocketflow_creator.graph_io import GraphLoader, GraphSaver
from pocketflow_creator.model.graph_model import EdgeModel, GraphModel, NodeModel
from pocketflow_creator.model.project import ProjectModel
from pocketflow_creator.project_io import ProjectLoader, ProjectSaver
from pocketflow_creator.validation.graph_validator import GraphValidator

_MAX_RECENT = 5
_VERSION = "0.1.0"
_EDITOR_TABS: frozenset[str] = frozenset({"Python", "Markdown", "YAML"})
_ROLE_PATH = Qt.ItemDataRole.UserRole  # type: ignore[attr-defined]
_ROLE_KIND = Qt.ItemDataRole(Qt.ItemDataRole.UserRole.value + 1)  # type: ignore[attr-defined]


class MainWindow(QMainWindow):
    """RAD-style main window for PocketFlow Creator."""

    def __init__(self) -> None:
        super().__init__()
        self._project: ProjectModel | None = None
        self._graphs: dict[str, GraphModel] = {}
        self._bottom_editors: dict[str, QPlainTextEdit] = {}
        self._bottom_tab_paths: dict[str, Path | None] = {}
        self._active_highlighters: dict[str, object] = {}
        self._undo_stack = QUndoStack(self)
        self._recent: list[Path] = []
        self._current_node: NodeModel | None = None
        self._current_node_item: NodeItem | None = None
        self._current_edge: EdgeModel | None = None
        # Assigned by their respective _build_* methods:
        self._explorer_tree: QTreeWidget
        self._bottom_tab_widget: QTabWidget
        self._markdown_preview: QTextBrowser
        self._recent_menu: QMenu
        self._inspector: QTreeWidget
        self._graph_view: GraphView
        self._graph_scene = GraphScene()
        self.setWindowTitle("PocketFlow Creator")
        self.resize(1400, 900)
        self._build_menu_bar()
        self._build_central_area()
        self._build_docks()
        self._graph_scene.node_item_selected.connect(self._on_node_item_selected)
        self._graph_scene.edge_item_selected.connect(self._on_edge_item_selected)
        self._graph_scene.selection_cleared.connect(self._on_selection_cleared)
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
        self.statusBar().showMessage("Ready")

    # ------------------------------------------------------------------ menus

    def _build_menu_bar(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        file_menu.addAction("New Project...", self._on_new_project)
        file_menu.addAction("New From Template...")
        file_menu.addAction("Open Project...", self._on_open_project)
        file_menu.addSeparator()
        self._recent_menu = file_menu.addMenu("Recent Projects")
        file_menu.addSeparator()
        file_menu.addAction("Save", self._on_save)
        file_menu.addAction("Save All", self._on_save_all)
        file_menu.addSeparator()
        file_menu.addAction("Export PocketFlow Project...")
        file_menu.addAction("Project Settings...", self._on_project_settings)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)

        edit_menu = self.menuBar().addMenu("Edit")
        undo_act = edit_menu.addAction("Undo", self._undo_stack.undo)
        undo_act.setShortcut("Ctrl+Z")
        redo_act = edit_menu.addAction("Redo", self._undo_stack.redo)
        redo_act.setShortcut("Ctrl+Y")
        edit_menu.addSeparator()
        for name in ["Cut", "Copy", "Paste", "Duplicate", "Delete", "Find..."]:
            edit_menu.addAction(name)

        view_menu = self.menuBar().addMenu("View")
        for name in ["Project Explorer", "Component Palette", "Object Inspector"]:
            view_menu.addAction(name)
        view_menu.addAction("Zoom to Fit", self._on_zoom_to_fit)

        project_menu = self.menuBar().addMenu("Project")
        project_menu.addAction("Validate Project", self._on_validate_project)
        project_menu.addAction("Generate Code", self._on_generate_code)
        project_menu.addAction("Open Project Folder", self._on_open_project_folder)
        project_menu.addAction("Provider Profiles...")

        for menu_name, actions in [
            (
                "Flow",
                ["New Flow...", "New Subflow...", "Set Start Node", "Validate Active Flow"],
            ),
            (
                "Node",
                ["New Custom Node Type...", "Generate Node Skeleton", "Validate Selected Node"],
            ),
            (
                "Run",
                ["Run Project", "Run Active Flow", "Debug Active Flow", "Run Tests", "Stop"],
            ),
        ]:
            m = self.menuBar().addMenu(menu_name)
            for action in actions:
                m.addAction(action)

        tools_menu = self.menuBar().addMenu("Tools")
        tools_menu.addAction("Provider Manager...", self._on_provider_manager)
        tools_menu.addAction("Tool Registry...", self._on_tool_registry)
        tools_menu.addAction("Shared Store Inspector...", self._on_shared_store_inspector)
        tools_menu.addAction("Options...")

        window_menu = self.menuBar().addMenu("Window")
        for name in ["Reset Layout", "Next Tab", "Previous Tab"]:
            window_menu.addAction(name)

        help_menu = self.menuBar().addMenu("Help")
        help_menu.addAction("PocketFlow Creator Help")
        help_menu.addAction("PocketFlow Quick Reference")
        help_menu.addAction("About PocketFlow Creator", self._on_about)

    # --------------------------------------------------------------- layout

    def _build_central_area(self) -> None:
        self._graph_view = GraphView(self._graph_scene)
        self._graph_view.setStyleSheet("background: #1a1a1a;")
        self.setCentralWidget(self._graph_view)

    def _build_docks(self) -> None:
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._build_project_explorer())
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._build_component_palette())
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._build_object_inspector())
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self._build_bottom_dock())

    def _build_project_explorer(self) -> QDockWidget:
        dock = QDockWidget("Project Explorer", self)
        self._explorer_tree = QTreeWidget()
        self._explorer_tree.setHeaderHidden(True)
        dock.setWidget(self._explorer_tree)
        return dock

    def _build_component_palette(self) -> QDockWidget:
        dock = QDockWidget("Component Palette", self)
        dock.setWidget(PaletteWidget())
        return dock

    def _build_object_inspector(self) -> QDockWidget:
        dock = QDockWidget("Object Inspector", self)
        self._inspector = QTreeWidget()
        self._inspector.setHeaderLabels(["Property", "Value"])
        self._inspector.setAlternatingRowColors(True)
        self._inspector.header().setStretchLastSection(True)
        dock.setWidget(self._inspector)
        return dock

    def _build_bottom_dock(self) -> QDockWidget:
        dock = QDockWidget("Output", self)
        self._bottom_tab_widget = QTabWidget()
        plain_tabs = [
            ("Problems", "No validation has been run."),
            ("Run Log", "No active run."),
            ("Shared Store", "{}"),
            ("Prompt Preview", "Select an LLM node to preview its prompt."),
            ("Generated Code", "Generated code appears here."),
            ("Python", "Open a Python file to edit custom code."),
            ("YAML", "Open metadata to edit YAML."),
            ("Test Results", "Tests have not been run."),
        ]
        for name, text in plain_tabs:
            editor = QPlainTextEdit()
            editor.setPlainText(text)
            self._bottom_tab_widget.addTab(editor, name)
            self._bottom_editors[name] = editor
            self._bottom_tab_paths[name] = None

        # Markdown tab: editor on left, live HTML preview on right
        md_splitter = QSplitter(Qt.Orientation.Horizontal)
        md_editor = QPlainTextEdit()
        md_editor.setPlainText("Open a prompt file to edit Markdown.")
        self._markdown_preview = QTextBrowser()
        self._markdown_preview.setPlainText("Preview appears here.")
        md_splitter.addWidget(md_editor)
        md_splitter.addWidget(self._markdown_preview)
        md_splitter.setSizes([1, 1])
        self._bottom_tab_widget.addTab(md_splitter, "Markdown")
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
                self._graph_scene.load_graph(next(iter(self._graphs.values())))
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

    def _on_about(self) -> None:
        QMessageBox.about(
            self,
            "About PocketFlow Creator",
            f"PocketFlow Creator v{_VERSION}\n\n"
            "RAD visual designer for PocketFlow LLM workflows.",
        )

    # ---------------------------------------------- canvas signal handlers

    def _on_node_item_selected(self, item: object) -> None:
        if not isinstance(item, NodeItem):
            return
        self._current_node_item = item
        self._current_node = item.node
        self._populate_inspector_for_node(item.node)

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

    def _on_inspector_item_changed(self, item: QTreeWidgetItem, col: int) -> None:
        if col != 1 or item.text(0) != "Title":
            return
        if self._current_node is None or self._current_node_item is None:
            return
        self._current_node.title = item.text(1)
        self._current_node_item.update()

    def _populate_inspector_for_node(self, node: NodeModel) -> None:
        self._inspector.blockSignals(True)
        self._inspector.clear()
        rows: list[tuple[str, str, bool]] = [
            ("ID", node.id, False),
            ("Type", node.type_id, False),
            ("Title", node.title, True),
            ("Position X", str(node.position.get("x", 0.0)), False),
            ("Position Y", str(node.position.get("y", 0.0)), False),
            ("Actions", ", ".join(node.actions), False),
            ("Reads", ", ".join(node.reads), False),
            ("Writes", ", ".join(node.writes), False),
        ]
        for label, value, editable in rows:
            row = QTreeWidgetItem([label, value])
            if editable:
                row.setFlags(row.flags() | Qt.ItemFlag.ItemIsEditable)
            self._inspector.addTopLevelItem(row)
        self._inspector.blockSignals(False)

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
        try:
            import markdown as _md

            html = _md.markdown(text)
        except ImportError:
            html = f"<pre>{text}</pre>"
        self._markdown_preview.setHtml(html)

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
        dlg = QDialog(self)
        dlg.setWindowTitle("Tool Registry")
        layout = QVBoxLayout(dlg)
        layout.addWidget(
            QLabel(
                "No tools registered.\n\n"
                "Tools are Python functions decorated with @tool\n"
                "and discovered from the project's tools/ directory."
            )
        )
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(dlg.accept)
        layout.addWidget(buttons)
        dlg.exec()

    def _on_shared_store_inspector(self) -> None:
        self._switch_bottom_tab("Shared Store")
        self.statusBar().showMessage("Shared Store Inspector — populated during run.")

    def _open_shared_store_designer(self, path: Path) -> None:
        self._open_file_in_editor(path)


def run(argv: Sequence[str] | None = None) -> int:
    if QApplication is None:
        raise RuntimeError("PySide6 is not available. Install project dependencies first.")
    app = QApplication(list(argv or []))
    window = MainWindow()
    window.show()
    return app.exec()

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

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
        QInputDialog,
        QLabel,
        QLineEdit,
        QListWidget,
        QMainWindow,
        QMenu,
        QMessageBox,
        QPlainTextEdit,
        QTabWidget,
        QTreeWidget,
        QTreeWidgetItem,
    )
except Exception:  # pragma: no cover - permits import in non-GUI test environments
    QApplication = None  # type: ignore[assignment,misc]

from pocketflow_creator.generation.python_generator import PythonGenerator
from pocketflow_creator.graph_io import GraphLoader, GraphSaver
from pocketflow_creator.model.graph_model import GraphModel
from pocketflow_creator.model.project import ProjectModel
from pocketflow_creator.project_io import ProjectLoader, ProjectSaver
from pocketflow_creator.validation.graph_validator import GraphValidator

_MAX_RECENT = 5
_VERSION = "0.1.0"


class MainWindow(QMainWindow):
    """RAD-style main window for PocketFlow Creator."""

    def __init__(self) -> None:
        super().__init__()
        self._project: ProjectModel | None = None
        self._graphs: dict[str, GraphModel] = {}
        self._bottom_editors: dict[str, QPlainTextEdit] = {}
        self._undo_stack = QUndoStack(self)
        self._recent: list[Path] = []
        # Declared here; assigned by their respective _build_* methods below:
        self._explorer_tree: QTreeWidget
        self._bottom_tab_widget: QTabWidget
        self._recent_menu: QMenu
        self.setWindowTitle("PocketFlow Creator")
        self.resize(1400, 900)
        self._build_menu_bar()
        self._build_central_area()
        self._build_docks()
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
        for name in ["Project Explorer", "Component Palette", "Object Inspector", "Zoom to Fit"]:
            view_menu.addAction(name)

        project_menu = self.menuBar().addMenu("Project")
        project_menu.addAction("Validate Project", self._on_validate_project)
        project_menu.addAction("Generate Code", self._on_generate_code)
        project_menu.addAction("Open Project Folder", self._on_open_project_folder)
        project_menu.addAction("Provider Profiles...")

        for menu_name, actions in {
            "Flow": ["New Flow...", "New Subflow...", "Set Start Node", "Validate Active Flow"],
            "Node": [
                "New Custom Node Type...", "Generate Node Skeleton", "Validate Selected Node",
            ],
            "Run": ["Run Project", "Run Active Flow", "Debug Active Flow", "Run Tests", "Stop"],
            "Tools": [
                "Provider Manager...", "Tool Registry...",
                "Shared Store Inspector...", "Options...",
            ],
            "Window": ["Reset Layout", "Next Tab", "Previous Tab"],
        }.items():
            m = self.menuBar().addMenu(menu_name)
            for action in actions:
                m.addAction(action)

        help_menu = self.menuBar().addMenu("Help")
        help_menu.addAction("PocketFlow Creator Help")
        help_menu.addAction("PocketFlow Quick Reference")
        help_menu.addAction("About PocketFlow Creator", self._on_about)

    # --------------------------------------------------------------- layout

    def _build_central_area(self) -> None:
        placeholder = QLabel(
            "Graph Designer\n\n"
            "Drag node types from the Component Palette, edit them in the Object Inspector,\n"
            "then wire action ports together here."
        )
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("font-size: 18px; border: 1px solid #888; background: #202020;")
        self.setCentralWidget(placeholder)

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
        items = QListWidget()
        for name in [
            "Start Node", "Stop Node", "Basic Node", "Router Node",
            "LLM Prompt Node", "JSON LLM Node", "Classifier Node",
            "Python Tool Node", "File Reader Node", "Human Review Node",
            "Batch Node", "Subflow Node",
        ]:
            items.addItem(name)
        dock.setWidget(items)
        return dock

    def _build_object_inspector(self) -> QDockWidget:
        dock = QDockWidget("Object Inspector", self)
        text = QPlainTextEdit()
        text.setPlainText(
            "Object: (none)\nType: —\n\n"
            "Select a node or edge on the canvas to inspect it."
        )
        dock.setWidget(text)
        return dock

    def _build_bottom_dock(self) -> QDockWidget:
        dock = QDockWidget("Output", self)
        self._bottom_tab_widget = QTabWidget()
        for name, text in [
            ("Problems", "No validation has been run."),
            ("Run Log", "No active run."),
            ("Shared Store", "{}"),
            ("Prompt Preview", "Select an LLM node to preview its prompt."),
            ("Generated Code", "Generated code appears here."),
            ("Python", "Open a Python file to edit custom code."),
            ("Markdown", "Open a prompt file to edit Markdown."),
            ("YAML", "Open metadata to edit YAML."),
            ("Test Results", "Tests have not been run."),
        ]:
            editor = QPlainTextEdit()
            editor.setPlainText(text)
            self._bottom_tab_widget.addTab(editor, name)
            self._bottom_editors[name] = editor
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
            for item in items:
                node.addChild(QTreeWidgetItem([Path(item).name]))
            return node

        root_item.addChild(_cat("Graphs", self._project.graphs))
        root_item.addChild(_cat("Prompts", self._project.prompts))
        root_item.addChild(_cat("Node Types", self._project.node_types))
        root_item.addChild(QTreeWidgetItem(["Tools"]))
        if self._project.shared_store_schema:
            root_item.addChild(QTreeWidgetItem(["Shared Store"]))
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
            self.statusBar().showMessage("Saved.")
        except Exception as exc:
            QMessageBox.critical(self, "Save Failed", str(exc))

    def _on_save_all(self) -> None:
        if self._project is None:
            self.statusBar().showMessage("No project open.")
            return
        try:
            ProjectSaver().save(self._project)
            saver = GraphSaver()
            for rel, graph in self._graphs.items():
                saver.save(graph, self._project.root / rel)
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
        for rel, graph in self._graphs.items():
            for issue in validator.validate(graph):
                lines.append(
                    f"[{issue.severity.upper()}] {rel}:{issue.object_id}  {issue.message}"
                )
        text = "\n".join(lines) if lines else "No issues found."
        self._bottom_editors["Problems"].setPlainText(text)
        self._switch_bottom_tab("Problems")
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


def run(argv: Sequence[str] | None = None) -> int:
    if QApplication is None:
        raise RuntimeError("PySide6 is not available. Install project dependencies first.")
    app = QApplication(list(argv or []))
    window = MainWindow()
    window.show()
    return app.exec()

from __future__ import annotations

from collections.abc import Sequence

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QApplication,
        QDockWidget,
        QLabel,
        QListWidget,
        QMainWindow,
        QPlainTextEdit,
        QTabWidget,
        QTreeWidget,
        QTreeWidgetItem,
    )
except Exception:  # pragma: no cover - permits import in non-GUI test environments
    QApplication = None  # type: ignore[assignment,misc]


class MainWindow(QMainWindow):
    """Initial RAD-style shell for PocketFlow Creator.

    The first implementation is intentionally light. It establishes the durable
    screen regions: project explorer, component palette, graph designer, object
    inspector, and bottom tool/editor tabs.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PocketFlow Creator")
        self.resize(1400, 900)
        self._build_menu_bar()
        self._build_central_area()
        self._build_docks()
        self.statusBar().showMessage("Ready")

    def _build_menu_bar(self) -> None:
        menu_specs = {
            "File": [
                "New Project...",
                "New From Template...",
                "Open Project...",
                "Save",
                "Save All",
                "Export PocketFlow Project...",
                "Project Settings...",
                "Exit",
            ],
            "Edit": ["Undo", "Redo", "Cut", "Copy", "Paste", "Duplicate", "Delete", "Find..."],
            "View": ["Project Explorer", "Component Palette", "Object Inspector", "Zoom to Fit"],
            "Project": [
                "Validate Project", "Generate Code", "Open Project Folder", "Provider Profiles...",
            ],
            "Flow": ["New Flow...", "New Subflow...", "Set Start Node", "Validate Active Flow"],
            "Node": ["New Custom Node Type...", "Generate Node Skeleton", "Validate Selected Node"],
            "Run": ["Run Project", "Run Active Flow", "Debug Active Flow", "Run Tests", "Stop"],
            "Tools": [
                "Provider Manager...", "Tool Registry...",
                "Shared Store Inspector...", "Options...",
            ],
            "Window": ["Reset Layout", "Next Tab", "Previous Tab"],
            "Help": [
                "PocketFlow Creator Help", "PocketFlow Quick Reference", "About PocketFlow Creator",
            ],
        }
        for menu_name, actions in menu_specs.items():
            menu = self.menuBar().addMenu(menu_name)
            for action in actions:
                menu.addAction(action)

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
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._project_explorer())
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._component_palette())
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._object_inspector())
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self._bottom_tabs())

    def _project_explorer(self) -> QDockWidget:
        dock = QDockWidget("Project Explorer", self)
        tree = QTreeWidget()
        tree.setHeaderHidden(True)
        root = QTreeWidgetItem(["DocumentSummarizer"])
        for name in [
            "Flows", "Graphs", "Prompts", "Node Types", "Tools",
            "Shared Store", "Source", "Tests", "Exports",
        ]:
            root.addChild(QTreeWidgetItem([name]))
        tree.addTopLevelItem(root)
        root.setExpanded(True)
        dock.setWidget(tree)
        return dock

    def _component_palette(self) -> QDockWidget:
        dock = QDockWidget("Component Palette", self)
        items = QListWidget()
        for name in [
            "Start Node",
            "Stop Node",
            "Basic Node",
            "Router Node",
            "LLM Prompt Node",
            "JSON LLM Node",
            "Classifier Node",
            "Python Tool Node",
            "File Reader Node",
            "Human Review Node",
            "Batch Node",
            "Subflow Node",
        ]:
            items.addItem(name)
        dock.setWidget(items)
        return dock

    def _object_inspector(self) -> QDockWidget:
        dock = QDockWidget("Object Inspector", self)
        text = QPlainTextEdit()
        text.setPlainText(
            "Object: MainFlow\n"
            "Type: Flow\n\n"
            "[General]\n"
            "Name: MainFlow\n"
            "Start Node: <unset>\n\n"
            "[Execution]\n"
            "Flow Type: Sync\n"
            "Max Steps: 100\n"
        )
        dock.setWidget(text)
        return dock

    def _bottom_tabs(self) -> QDockWidget:
        dock = QDockWidget("Output", self)
        tabs = QTabWidget()
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
            tabs.addTab(editor, name)
        dock.setWidget(tabs)
        return dock


def run(argv: Sequence[str] | None = None) -> int:
    if QApplication is None:
        raise RuntimeError("PySide6 is not available. Install project dependencies first.")
    app = QApplication(list(argv or []))
    window = MainWindow()
    window.show()
    return app.exec()

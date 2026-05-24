"""
Capture UI screenshots for help/img/ using the offscreen Qt platform.
Run with: QT_QPA_PLATFORM=offscreen python scripts/capture_screenshots.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Ensure src is on the path
repo = Path(__file__).parent.parent
sys.path.insert(0, str(repo / "src"))

from PySide6.QtWidgets import QApplication  # noqa: E402

app = QApplication.instance() or QApplication(sys.argv)

out_dir = repo / "src" / "pocketflow_creator" / "help" / "img"
out_dir.mkdir(parents=True, exist_ok=True)

# ── Main Window ─────────────────────────────────────────────────────────────
from pocketflow_creator.app.main import MainWindow  # noqa: E402

win = MainWindow()
win.resize(1280, 800)
win.show()
app.processEvents()
pixmap = win.grab()
pixmap.save(str(out_dir / "main_window.png"))
print(f"  main_window.png  ({pixmap.width()}x{pixmap.height()})")

# ── Canvas close-up — load example project ──────────────────────────────────
from pathlib import Path as _Path  # noqa: E402

example = repo / "examples" / "document_summarizer" / "document_summarizer.pfcproj.yaml"
if example.exists():
    from pocketflow_creator.project_io import ProjectLoader  # noqa: E402

    proj = ProjectLoader.load(example)
    win._project = proj  # type: ignore[attr-defined]
    if proj.graphs:
        from pocketflow_creator.graph_io import GraphLoader  # noqa: E402

        gpath = proj.root / proj.graphs[0]
        graph = GraphLoader.load(gpath)
        win._graphs[proj.graphs[0]] = graph  # type: ignore[attr-defined]
        win._canvas.load_graph(graph)  # type: ignore[attr-defined]
        app.processEvents()
        canvas_pix = win._canvas.grab()  # type: ignore[attr-defined]
        canvas_pix.save(str(out_dir / "canvas.png"))
        print(f"  canvas.png  ({canvas_pix.width()}x{canvas_pix.height()})")

# ── Help Browser ─────────────────────────────────────────────────────────────
from pocketflow_creator.app.help_browser import HelpBrowser  # noqa: E402

browser = HelpBrowser("index.md", win)
browser.resize(820, 600)
browser.show()
app.processEvents()
help_pix = browser.grab()
help_pix.save(str(out_dir / "help_browser.png"))
print(f"  help_browser.png  ({help_pix.width()}x{help_pix.height()})")
browser.hide()

print(f"\nScreenshots written to {out_dir}")

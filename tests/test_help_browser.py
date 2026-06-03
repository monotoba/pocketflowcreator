"""Smoke tests for the HelpBrowser — run offscreen via QApplication."""

import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication

    _QT = True
except ImportError:  # pragma: no cover
    _QT = False

pytestmark = pytest.mark.skipif(not _QT, reason="PySide6 not available")

_HELP_ROOT = Path(__file__).parent.parent / "src" / "pocketflow_creator" / "help"


@pytest.fixture(scope="module")
def app():
    existing = QApplication.instance()
    if existing:
        yield existing
        return
    a = QApplication(sys.argv[:1])
    yield a


def test_help_root_exists():
    assert _HELP_ROOT.is_dir(), "help/ directory missing"


def test_index_md_exists():
    assert (_HELP_ROOT / "index.md").exists()


def test_all_context_files_exist():
    expected = [
        "canvas.md",
        "inspector.md",
        "palette.md",
        "explorer.md",
        "options.md",
        "provider_manager.md",
        "shared_store.md",
        "node_type_wizard.md",
        "code_editor.md",
        "run_log.md",
        "validation.md",
    ]
    context_dir = _HELP_ROOT / "context"
    for name in expected:
        assert (context_dir / name).exists(), f"context/{name} missing"


def test_all_tutorial_files_exist():
    expected = [
        "index.md",
        "part1_fundamentals.md",
        "part2_patterns.md",
        "part3_advanced.md",
        "part4_exercises.md",
    ]
    tut_dir = _HELP_ROOT / "tutorials"
    for name in expected:
        assert (tut_dir / name).exists(), f"tutorials/{name} missing"


def test_help_browser_loads_index(app):
    from pocketflow_creator.app.help_browser import HelpBrowser

    browser = HelpBrowser("index.md")
    text = browser._browser.toPlainText()
    assert len(text) > 50, "index.md rendered no content"
    browser.close()


def test_help_browser_navigate_to_context(app):
    from pocketflow_creator.app.help_browser import HelpBrowser

    browser = HelpBrowser("context/canvas.md")
    text = browser._browser.toPlainText()
    assert "canvas" in text.lower()
    browser.close()


def test_help_browser_missing_page_shows_error(app):
    from pocketflow_creator.app.help_browser import HelpBrowser

    browser = HelpBrowser("does_not_exist.md")
    html = browser._browser.toHtml()
    assert "not found" in html.lower() or "does_not_exist" in html.lower()
    browser.close()


def test_help_browser_back_forward(app):
    from pocketflow_creator.app.help_browser import HelpBrowser

    browser = HelpBrowser("index.md")
    browser._navigate("context/canvas.md")
    assert browser._history_pos == 1
    browser._go_back()
    assert browser._history_pos == 0
    browser._go_forward()
    assert browser._history_pos == 1
    browser.close()

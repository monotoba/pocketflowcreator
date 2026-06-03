from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication, QPlainTextEdit

from pocketflow_creator.app.editors import PythonHighlighter, YamlHighlighter

pytestmark = pytest.mark.gui

_app = QApplication.instance() or QApplication([])


def _make_editor(text: str) -> QPlainTextEdit:
    editor = QPlainTextEdit()
    editor.setPlainText(text)
    return editor


def test_python_highlighter_attaches() -> None:
    editor = _make_editor("def foo(): pass")
    h = PythonHighlighter(editor.document())
    assert h.document() is editor.document()


def test_python_highlighter_detach() -> None:
    editor = _make_editor("x = 1")
    h = PythonHighlighter(editor.document())
    h.setDocument(None)
    assert h.document() is None


def test_yaml_highlighter_attaches() -> None:
    editor = _make_editor("key: value\n---\n# comment")
    h = YamlHighlighter(editor.document())
    assert h.document() is editor.document()


def test_python_highlighter_does_not_crash_on_keywords() -> None:
    code = (
        "def greet(name: str) -> None:\n"
        "    if name:\n"
        "        print(f'Hello {name}')\n"
        "    return None\n"
        "class Foo:\n"
        "    pass\n"
    )
    editor = _make_editor(code)
    h = PythonHighlighter(editor.document())
    h.rehighlight()


def test_yaml_highlighter_does_not_crash_on_nested_yaml() -> None:
    content = (
        "---\n"
        "document:\n"
        "  path:\n"
        "    type: string\n"
        "  text:\n"
        "    type: string\n"
        "    default: 'hello'\n"
        "# end\n"
    )
    editor = _make_editor(content)
    h = YamlHighlighter(editor.document())
    h.rehighlight()

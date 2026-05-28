from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from PySide6.QtCore import QRegularExpression
    from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat
else:
    try:
        from PySide6.QtCore import QRegularExpression
        from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat
    except ImportError:  # pragma: no cover
        # QSyntaxHighlighter is used as a base class at import time; the rest
        # are only used inside method bodies never called without PySide6.
        QSyntaxHighlighter = object


class _RulesHighlighter(QSyntaxHighlighter):
    """Base syntax highlighter that dispatches a list of (pattern, format) rules.

    Subclasses implement ``_build_rules()`` to return the rule list.  Rules are
    stored as a ``ClassVar`` and built once on the first instantiation of each
    subclass — not rebuilt for every document that uses the same highlighter type.
    """

    # Per-subclass cache; None means "not yet built for this class".
    _rules: ClassVar[list[tuple[Any, Any]] | None] = None

    def __init__(self, document: Any) -> None:
        super().__init__(document)
        # Build rules once per concrete class, not once per instance.
        if type(self)._rules is None:
            type(self)._rules = self._build_rules()

    def _build_rules(self) -> list[tuple[Any, Any]]:
        """Return a list of (QRegularExpression, QTextCharFormat) pairs."""
        raise NotImplementedError  # pragma: no cover

    def highlightBlock(self, text: str) -> None:
        for pattern, fmt in (type(self)._rules or []):
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)


class PythonHighlighter(_RulesHighlighter):
    _KEYWORDS = (
        "False None True and as assert async await break class continue def del elif "
        "else except finally for from global if import in is lambda nonlocal not or "
        "pass raise return try while with yield"
    ).split()

    def _build_rules(self) -> list[tuple[Any, Any]]:
        kw_fmt = QTextCharFormat()
        kw_fmt.setForeground(QColor("#cc7832"))
        kw_fmt.setFontWeight(QFont.Weight.Bold)

        str_fmt = QTextCharFormat()
        str_fmt.setForeground(QColor("#6a8759"))

        comment_fmt = QTextCharFormat()
        comment_fmt.setForeground(QColor("#808080"))
        comment_fmt.setFontItalic(True)

        def_fmt = QTextCharFormat()
        def_fmt.setForeground(QColor("#ffc66d"))

        kw_pattern = r"\b(?:" + "|".join(self._KEYWORDS) + r")\b"
        return [
            (QRegularExpression(kw_pattern), kw_fmt),
            (QRegularExpression(r"\b(?:def|class)\b\s+\w+"), def_fmt),
            (QRegularExpression(r"\"[^\"]*\"|'[^']*'"), str_fmt),
            (QRegularExpression(r"#[^\n]*"), comment_fmt),
        ]


class YamlHighlighter(_RulesHighlighter):
    def _build_rules(self) -> list[tuple[Any, Any]]:
        key_fmt = QTextCharFormat()
        key_fmt.setForeground(QColor("#9876aa"))
        key_fmt.setFontWeight(QFont.Weight.Bold)

        str_fmt = QTextCharFormat()
        str_fmt.setForeground(QColor("#6a8759"))

        comment_fmt = QTextCharFormat()
        comment_fmt.setForeground(QColor("#808080"))
        comment_fmt.setFontItalic(True)

        sep_fmt = QTextCharFormat()
        sep_fmt.setForeground(QColor("#cc7832"))
        sep_fmt.setFontWeight(QFont.Weight.Bold)

        return [
            (QRegularExpression(r"^---"), sep_fmt),
            (QRegularExpression(r"^[ \t]*[^:#\n ][^:#\n]*(?=\s*:)"), key_fmt),
            (QRegularExpression(r"\"[^\"]*\"|'[^']*'"), str_fmt),
            (QRegularExpression(r"#[^\n]*"), comment_fmt),
        ]

"""Help browser — renders Markdown help files in a navigable QDialog."""

from __future__ import annotations

from pathlib import Path

try:
    from PySide6.QtCore import QUrl
    from PySide6.QtWidgets import (
        QDialog,
        QDialogButtonBox,
        QHBoxLayout,
        QPushButton,
        QTextBrowser,
        QVBoxLayout,
    )

except ImportError:  # pragma: no cover
    pass


_HELP_ROOT = Path(__file__).parent.parent / "help"


class HelpBrowser(QDialog):  # type: ignore[misc]
    """A navigable Markdown help viewer.

    Parameters
    ----------
    start_page:
        Path relative to the help root (e.g. "index.md" or "context/canvas.md").
    parent:
        Qt parent widget.
    """

    def __init__(self, start_page: str = "index.md", parent: object = None) -> None:
        super().__init__(parent)  # type: ignore[arg-type]
        self.setWindowTitle("PocketFlow Creator Help")
        self.resize(820, 620)

        self._help_root = _HELP_ROOT
        self._history: list[Path] = []
        self._history_pos: int = -1

        # ── navigation bar ──────────────────────────────────────────────────
        nav = QHBoxLayout()
        self._btn_back = QPushButton("◀")
        self._btn_forward = QPushButton("▶")
        self._btn_home = QPushButton("⌂ Home")
        self._btn_back.setFixedWidth(32)
        self._btn_forward.setFixedWidth(32)
        self._btn_back.clicked.connect(self._go_back)
        self._btn_forward.clicked.connect(self._go_forward)
        self._btn_home.clicked.connect(lambda: self._navigate("index.md"))
        nav.addWidget(self._btn_back)
        nav.addWidget(self._btn_forward)
        nav.addWidget(self._btn_home)
        nav.addStretch()

        # ── text browser ────────────────────────────────────────────────────
        self._browser = QTextBrowser()
        self._browser.setOpenLinks(False)
        self._browser.anchorClicked.connect(self._on_link_clicked)
        self._browser.setSearchPaths([str(self._help_root)])

        # ── button box ──────────────────────────────────────────────────────
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(self.reject)

        root = QVBoxLayout(self)
        root.addLayout(nav)
        root.addWidget(self._browser)
        root.addWidget(btns)

        self._navigate(start_page)

    # ------------------------------------------------------------------ nav
    def _navigate(self, rel: str, fragment: str = "") -> None:
        """Load a page by path relative to the help root, optionally scrolling to fragment."""
        path = (self._help_root / rel).resolve()
        if not path.exists():
            self._browser.setHtml(f"<h2>Page not found</h2><p><code>{rel}</code></p>")
            return
        text = path.read_text(encoding="utf-8")
        self._browser.setMarkdown(text)
        self._browser.setSearchPaths([str(path.parent), str(self._help_root)])
        if fragment:
            self._browser.scrollToAnchor(fragment)

        # Trim forward history when navigating to a new page
        if self._history_pos < len(self._history) - 1:
            self._history = self._history[: self._history_pos + 1]
        self._history.append(path)
        self._history_pos = len(self._history) - 1
        self._update_nav_buttons()

    def _go_back(self) -> None:
        if self._history_pos > 0:
            self._history_pos -= 1
            self._load_current()

    def _go_forward(self) -> None:
        if self._history_pos < len(self._history) - 1:
            self._history_pos += 1
            self._load_current()

    def _load_current(self) -> None:
        path = self._history[self._history_pos]
        text = path.read_text(encoding="utf-8")
        self._browser.setMarkdown(text)
        self._browser.setSearchPaths([str(path.parent), str(self._help_root)])
        self._update_nav_buttons()

    def _update_nav_buttons(self) -> None:
        self._btn_back.setEnabled(self._history_pos > 0)
        self._btn_forward.setEnabled(self._history_pos < len(self._history) - 1)

    def _on_link_clicked(self, url: QUrl) -> None:
        href = url.toString()
        if href.startswith("http://") or href.startswith("https://"):
            try:
                from PySide6.QtGui import QDesktopServices

                QDesktopServices.openUrl(url)
            except Exception:  # pragma: no cover
                pass
            return
        # Split fragment before resolving the file path
        fragment = ""
        if "#" in href:
            href, fragment = href.split("#", 1)
        # Pure fragment — scroll within the current page
        if not href:
            self._browser.scrollToAnchor(fragment)
            return
        # Internal link: resolve relative to the current page's directory
        if self._history:
            current_dir = self._history[self._history_pos].parent
            target = (current_dir / href).resolve()
            rel = target.relative_to(self._help_root.resolve())
            self._navigate(str(rel), fragment)


def open_help(start_page: str = "index.md", parent: object = None) -> None:
    """Convenience function: show the help browser at start_page."""
    dlg = HelpBrowser(start_page, parent)
    dlg.exec()

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def pytest_configure(config):
    """Skip GUI tests in CI environment."""
    config.addinivalue_line("markers", "gui: mark test as GUI test (skip in CI)")
    if os.getenv("CI"):
        config.option.markexpr = "not gui"

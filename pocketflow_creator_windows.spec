# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for PocketFlow Creator — Windows one-file bundle.
#
# Usage (from a Windows host or Wine environment):
#   pyinstaller pocketflow_creator_windows.spec
#
# Output: dist\pocketflow-creator.exe  (single executable)
#
# Requires PyInstaller 6+ and all runtime deps installed in the active venv.

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

SRC = Path("src")
PKG = SRC / "pocketflow_creator"

# ── data files bundled into the executable ──────────────────────────────────
datas = [
    # Jinja2 templates
    (str(PKG / "templates"), "pocketflow_creator/templates"),
    # Node snippet library
    (str(PKG / "node_snippets.yaml"), "pocketflow_creator"),
    # Project template directories
    (str(PKG / "project_templates"), "pocketflow_creator/project_templates"),
]

datas += collect_data_files("PySide6")

# ── hidden imports ───────────────────────────────────────────────────────────
hiddenimports = (
    collect_submodules("pocketflow_creator")
    + collect_submodules("PySide6")
    + [
        "yaml",
        "jsonschema",
        "markdown",
        "jinja2",
        "jinja2.ext",
    ]
)

# ── analysis ─────────────────────────────────────────────────────────────────
a = Analysis(
    [str(SRC / "pocketflow_creator" / "__main__.py")],
    pathex=[str(SRC)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "test", "unittest"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="pocketflow-creator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

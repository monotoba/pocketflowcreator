#!/usr/bin/env bash
# Extract translatable strings from Python source into .ts files.
# Requires pyside6-lupdate (installed with PySide6).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SRC="$REPO_ROOT/src/pocketflow_creator"
TS_DIR="$SRC/translations"

echo "Updating translation files in $TS_DIR ..."

pyside6-lupdate \
    "$SRC/app/main.py" \
    -ts \
    "$TS_DIR/pocketflow_creator_en.ts" \
    "$TS_DIR/pocketflow_creator_es.ts"

echo "Done. Review the .ts files and fill in any new <translation> elements."

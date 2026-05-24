#!/usr/bin/env bash
# Compile .ts source files into binary .qm files that Qt loads at runtime.
# Requires pyside6-lrelease (installed with PySide6).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

TS_DIR="$REPO_ROOT/src/pocketflow_creator/translations"

echo "Compiling translation files in $TS_DIR ..."

for ts_file in "$TS_DIR"/*.ts; do
    qm_file="${ts_file%.ts}.qm"
    pyside6-lrelease "$ts_file" -qm "$qm_file"
    echo "  compiled: $(basename "$ts_file") -> $(basename "$qm_file")"
done

echo "Done."

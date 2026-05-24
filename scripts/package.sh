#!/usr/bin/env bash
# package.sh — build a self-contained PocketFlow Creator binary with PyInstaller.
#
# Usage:
#   bash scripts/package.sh [linux|windows]
#
# Default target is "linux". The "windows" target cross-compiles using the
# Windows spec file; it still requires a Windows Python environment or Wine.
#
# Prerequisites:
#   pip install pyinstaller
#   All runtime dependencies must be installed in the active virtual environment.
#
# Output:
#   dist/pocketflow-creator        (Linux)
#   dist/pocketflow-creator.exe    (Windows, if cross-compiled)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TARGET="${1:-linux}"

cd "$PROJECT_ROOT"

if ! command -v pyinstaller &>/dev/null; then
    echo "ERROR: pyinstaller not found. Install it with: pip install pyinstaller" >&2
    exit 1
fi

echo "=== PocketFlow Creator packager ==="
echo "Target:  $TARGET"
echo "Root:    $PROJECT_ROOT"
echo ""

case "$TARGET" in
    linux)
        SPEC="pocketflow_creator_linux.spec"
        ;;
    windows)
        SPEC="pocketflow_creator_windows.spec"
        ;;
    *)
        echo "ERROR: unknown target '$TARGET'. Use 'linux' or 'windows'." >&2
        exit 1
        ;;
esac

echo "Running: pyinstaller $SPEC --clean --noconfirm"
pyinstaller "$SPEC" --clean --noconfirm

echo ""
echo "Build complete. Output in: $PROJECT_ROOT/dist/"
ls -lh "$PROJECT_ROOT/dist/" 2>/dev/null || true

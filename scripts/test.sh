#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ ! -d .venv ]; then
  echo "Missing .venv. Run ./scripts/setup-prj.sh first." >&2
  exit 1
fi
. .venv/bin/activate
pytest "$@"

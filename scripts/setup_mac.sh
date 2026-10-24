#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ "$(uname -s)" != Darwin || "$(uname -m)" != arm64 ]]; then
  echo 'Run this on an Apple Silicon Mac in a native arm64 terminal.' >&2
  exit 1
fi
python3 - <<'PY'
import platform, sys
if sys.version_info < (3, 11) or platform.machine() != 'arm64':
    raise SystemExit('Use native Apple Silicon Python 3.11 or newer (not Rosetta Python).')
PY
python3 -m venv .venv-mac
.venv-mac/bin/python -m pip install -r requirements-mac.txt
.venv-mac/bin/python -m pip check
.venv-mac/bin/python -c 'import sys; sys.path.insert(0,"scripts"); from train_mlx import check_mac; check_mac(); print("MLX Metal available")'
.venv-mac/bin/python -m pytest -q

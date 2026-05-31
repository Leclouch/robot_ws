#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${VENV_DIR:-$ROOT_DIR/.venv}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

WITH_SYSTEM_PACKAGES=0
WITH_JETSON_TORCH=0

usage() {
  cat <<'EOF'
Usage: scripts/install_dependencies.sh [options]

Options:
  --system-packages   Install common Ubuntu/Jetson system packages with apt.
  --jetson-torch      Do not pip-install torch; use Jetson's preinstalled/NVIDIA torch.
  -h, --help          Show this help.

Environment:
  VENV_DIR            Virtualenv path. Default: .venv
  PYTHON_BIN          Python executable. Default: python3

Examples:
  scripts/install_dependencies.sh
  scripts/install_dependencies.sh --system-packages --jetson-torch
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --system-packages)
      WITH_SYSTEM_PACKAGES=1
      shift
      ;;
    --jetson-torch)
      WITH_JETSON_TORCH=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 2
      ;;
  esac
done

cd "$ROOT_DIR"

if [[ "$WITH_SYSTEM_PACKAGES" -eq 1 ]]; then
  if ! command -v sudo >/dev/null 2>&1; then
    echo "sudo is required for --system-packages." >&2
    exit 1
  fi

  sudo apt-get update
  sudo apt-get install -y \
    python3 \
    python3-dev \
    python3-pip \
    python3-venv \
    libgl1 \
    libglib2.0-0 \
    v4l-utils
fi

"$PYTHON_BIN" -m venv "$VENV_DIR"
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip setuptools wheel

if [[ "$WITH_JETSON_TORCH" -eq 1 ]]; then
  TMP_REQUIREMENTS="$(mktemp)"
  grep -vE '^(torch|torch==|torch>=|torch<=)' requirements.txt > "$TMP_REQUIREMENTS"
  python -m pip install -r "$TMP_REQUIREMENTS"
  rm -f "$TMP_REQUIREMENTS"
else
  python -m pip install -r requirements.txt
fi

cat <<EOF

Dependencies installed.

Activate the environment with:
  source "$VENV_DIR/bin/activate"

Run the robot stack with:
  python main.py
EOF

#!/usr/bin/env bash
set -euo pipefail

VENV="${VENV:-.venv}"
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Installing music-video pipeline (CUDA) ==="

# --- Create venv ---
if [ ! -d "$VENV" ]; then
    python3 -m venv "$VENV"
fi
source "$VENV/bin/activate"
pip install -U pip uv

# --- Install PyTorch + friends with CUDA 12.8 ---
uv pip install \
    torch==2.10.0+cu128 \
    torchvision==0.25.0+cu128 \
    torchaudio==2.10.0+cu128 \
    --index-url https://download.pytorch.org/whl/cu128

# --- Install llama-cpp-python with CUDA ---
# Build from source with CUDA support
CMAKE_ARGS="-DGGML_CUDA=on" uv pip install \
    --force-reinstall \
    --no-build-isolation \
    "llama-cpp-python==0.3.22"

# --- Install project dependencies (minus torch/llama which are already handled) ---
uv pip install -r "$ROOT_DIR/requirements.txt"
uv pip install qwen-asr

# --- Install ACE-Step as editable ---
uv pip install -e "$ROOT_DIR/ACE-Step-1.5"

echo "=== CUDA install complete ==="
echo "Activate with: source $VENV/bin/activate"

#!/usr/bin/env bash
set -euo pipefail

VENV="${VENV:-.venv}"
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Installing music-video pipeline (ROCm) ==="

# --- Create venv ---
if [ ! -d "$VENV" ]; then
    python3 -m venv "$VENV"
fi
source "$VENV/bin/activate"
#pip install -U pip uv

# --- Install PyTorch + friends with ROCm 6.2 ---
# MI300A/X fully supported on ROCm 6.2+
uv pip install \
    torch==2.10.0+rocm6.2 \
    torchvision==0.25.0+rocm6.2 \
    torchaudio==2.10.0+rocm6.2 \
    --index-url https://download.pytorch.org/whl/rocm6.2

# --- Build llama-cpp-python with HIP support for ROCm ---
uv pip install \
    --force-reinstall \
    --no-deps \
    "llama-cpp-python==0.3.22" \
    --config-settings=cmake.args="-DGGML_HIPBLAS=on;-DCMAKE_C_COMPILER=hipcc;-DCMAKE_CXX_COMPILER=hipcc" \
    --no-build-isolation

# --- Install project dependencies ---
uv pip install -r "$ROOT_DIR/requirements.txt"
uv pip install qwen-asr

# --- Install ACE-Step editable ---
uv pip install -e "$ROOT_DIR/ACE-Step-1.5"

echo "=== ROCm install complete ==="
echo "Activate with: source $VENV/bin/activate"

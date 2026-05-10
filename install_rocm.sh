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

# --- Install PyTorch + friends with ROCm 6.3 ---
uv pip install \
    torch==2.9.1+rocm6.3 \
    torchvision==0.24.1+rocm6.3 \
    torchaudio==2.9.1+rocm6.3 \
    --index-url https://download.pytorch.org/whl/rocm6.3

# --- Build llama-cpp-python with HIP (use pip directly to force source build) ---
# MI300A = gfx942. FORCE_CMAKE=1 forces cmake reconfigure.
CMAKE_ARGS="-DGGML_HIPBLAS=on -DCMAKE_C_COMPILER=hipcc -DCMAKE_CXX_COMPILER=hipcc -DAMDGPU_TARGETS=gfx942" \
FORCE_CMAKE=1 pip install \
    --force-reinstall \
    --no-cache-dir \
    --no-binary llama-cpp-python \
    "llama-cpp-python==0.3.22"

# --- Install project dependencies ---
uv pip install -r "$ROOT_DIR/requirements.txt"
uv pip install qwen-asr

# --- Install ACE-Step without PyTorch deps (requirements.txt hardcodes CUDA) ---
uv pip install -r "$ROOT_DIR/ACE-Step-1.5/requirements-rocm-linux.txt"
uv pip install --no-deps -e "$ROOT_DIR/ACE-Step-1.5"

# --- Re-pin ROCm torch at the END so nothing overwrites it ---
uv pip install \
    --force-reinstall \
    torch==2.9.1+rocm6.3 \
    torchvision==0.24.1+rocm6.3 \
    torchaudio==2.9.1+rocm6.3 \
    --index-url https://download.pytorch.org/whl/rocm6.3

echo "=== ROCm install complete ==="
echo "Activate with: source $VENV/bin/activate"
echo "Verify with: python -c \"import torch; print('cuda:', torch.cuda.is_available(), 'hip:', torch.version.hip)\""

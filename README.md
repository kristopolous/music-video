# Music Video Automator 🎵🎬

An agentic pipeline that transforms a simple text prompt into a fully synchronized, structurally intelligent music video using high-performance open-source AI models.

## 🌟 Features

- **Agentic Orchestration**: Uses `Qwen 3.6-35B` as a "Director" to plan lyrics and scenes.
- **Smart Music Generation**: `ACE-Step 1.5` generates the master audio track.
- **Perfect Synchronization**: `Qwen3-ASR` extracts timestamps to align visuals with the rhythm.
- **Dynamic Video Production**: `LTX-2.3` generates video clips conditioned on audio for perfect beat-matching.
- **Interactive Web UI**: A stylish, row-based "vertical timeline" that allows you to edit and regenerate from any stage.
- **High Efficiency**: GGUF-based models allow the entire pipeline to run on consumer-grade hardware (e.g., RTX 3090/4090).

## 🚀 Quick Start

### 1. Prerequisites
- NVIDIA GPU with 24GB+ VRAM recommended.
- [uv](https://github.com/astral-sh/uv) installed for fast Python management.

### 2. Setup
```bash
# Clone the repository and install dependencies
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 3. Launch the API
The backend handles model loading, persistence, and the execution pipeline.
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. Access the UI
Open your browser to:
**`http://127.0.0.1:8000/static/index.html`**

---

## 🛠 Usage

### Using the Web Interface
1.  **Enter Prompt**: Provide a **Topic** and a **Musical Style**.
2.  **Monitor**: Watch the vertical timeline as the AI "Brain," "Ear," and "Eye" complete each stage.
3.  **Iterate**: 
    - Don't like the lyrics? Click **Edit**, change them, and hit **Regenerate From Here**.
    - The system will only restart the necessary downstream steps (Song -> Video).

### Using the CLI
You can also trigger projects from the command line:
```bash
./.venv/bin/python cli.py start "A space odyssey" "Cinematic synthwave" --quality low
```

---

## 🏗 Pipeline Stages

1.  **Lyrics Generation**: `Qwen 3.6-35B` writes themed lyrics with structural markers.
2.  **Music Composition**: `ACE-Step 1.5` plans and synthesizes a master WAV file.
3.  **Timestamp Extraction**: `Qwen3-ASR` aligns the song and lyrics with millisecond precision.
4.  **Scene Breakdown**: The Director groups timestamps into descriptive visual chapters.
5.  **Video Production**: `LTX-2.3` produces clips of varying lengths `(8n+1 frames)` conditioned on the audio's rhythm.
6.  **Final Mastering**: `FFmpeg` merges scenes and muxes the high-fidelity master audio.

## 📦 Model Stack (GGUF)
All models are automatically downloaded from Hugging Face on first run:
- **Lyrics/Director**: `unsloth/Qwen3.6-35B-A3B-GGUF`
- **Music**: `Serveurperso/ACE-Step-1.5-GGUF`
- **Video**: `unsloth/LTX-2.3-GGUF`
- **ASR**: `Qwen/Qwen3-ASR-1.7B`

---

## 📝 Documentation
- [status.md](status.md): Project overview and completed features.
- [problems.md](problems.md): Current limitations and known issues.
- [improvements.md](improvements.md): Future roadmap and optimizations.

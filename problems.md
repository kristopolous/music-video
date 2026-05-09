# Current Problems & Limitations

## 1. Mocked Components
- **Brave Search API**: Currently uses a mock sleeper. Needs actual API key integration and image/video scraping logic.
- **FFmpeg Merging**: The final step of concatenating scene clips and muxing audio is currently a `time.sleep` placeholder.
- **ACE-Step DiT**: While the GGUF LM planning is implemented, the actual DiT synthesis for ACE-Step often requires a specific custom pipeline or `acestep.cpp` server which is currently mocked as "MOCK AUDIO DATA".

## 2. Resource Management
- **VRAM Conflict**: Loading Qwen, ACE-Step, and LTX-2.3 simultaneously will exceed 24GB VRAM.
- **Loading Latency**: Switching between models causes significant delays. We need a "model offloading" or "unloading" strategy to free up memory for the current active step.
- **Process Blocking**: Long-running model inference (even in threads) can occasionally jitter the FastAPI event loop if not carefully managed.

## 3. UI/UX Gaps
- **Prompt Edits**: The Web UI uses a standard browser `prompt()` for editing. This should be replaced with an inline, styled modal or textarea.
- **Scene-Specific Overrides**: Users currently can't edit an *individual* scene's prompt in the middle of a loop easily without regenerating the whole scene list.
- **Mobile Support**: The vertical timeline is stylish on desktop but too wide for mobile viewports.

## 4. Technical Fragility
- **Error Propagation**: If a model fails to load, the error messages in the UI could be more descriptive than just "FAILED".
- **Audio Alignment**: While the math for frame counts `(8n+1)` is correct, real-world synchronization might experience minor drift (1-2 frames) over long songs.
- **No Stop Button**: Once a pipeline starts, there is no clean way to "abort" the current background task from the UI.

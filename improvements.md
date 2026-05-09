# Future Improvements

## 1. Feature Additions
- **Real Asset Search**: Integrate the Brave Search API to download real video clips or images to serve as "seeds" for LTX-2.3.
- **FFmpeg Master**: Implement the automated assembly script that stitches scenes, applies transitions, and muxes the master audio.
- **Lip-Sync Enhancement**: Use LTX-2.3's native portrait support for specific scenes where a character is singing lyrics.

## 2. Advanced AI Capabilities
- **Spatial Upscaling**: Add an optional 7th step using the LTX-2.3-spatial-upscaler to take 480p previews to 4K resolution.
- **Recursive Directing**: Allow Qwen 3.6 to "critique" the generated clips and suggest prompt adjustments if the motion doesn't match the music's BPM.
- **Fine-grained Audio Conditioning**: Pass not just the audio, but the **spectrogram** or **onset data** to the video generator for even tighter visual beat-matching.

## 3. Web UI Enhancements
- **Inline Waveform Editor**: Allow users to trim the song or move scene boundaries directly on an audio timeline.
- **Gallery Mode**: A dedicated page to browse all past projects and their final exports.
- **Project Duplication**: Start a new project using the "Settings" of an old one (Style, Quality, etc.).

## 4. Operational Optimizations
- **Worker Queues**: Use a task queue like Celery or RQ for better management of multiple concurrent projects.
- **Quantization Toggle**: Allow users to choose between 4-bit, 8-bit, or Full precision models based on their hardware.
- **VRAM Offloading**: Implement a memory-aware `ModelManager` that aggressively clears the GPU cache between pipeline stages.
- **Multi-GPU Distribution**: Support running the "Brain" on GPU 0 and the "Eye" on GPU 1.

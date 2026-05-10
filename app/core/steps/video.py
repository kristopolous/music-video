import torch
import torchaudio
import asyncio
import os
from diffusers.utils import export_to_video
from app.core.steps.base import BaseStep
from app.core.model_manager import model_manager, detect_device
from app.models.schemas import QualityLevel

class GenerateVideoStep(BaseStep):
    async def run(self, project_id: str, context: dict):
        topic = context.get("topic")
        style = context.get("style")
        song_path = context.get("song_path")
        scene = context.get("current_scene") # {start, end, description}
        quality = context.get("quality", QualityLevel.MEDIUM)
        
        # Quality Settings
        if quality == QualityLevel.LOW:
            steps = 9
            width, height = 320, 192
        elif quality == QualityLevel.HIGH:
            steps = 29
            width, height = 1280, 720
        else: # MEDIUM
            steps = 19
            width, height = 848, 480
            
        start_time = scene["start"]
        end_time = scene["end"]
        duration = end_time - start_time
        
        # LTX-2.3 Requirement: Frames = (8 * n) + 1
        # Target 24 fps
        target_frames = int(duration * 24)
        n = max(1, (target_frames - 1) // 8) 
        num_frames = (8 * n) + 1
        actual_duration = (num_frames - 1) / 24

        await self.update_progress(project_id, f"Preparing audio segment ({actual_duration:.2f}s) for scene...", 0.1)
        
        def process_audio(path, start, dur):
            audio, sr = torchaudio.load(path)
            if sr != 24000:
                resampler = torchaudio.transforms.Resample(sr, 24000)
                audio = resampler(audio)
            
            start_sample = int(start * 24000)
            end_sample = start_sample + int(dur * 24000)
            return audio[:, start_sample:end_sample]

        audio_input = await asyncio.to_thread(process_audio, song_path, start_time, actual_duration)

        await self.update_progress(project_id, f"Generating {num_frames} frames for: {scene['description']} ({quality} quality)", 0.3)
        
        def generate(pipe, audio, prompt_desc, frame_count, num_steps, w, h):
            prompt = f"{prompt_desc}, cinematic style of {style}, rhythmically synced."
            
            with torch.no_grad():
                audio_latents = pipe.audio_vae.encode(
                    audio.unsqueeze(0).to("cuda", dtype=torch.bfloat16)
                ).latent_dist.sample()

            output = pipe(
                prompt=prompt,
                audio_latents=audio_latents,
                num_frames=frame_count,
                frame_rate=24,
                num_inference_steps=num_steps,
                width=w,
                height=h,
                audio_guidance_scale=7.0,
                use_cross_timestep=True
            )
            
            scene_idx = context.get("scene_index", 0)
            output_dir = f"output/{project_id}/scenes"
            os.makedirs(output_dir, exist_ok=True)
            output_path = f"{output_dir}/scene_{scene_idx:03d}.mp4"
            export_to_video(output.frames[0], output_path, fps=24)
            return output_path

        pipe = await model_manager.get_ltx()
        video_path = await asyncio.to_thread(generate, pipe, audio_input, scene["description"], num_frames, steps, width, height)
        
        return video_path

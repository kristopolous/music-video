from app.core.steps.base import BaseStep
from app.core.model_manager import model_manager
import asyncio
import os
import re
import logging

logger = logging.getLogger(__name__)

def _clean_lyrics(raw: str) -> str:
    """Strip structural tags like [verse], [chorus] and parenthetical notes."""
    text = re.sub(r'\[.*?\]', '', raw)
    text = re.sub(r'\(.*?\)', '', text)
    return re.sub(r'\n{3,}', '\n\n', text).strip()

class GenerateSongStep(BaseStep):
    async def run(self, project_id: str, context: dict):
        lyrics = _clean_lyrics(context.get("lyrics", ""))
        style = context.get("style")

        await self.update_progress(project_id, "Initializing ACE-Step for music generation...", 0.1)

        def generate(pipeline):
            from acestep.inference import GenerationParams, GenerationConfig, generate_music

            dit_handler, llm_handler = pipeline

            params = GenerationParams(
                task_type="text2music",
                caption=style,
                lyrics=lyrics,
                duration=30,
            )

            config = GenerationConfig(
                batch_size=1,
                audio_format="wav",
            )

            output_dir = f"output/{project_id}"
            os.makedirs(output_dir, exist_ok=True)

            result = generate_music(
                dit_handler, llm_handler, params, config, save_dir=output_dir
            )

            if not result.success:
                raise RuntimeError(f"Music generation failed: {result.error}")

            audio_path = result.audios[0]["path"]
            return audio_path

        pipeline = await model_manager.get_ace_step_pipeline()
        song_path = await asyncio.to_thread(generate, pipeline)

        context["song_path"] = song_path
        await self.update_progress(project_id, f"Song generated: {song_path}", 1.0)
        return song_path

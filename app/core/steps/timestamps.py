from app.core.steps.base import BaseStep
from app.core.model_manager import model_manager
import asyncio

class ExtractTimestampsStep(BaseStep):
    async def run(self, project_id: str, context: dict):
        song_path = context.get("song_path")
        lyrics = context.get("lyrics")
        
        await self.update_progress(project_id, "Extracting timestamps with Qwen3-ASR...", 0.1)
        
        def extract(asr):
            # Using Qwen3-ASR to align lyrics with the generated song
            results = asr.transcribe(
                audio=song_path,
                return_timestamps=True,
                forced_aligner="Qwen/Qwen3-ForcedAligner-0.6B"
            )
            # The result contains segments with start/end times
            return results[0].timestamps

        asr = await model_manager.get_asr()
        timestamps = await asyncio.to_thread(extract, asr)
        
        context["lyrics_with_timestamps"] = timestamps
        await self.update_progress(project_id, "Timestamps extracted.", 1.0)
        return timestamps

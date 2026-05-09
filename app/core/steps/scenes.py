from app.core.steps.base import BaseStep
from app.core.model_manager import model_manager
import asyncio
import json

class GenerateSceneListStep(BaseStep):
    async def run(self, project_id: str, context: dict):
        lyrics_with_timestamps = context.get("lyrics_with_timestamps")
        
        await self.update_progress(project_id, "Generating scene list from timestamps...", 0.1)
        
        def generate(qwen):
            # We ask Qwen to group the timestamped lyrics into logical scenes
            prompt = (
                f"Convert these timestamped lyrics into a list of scenes for a music video. "
                f"Each scene should have a 'start', 'end', and a descriptive 'description'. "
                f"Lyrics: {json.dumps([{'text': s.text, 'start': s.start, 'end': s.end} for s in lyrics_with_timestamps])}"
            )
            
            response = qwen.create_chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                response_format={"type": "json_object"}
            )
            return json.loads(response["choices"][0]["message"]["content"])["scenes"]

        qwen = await model_manager.get_qwen()
        scene_list = await asyncio.to_thread(generate, qwen)
        
        context["scene_list"] = scene_list
        await self.update_progress(project_id, f"Scene list generated ({len(scene_list)} scenes).", 1.0)
        return scene_list

from app.core.steps.base import BaseStep
from app.core.model_manager import model_manager
import asyncio

class GenerateLyricsStep(BaseStep):
    async def run(self, project_id: str, context: dict):
        topic = context.get("topic")
        style = context.get("style")
        
        await self.update_progress(project_id, "Initializing Qwen GGUF for lyrics generation...", 0.1)
        
        def generate(qwen):
            prompt = f"Write song lyrics about {topic} in the style of {style}. Include [verse], [chorus] tags."
            response = qwen.create_chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=16384
            )
            return response["choices"][0]["message"]["content"]

        qwen = await model_manager.get_qwen()
        lyrics = await asyncio.to_thread(generate, qwen)

        import re
        lyrics = re.sub(r'<\|thinking\|>.*?<\|end_of_thinking\|>', '', lyrics, flags=re.DOTALL)
        lyrics = lyrics.strip()

        context["lyrics"] = lyrics
        await self.update_progress(project_id, "Lyrics generated successfully.", 1.0)
        return lyrics

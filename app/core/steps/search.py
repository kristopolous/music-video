from app.core.steps.base import BaseStep
import asyncio
import logging

class BraveSearchStep(BaseStep):
    async def run(self, project_id: str, context: dict):
        topic = context.get("topic")
        await self.update_progress(project_id, f"Searching for assets for {topic}...", 0.5)
        # Mocking Brave Search API call
        await asyncio.sleep(1)
        context["assets"] = ["asset1.jpg", "asset2.jpg"]
        await self.update_progress(project_id, "Assets found.", 1.0)
        return context["assets"]

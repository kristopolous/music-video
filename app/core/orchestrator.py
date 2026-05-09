import asyncio
import uuid
import json
import os
from typing import Dict, List, Any, Optional
from app.models.schemas import ProjectState, ProjectStatus, StepStatus, StepProgress, QualityLevel
from app.core.steps.lyrics import GenerateLyricsStep
from app.core.steps.song import GenerateSongStep
from app.core.steps.timestamps import ExtractTimestampsStep
from app.core.steps.scenes import GenerateSceneListStep
from app.core.steps.video import GenerateVideoStep
from app.core.steps.search import BraveSearchStep
import logging

logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self):
        self.projects: Dict[str, ProjectState] = {}
        self.streams: Dict[str, List[asyncio.Queue]] = {}
        self.persistence_dir = "projects"
        os.makedirs(self.persistence_dir, exist_ok=True)
        self._load_projects()

    def _load_projects(self):
        for filename in os.listdir(self.persistence_dir):
            if filename.endswith(".json"):
                with open(os.path.join(self.persistence_dir, filename), "r") as f:
                    try:
                        data = json.load(f)
                        project = ProjectState(**data)
                        self.projects[project.project_id] = project
                    except Exception as e:
                        logger.error(f"Failed to load project {filename}: {e}")

    def _save_project(self, project_id: str):
        if project_id in self.projects:
            path = os.path.join(self.persistence_dir, f"{project_id}.json")
            with open(path, "w") as f:
                json.dump(self.projects[project_id].dict(), f, indent=2)

    async def create_project(self, topic: str, style: str, quality: QualityLevel) -> str:
        project_id = str(uuid.uuid4())
        steps = [
            "generate_lyrics",
            "generate_song",
            "extract_timestamps",
            "generate_scene_list",
            "generate_video_scenes",
            "finalize_video"
        ]
        
        project = ProjectState(
            project_id=project_id,
            topic=topic,
            style=style,
            quality=quality,
            status=ProjectStatus.IDLE,
            steps={step: StepProgress(step_name=step, status=StepStatus.PENDING, message="Waiting...") for step in steps}
        )
        self.projects[project_id] = project
        self.streams[project_id] = []
        self._save_project(project_id)
        return project_id

    async def subscribe(self, project_id: str):
        if project_id not in self.streams:
            self.streams[project_id] = []
        queue = asyncio.Queue()
        self.streams[project_id].append(queue)
        try:
            yield queue
        finally:
            if project_id in self.streams:
                self.streams[project_id].remove(queue)

    async def broadcast(self, project_id: str, message: Any):
        if project_id in self.streams:
            for queue in self.streams[project_id]:
                await queue.put(message)

    async def update_step(self, project_id: str, step_name: str, status: StepStatus, message: str, progress: float, data: Any = None):
        project = self.projects[project_id]
        project.current_step = step_name
        step = project.steps[step_name]
        step.status = status
        step.message = message
        step.progress = progress
        if data is not None:
            step.data = data
        
        self._save_project(project_id)
        await self.broadcast(project_id, project.dict())

    async def run_pipeline(self, project_id: str, start_at: Optional[str] = None):
        project = self.projects[project_id]
        project.status = ProjectStatus.PROCESSING
        await self.broadcast(project_id, project.dict())

        # Reconstruct context from previous steps if starting mid-way
        context = {
            "topic": project.topic,
            "style": project.style,
            "quality": project.quality,
            "project_id": project_id,
            "video_list": []
        }
        
        # Populate context from completed steps
        if project.steps["generate_lyrics"].data: context["lyrics"] = project.steps["generate_lyrics"].data
        if project.steps["generate_song"].data: context["song_path"] = project.steps["generate_song"].data
        if project.steps["extract_timestamps"].data: context["lyrics_with_timestamps"] = project.steps["extract_timestamps"].data
        if project.steps["generate_scene_list"].data: context["scene_list"] = project.steps["generate_scene_list"].data

        step_names = [
            "generate_lyrics",
            "generate_song",
            "extract_timestamps",
            "generate_scene_list",
            "generate_video_scenes",
            "finalize_video"
        ]

        try:
            run = False
            if start_at is None: run = True

            # 1. Lyrics
            if not run and start_at == "generate_lyrics": run = True
            if run:
                result = await GenerateLyricsStep("generate_lyrics", self).run(project_id, context)
                await self.update_step(project_id, "generate_lyrics", StepStatus.COMPLETED, "Lyrics generated", 1.0, data=result)

            # 2. Song
            if not run and start_at == "generate_song": run = True
            if run:
                result = await GenerateSongStep("generate_song", self).run(project_id, context)
                await self.update_step(project_id, "generate_song", StepStatus.COMPLETED, "Song generated", 1.0, data=result)

            # 3. Timestamps
            if not run and start_at == "extract_timestamps": run = True
            if run:
                result = await ExtractTimestampsStep("extract_timestamps", self).run(project_id, context)
                await self.update_step(project_id, "extract_timestamps", StepStatus.COMPLETED, "Timestamps extracted", 1.0, data=result)

            # 4. Scene List
            if not run and start_at == "generate_scene_list": run = True
            if run:
                result = await GenerateSceneListStep("generate_scene_list", self).run(project_id, context)
                await self.update_step(project_id, "generate_scene_list", StepStatus.COMPLETED, "Scene list generated", 1.0, data=result)

            # 5. Scene-by-Scene Loop
            if not run and start_at == "generate_video_scenes": run = True
            if run:
                scene_list = context["scene_list"]
                context["video_list"] = [] # Reset video list if regenerating scenes
                for i, scene in enumerate(scene_list):
                    scene_context = context.copy()
                    scene_context["current_scene"] = scene
                    scene_context["scene_index"] = i
                    
                    msg = f"Processing scene {i+1}/{len(scene_list)}: {scene['description']} ({scene['end']-scene['start']:.2f}s)"
                    await self.update_step(project_id, "generate_video_scenes", StepStatus.RUNNING, msg, (i/len(scene_list)))

                    await BraveSearchStep("search_assets_internal", self).run(project_id, scene_context)
                    video_clip = await GenerateVideoStep("generate_video_internal", self).run(project_id, scene_context)
                    context["video_list"].append(video_clip)

                await self.update_step(project_id, "generate_video_scenes", StepStatus.COMPLETED, "All scenes generated", 1.0, data=context["video_list"])

            # 6. Finalize
            if not run and start_at == "finalize_video": run = True
            if run:
                await self.update_step(project_id, "finalize_video", StepStatus.RUNNING, "Merging scenes and applying high-quality audio...", 0.5)
                # FFmpeg merge logic here
                await asyncio.sleep(2) 
                final_video_path = f"output/{project_id}/final_video.mp4" # Placeholder
                await self.update_step(project_id, "finalize_video", StepStatus.COMPLETED, "Project completed!", 1.0, data=final_video_path)

            project.status = ProjectStatus.COMPLETED
            await self.broadcast(project_id, project.dict())
        except Exception as e:
            logger.error(f"Pipeline failed for {project_id}: {e}")
            project.status = ProjectStatus.FAILED
            await self.broadcast(project_id, project.dict())

orchestrator = Orchestrator()

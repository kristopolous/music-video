from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
from app.core.orchestrator import orchestrator
from app.models.schemas import QualityLevel
from pydantic import BaseModel
from typing import Any, Optional
import json
import asyncio

router = APIRouter()

class ProjectCreate(BaseModel):
    topic: str
    style: str
    quality: QualityLevel = QualityLevel.MEDIUM

class StepUpdate(BaseModel):
    data: Any

class RegenerateRequest(BaseModel):
    from_step: Optional[str] = None

@router.post("/projects")
async def create_project(data: ProjectCreate, background_tasks: BackgroundTasks):
    project_id = await orchestrator.create_project(data.topic, data.style, data.quality)
    orchestrator.start_pipeline(project_id)
    return {"project_id": project_id}

@router.get("/projects/{project_id}")
async def get_project(project_id: str):
    if project_id not in orchestrator.projects:
        raise HTTPException(status_code=404, detail="Project not found")
    return orchestrator.projects[project_id]

@router.patch("/projects/{project_id}/steps/{step_name}")
async def update_step(project_id: str, step_name: str, update: StepUpdate):
    if project_id not in orchestrator.projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project = orchestrator.projects[project_id]
    if step_name not in project.steps:
        raise HTTPException(status_code=404, detail="Step not found")
    
    project.steps[step_name].data = update.data
    orchestrator._save_project(project_id)
    return project.steps[step_name]

@router.post("/projects/{project_id}/regenerate")
async def regenerate_project(project_id: str, req: RegenerateRequest, background_tasks: BackgroundTasks):
    if project_id not in orchestrator.projects:
        raise HTTPException(status_code=404, detail="Project not found")

    orchestrator.start_pipeline(project_id, start_at=req.from_step)
    return {"message": f"Regeneration started from {req.from_step or 'beginning'}"}

@router.get("/projects/{project_id}/events")
async def project_events(project_id: str):
    if project_id not in orchestrator.projects:
        raise HTTPException(status_code=404, detail="Project not found")

    async def event_generator():
        async for queue in orchestrator.subscribe(project_id):
            while True:
                data = await queue.get()
                yield f"data: {json.dumps(data)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

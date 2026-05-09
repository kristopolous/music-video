import asyncio
from abc import ABC, abstractmethod
from app.models.schemas import StepStatus
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.core.orchestrator import Orchestrator

class BaseStep(ABC):
    def __init__(self, name: str, orchestrator: "Orchestrator"):
        self.name = name
        self.orchestrator = orchestrator

    @abstractmethod
    async def run(self, project_id: str, context: dict) -> Any:
        pass

    async def update_progress(self, project_id: str, message: str, progress: float, status: StepStatus = StepStatus.RUNNING, data: Any = None):
        await self.orchestrator.update_step(project_id, self.name, status, message, progress, data)

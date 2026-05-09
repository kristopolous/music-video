from pydantic import BaseModel
from typing import List, Optional, Dict
from enum import Enum

class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class ProjectStatus(str, Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class QualityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class StepProgress(BaseModel):
    step_name: str
    status: StepStatus
    message: str
    progress: float = 0.0  # 0.0 to 1.0
    data: Optional[Any] = None

class ProjectState(BaseModel):
    project_id: str
    topic: str
    style: str
    quality: QualityLevel = QualityLevel.MEDIUM
    status: ProjectStatus
    current_step: Optional[str] = None
    steps: Dict[str, StepProgress] = {}

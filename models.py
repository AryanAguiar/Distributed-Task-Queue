from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class JobRequest(BaseModel):
    type: str
    payload: dict
    
class Job(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    payload: dict
    status: str = "pending"
    retries: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
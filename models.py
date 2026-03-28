from datetime import datetime
from pydantic import BaseModel, Field, field_validator
import uuid


class JobRequest(BaseModel):
    type: str
    payload: dict
    
    @field_validator('type')
    def type_must_be_known(cls, v):
        allowed = {"summarise", "validate", 'translate'}
        if not v in allowed:
            raise ValueError(f"Unknown job type: {v}")
        return v

    @field_validator('payload')
    def validate_payload(cls, v):
        if not v:
            raise ValueError("Payload is required")
        return v

class Job(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    payload: dict
    status: str = "pending"
    retries: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
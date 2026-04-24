from pydantic import BaseModel
from typing import Literal

class AlertDispatchPayload(BaseModel):
    incident_id: str
    channel: Literal["webhook", "email", "slack"]
    destination: str
    severity: Literal["low", "medium", "high", "critical"] = "medium"

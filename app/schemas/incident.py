from sqlalchemy import UUID
from typing import Literal, Optional
from pydantic import BaseModel

class IncidentOpenPayload(BaseModel):
    service_id: UUID
    failure_reason: Literal["timeout", "bad_status", "latency_exceeded", "connection_error"]
    consecutive_failures: int
    failed_check_ids: list[UUID]

class IncidentResolvePayload(BaseModel):
    incident_id: UUID
    resolved_by: Literal["auto", "manual"] = "auto"
    resolution_note: Optional[str] = None

class IncidentReportPayload(BaseModel):
    incident_id: UUID
    trigger: Literal["on_open", "on_resolve", "manual"] = "on_open"
    report_type: Literal["pdf", "xlsx"] = "pdf"

class EscalationCheckPayload(BaseModel):
    incident_id: UUID
    escalate_after_minutes: int = 30
    escalation_channel: Literal["webhook", "email", "slack"] = "webhook"
    escalation_destination: str

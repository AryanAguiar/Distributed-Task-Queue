import enum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.core.database import Base

class ReportTrigger(enum.Enum):
    manual = "manual"
    on_resolve = "on_resolve"
    on_open = "on_open"

class IncidentReport(Base):
    __tablename__ = "incident_reports"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False, index=True)
    report_type = Column(String, nullable=False)
    report_content = Column(String, nullable=False)
    trigger_type  = Column(Enum(ReportTrigger), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
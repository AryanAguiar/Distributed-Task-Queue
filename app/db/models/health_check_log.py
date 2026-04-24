from sqlalchemy import Column, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.core.database import Base

class HealthCheckLog(Base):
    __tablename__ = "health_check_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id"), nullable=False, index=True)
    status_code = Column(Integer)
    latency_ms = Column(Integer)
    is_healthy = Column(Boolean)
    checked_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
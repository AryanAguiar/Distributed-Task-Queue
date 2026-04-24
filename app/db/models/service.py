import enum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.core.database import Base

class ServiceStatus(enum.Enum):
    healthy = "healthy"
    degraded = "degraded"
    unhealthy = "unhealthy"

class Service(Base):
    __tablename__ = "services"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    url = Column(String)
    expected_status = Column(Integer)
    timeout = Column(Integer)
    max_latency_ms = Column(Integer)
    failure_threshold = Column(Integer)
    consecutive_failures = Column(Integer)
    current_status = Column(Enum(ServiceStatus), default=ServiceStatus.healthy, index=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
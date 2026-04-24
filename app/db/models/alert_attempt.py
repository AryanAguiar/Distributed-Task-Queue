from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.sql import func
from app.core.database import Base
import enum

    
class AlertStatus(enum.Enum):
    pending = "pending"
    delivered = "delivered"
    failed = "failed"
    dead_lettered = "dead_lettered"

class Channel(enum.Enum):
    email = "email"
    push = "push"
    webhook = "webhook"

class AlertAttempt(Base):
    __tablename__ = "alert_attempts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False, index=True)
    attempt_number = Column(Integer, nullable=False)
    channel = Column(Enum(Channel), nullable=False)
    status = Column(Enum(AlertStatus), nullable=False, index=True)
    error_message = Column(String, nullable=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
import uuid
from typing import Literal, Optional


class SummarisePayload(BaseModel):
    text: str
    max_words: int = 100
    style: Literal["bullet", "paragraph"] = "paragraph"

class ValidatePayload(BaseModel):
    data: dict
    rules: list[Literal["no_nulls", "email_format", "age_range", "phone_format"]]
    strict: bool = False

class TranslatePayload(BaseModel):
    text: str
    target_lang: str          
    source_lang: str = "auto"
    formality: Literal["formal", "informal"] = "formal"

class WebhookDeliverPayload(BaseModel):
    url: str
    body: dict
    method: Literal["POST", "PUT", "PATCH"] = "POST"
    headers: dict[str, str] = {}
    retry_on: list[int] = [429, 500, 502, 503, 504]

class PDFExtractPayload(BaseModel):
    source_url: str
    extract: list[Literal["text", "tables", "metadata"]] = ["text"]
    page_limit: Optional[int] = None

class DataQualityPayload(BaseModel):
    records: list[dict]
    rules: list[Literal["no_nulls", "email_format", "age_range"]]

class HealthCheckPayload(BaseModel):
    urls: list[str]
    timeout_seconds: int = 5
    expected_status: int = 200

class ReportGeneratePayload(BaseModel):
    title: str
    sections: list[str]
    format: Literal["pdf", "xlsx"] = "pdf"

AI_JOB_PAYLOAD = {
    "pdf_extract":        PDFExtractPayload,
    "report_generate":    ReportGeneratePayload,
    "summarise":          SummarisePayload,
    "translate":          TranslatePayload,
}

NORMAL_JOB_PAYLOAD = {
    "data_quality_check": DataQualityPayload,
    "health_check_batch": HealthCheckPayload,
    "validate":           ValidatePayload,
    "webhook_deliver":    WebhookDeliverPayload,
}

JOB_PAYLOAD_MAP = {**AI_JOB_PAYLOAD, **NORMAL_JOB_PAYLOAD}

AI_JOB_TYPES = set(AI_JOB_PAYLOAD.keys())
NORMAL_JOB_TYPES = set(NORMAL_JOB_PAYLOAD.keys())

class JobRequest(BaseModel):
    type: str
    payload: dict
    use_ai: bool = False
    priority: str = "normal"
    
    @field_validator('use_ai', mode='before')
    @classmethod
    def set_use_ai_for_known(cls, v, info):
        job_type = info.data.get('type')
        from models import AI_JOB_TYPES
        if job_type in AI_JOB_TYPES:
            return True
        return v
    
    @field_validator('type')
    def type_must_be_known(cls, v):
        allowed = set(JOB_PAYLOAD_MAP.keys())
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
    use_ai: bool = False
    priority: str = "normal"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    @field_validator('use_ai', mode='before')
    @classmethod
    def set_use_ai_for_known_types(cls, v, info):
        job_type = info.data.get('type')
        if job_type in AI_JOB_TYPES:
            return True
        return v
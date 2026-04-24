from pydantic import BaseModel

class ServiceHealthCheckPayload(BaseModel):
    service_id: str
    url: str
    timeout_seconds: int = 5
    expected_status: int = 200
    max_latency_ms: int = 2000

class HealthCheckPayload(BaseModel):
    urls: list[str]
    timeout_seconds: int = 5
    expected_status: int = 200

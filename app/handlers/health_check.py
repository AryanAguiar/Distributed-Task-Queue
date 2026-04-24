from app.queue.task_queue import get_redis, enqueue_job
from app.db.models import HealthCheckLog, Service, Incident
from app.db.models.incident import State
from app.core.database import AsyncSessionLocal
from app.schemas import Job
from sqlalchemy.future import select
import httpx
from app.schemas.service import ServiceHealthCheckPayload, HealthCheckPayload
from datetime import datetime
import time

async def handle_service_health_check(payload: ServiceHealthCheckPayload) -> dict:
    start = time.monotonic()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(payload.url, timeout = payload.timeout_seconds)
        latency_ms = int((time.monotonic() - start) * 1000)
        status_code = response.status_code
    
    except httpx.ConnectError:
        latency_ms = int((time.monotonic() - start) * 1000)
        status_code = None
        failure_reason = "connection_error"
    
    log = HealthCheckLog(
        service_id=payload.service_id,
        status_code=status_code,
        latency_ms=latency_ms,
        is_healthy=False,  
        checked_at=datetime.utcnow()
    )

    passed = (
        status_code == payload.expected_status and 
        latency_ms <= payload.max_latency_ms
    )

    log.is_healthy = passed

    async with AsyncSessionLocal() as db:
        db.add(log)
        await db.flush()

        result = await db.execute(select(Service).filter(Service.id == payload.service_id))
        service = result.scalar_one_or_none()
        
        if service:
            if passed:
                service.consecutive_failures = 0
                result = await db.execute(select(Incident).filter(
                    Incident.service_id == payload.service_id, 
                    Incident.state != State.resolved
                ))
                open_incident = result.scalar_one_or_none()
                
                if open_incident:
                    r = await get_redis()
                    try:
                        job = Job(
                            type="incident_resolve", 
                            payload={"incident_id": str(open_incident.id)},
                            use_ai=False
                        )
                        await enqueue_job(r, job)
                    finally:
                        await r.close()
            else:
                service.consecutive_failures = (service.consecutive_failures or 0) + 1
                if status_code is None:
                    failure_reason = "connection_error"
                elif status_code != payload.expected_status:
                    failure_reason = "unexpected_status"
                else:
                    failure_reason = "latency_exceeded"

                result = await db.execute(select(Incident).filter(
                    Incident.service_id == payload.service_id,
                    Incident.state != State.resolved
                ))
                
                existing = result.scalar_one_or_none()
                
                if (service.consecutive_failures >= service.failure_threshold and existing is None):
                    r = await get_redis()
                    try:
                        job = Job(
                            type="incident_open", 
                            payload={
                                "service_id": str(service.id),
                                "failure_reason": failure_reason,
                                "consecutive_failures": service.consecutive_failures,
                                "failed_check_ids": [str(log.id)]
                            }, 
                            use_ai=False
                        )
                        await enqueue_job(r, job)
                    finally:
                        await r.close()
        
        await db.commit()

    return log
           

async def handle_health_check_batch(payload: HealthCheckPayload) -> dict:
    results = []
    async with httpx.AsyncClient(timeout=payload.timeout_seconds) as http:
        for url in payload.urls:
            try:
                r = await http.get(url)
                results.append({
                    "url": url,
                    "status": r.status_code,
                    "ok": r.status_code == payload.expected_status,
                    "latency_ms": int(r.elapsed.total_seconds() * 1000),
                })
            except Exception as e:
                results.append({"url": url, "status": None, "ok": False, "error": str(e)})

    return {
        "checked": len(results),
        "healthy": sum(1 for r in results if r["ok"]),
        "results": results,
    }

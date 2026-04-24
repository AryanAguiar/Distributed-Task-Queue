from app.queue.task_queue import get_queue_for_job_type, refresh_lock, release_lock, acquire_lock, store_result
from metrics import increment_jobs_failed, increment_jobs_processed
from config import DEAD_LETTER_KEY, BACKOFF_BASE, MAX_RETRIES
import asyncio
from app.schemas import Job
import structlog
from app.handlers import process_job_payload


logger = structlog.get_logger()

async def renew_lock_loop(r, job_id: str, interval: int = 15):
    try:
        while True:
            await asyncio.sleep(interval)
            await refresh_lock(r, job_id)
    except asyncio.CancelledError:
        logger.info("Lock renewal cancelled", job_id=job_id)
        pass

async def process_job(r, job: Job):
    acquired = await acquire_lock(r, job.id)
    if not acquired:
        logger.warning("Job already being processed by another worker", job_id=job.id)
        return

    renewer_task = asyncio.create_task(renew_lock_loop(r, job.id))

    try:
        job.status = "processing"
        await store_result(r, job)
        result = await process_job_payload(job.type, job.payload, job.use_ai)
        job.status = "completed"
        job.payload["result"] = result
        await store_result(r,job)
        await increment_jobs_processed(r)

    except Exception as e:
        logger.error("job_failed", job_id=job.id, error=str(e), retries=job.retries)
        job.retries += 1

        if job.retries < MAX_RETRIES:
            wait = BACKOFF_BASE ** job.retries
            await asyncio.sleep(wait)
            queue = get_queue_for_job_type(job.type)
            await r.lpush(queue, job.model_dump_json())
        else:
            job.status = "failed"
            await r.lpush(DEAD_LETTER_KEY, job.model_dump_json())
            await store_result(r, job)
            await increment_jobs_failed(r)
    finally: 
        renewer_task.cancel()
        await release_lock(r, job.id)

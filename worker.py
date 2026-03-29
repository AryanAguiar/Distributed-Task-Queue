from task_queue import refresh_lock
from task_queue import release_lock, acquire_lock, get_redis, dequeue_job, store_result
from metrics import increment_jobs_failed, increment_jobs_processed
from ai import run_ai
from config import DEAD_LETTER_KEY, JOB_QUEUE_KEY, BACKOFF_BASE, MAX_RETRIES
import asyncio
from models import Job
import structlog
import signal


logger = structlog.get_logger()
shutdown_event = asyncio.Event()

def handle_shutdown(signum):
    logger.info("Shutdown signal received, finishing current job...", signal=signum)
    shutdown_event.set()

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
        result = await run_ai(job.type, job.payload)
        job.status = "completed"
        job.payload["result"] = result
        await store_result(r,job)
        await increment_jobs_processed(r)

    except Exception as e:
        logger.error("Error processing job", error=str(e))
        job.retries += 1

        if job.retries < MAX_RETRIES:
            wait = BACKOFF_BASE ** job.retries
            await asyncio.sleep(wait)
            await r.lpush(JOB_QUEUE_KEY, job.model_dump_json())
        else:
            job.status = "failed"
            await r.lpush(DEAD_LETTER_KEY, job.model_dump_json())
            await store_result(r, job)
            await increment_jobs_failed(r)
    finally: 
        renewer_task.cancel()
        await release_lock(r, job.id)

async def worker_loop():
    r = await get_redis()
    try:    
        while not shutdown_event.is_set():
            job = await dequeue_job(r)
            if job:
                logger.info("Processing job", job_id=job.id)
                await process_job(r, job)
            else:
                await asyncio.sleep(0.1)
        logger.info("Worker shut down gracefully.")
    finally:
        await r.close()
        
if __name__ == "__main__":
    from config import validate
    validate()
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    logger.info("Worker running...")
    asyncio.run(worker_loop())
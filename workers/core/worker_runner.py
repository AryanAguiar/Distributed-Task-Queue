from task_queue import enqueue_job
import asyncio
import structlog
from task_queue import get_redis


logger = structlog.get_logger()

async def worker_loop(
    *,
    dequeue_fn,
    process_job_fn,
    shutdown_event,
    job_filter=None,
    concurrency_control=None,
    idle_sleep=0.1,
    worker_name="worker",
):
    r = await get_redis()
    try:
        while not shutdown_event.is_set():
            job = await dequeue_fn(r)

            if job:
                if job_filter and not job_filter(job):
                    logger.info("Job filtered out, requeuing", job_id=job.id)
                    await enqueue_job(r, job)
                    continue
                
                logger.info("Processing job", job_id=job.id, job_type=job.type)
                
                try:
                    if concurrency_control:
                        async with concurrency_control:
                            await process_job_fn(r, job)
                    else:
                        await process_job_fn(r, job)
                
                except Exception as e:
                    logger.error("Unexpected error occured", job_id=job.id, error=str(e), worker=worker_name)
            
            else:
                await asyncio.sleep(idle_sleep)

    finally:
        await r.close()
        logger.info("Worker shut down gracefully", worker=worker_name)        
                    
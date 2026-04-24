from workers.core.worker_runner import worker_loop
from workers.core.lifecycle import setup_signal_handlers
from workers.core.job_processor import process_job
from app.queue.task_queue import dequeue_normal_job, get_redis, enqueue_job
from app.schemas import Job
import asyncio
import structlog

logger = structlog.get_logger()
# Setup signal handlers
shutdown_event = setup_signal_handlers()

# Filter out AI jobs
def no_ai_jobs(job):
    return not job.use_ai

# Background task to enqueue health checks periodically
async def health_check_enqueuer():
    r = await get_redis()
    try:
        while not shutdown_event.is_set():
            # TODO: Fetch your actual registered services here
            registered_services = [
                {"id": "service_1", "url": "https://example.com/health"},
                {"id": "service_2", "url": "https://api.example.com/ping"}
            ]
            
            for svc in registered_services:
                job = Job(
                    type="service_health_check", 
                    payload={
                        "service_id": svc["id"],
                        "url": svc["url"]
                    },
                    use_ai=False
                )
                await enqueue_job(r, job)
            
            logger.info("Enqueued health check batch", count=len(registered_services))
            
            # Sleep for 30 seconds or until shutdown event is set
            try:
                await asyncio.wait_for(shutdown_event.wait(), timeout=30)
            except asyncio.TimeoutError:
                pass # expected after 30s timeout
    except Exception as e:
        logger.error("Error in health_check_enqueuer", error=str(e))
    finally:
        await r.close()

# Main worker loop
async def main():
    # Start the periodic background task
    health_check_task = asyncio.create_task(health_check_enqueuer())

    await worker_loop(
        dequeue_fn=dequeue_normal_job,
        process_job_fn=process_job,
        shutdown_event=shutdown_event,
        job_filter=no_ai_jobs,
        worker_name="Normal worker",
    )
    
    # Wait for the background task to cleanly finish during shutdown
    await health_check_task

if __name__ == "__main__":
    asyncio.run(main())
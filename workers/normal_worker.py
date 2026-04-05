from workers.core.worker_runner import worker_loop
from workers.core.lifecycle import setup_signal_handlers
from workers.core.job_processor import process_job
from task_queue import dequeue_normal_job
import asyncio

# Setup signal handlers
shutdown_event = setup_signal_handlers()

# Filter out AI jobs
def no_ai_jobs(job):
    return not job.use_ai

# Main worker loop
async def main():
    await worker_loop(
        dequeue_fn=dequeue_normal_job,
        process_job_fn=process_job,
        shutdown_event=shutdown_event,
        job_filter=no_ai_jobs,
        worker_name="Normal worker",
    )

if __name__ == "__main__":
    asyncio.run(main())
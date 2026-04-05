from workers.core.worker_runner import worker_loop
from workers.core.lifecycle import setup_signal_handlers
from workers.core.job_processor import process_job
from task_queue import dequeue_ai_job
from aiolimiter import AsyncLimiter
import asyncio

# Setup signal handlers
shutdown_event = setup_signal_handlers()

# AI rate limiting
ai_limiter = AsyncLimiter(10, 60)
ai_semaphore = asyncio.Semaphore(3)

# Combined limiter for AI rate limiting
class CombinedLimiter:
    async def __aenter__(self):
        await ai_limiter.acquire()
        await ai_semaphore.acquire()

    async def __aexit__(self, *args):
        ai_semaphore.release()

# Main worker loop
async def main():
    await worker_loop(
        dequeue_fn=dequeue_ai_job,
        process_job_fn=process_job,
        shutdown_event=shutdown_event,
        concurrency_control=CombinedLimiter(),
        worker_name="AI worker",
    )

if __name__ == "__main__":
    asyncio.run(main())
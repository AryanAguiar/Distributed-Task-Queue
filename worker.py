from ai import run_ai
from config import DEAD_LETTER_KEY
from config import JOB_QUEUE_KEY
from config import BACKOFF_BASE
from config import MAX_RETRIES
from task_queue import get_redis, dequeue_job, store_result
import asyncio
from models import Job

async def process_job(r, job: Job):
    try:
        job.status = "processing"
        await store_result(r, job)

        result = await run_ai(job.type, job.payload)

        job.status = "completed"
        job.payload["result"] = result
        await store_result(r,job)
    except Exception as e:
        print(f"Error: {e}")
        job.retries += 1
        if job.retries < MAX_RETRIES:
            wait = BACKOFF_BASE ** job.retries
            await asyncio.sleep(wait)
            await r.lpush(JOB_QUEUE_KEY, job.model_dump_json())
        else:
            job.status = "failed"
            await r.lpush(DEAD_LETTER_KEY, job.model_dump_json())
            await store_result(r, job)

async def worker_loop():
    r = await get_redis()
    while True:
        job = await dequeue_job(r)
        if job:
            await process_job(r, job)
        else:
            await asyncio.sleep(0.1)

if __name__ == "__main__":
    print("Worker running...")
    asyncio.run(worker_loop())
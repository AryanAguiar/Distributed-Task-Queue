import redis.asyncio as redis
from config import REDIS_URL, JOB_QUEUE_KEY, JOB_RESULTS_KEY, JOB_RESULT_TTL
from models import Job


async def get_redis():
    return await redis.from_url(REDIS_URL, decode_responses=True)

async def enqueue_job(r, job: Job):
    await r.lpush(JOB_QUEUE_KEY, job.model_dump_json())

async def dequeue_job(r):
    result = await r.brpop(JOB_QUEUE_KEY, timeout=0)
    if result:
        _, data = result
        return Job.model_validate_json(data)
    return None

async def store_result(r, job: Job):
    await r.hset(JOB_RESULTS_KEY, job.id, job.model_dump_json())
    await r.expire(JOB_RESULTS_KEY, JOB_RESULT_TTL)

async def get_result(r, job_id: str):
    data = await r.hget(JOB_RESULTS_KEY, job_id)
    if data:
        return Job.model_validate_json(data)
    return None
import redis.asyncio as redis
from config import REDIS_URL, JOB_QUEUE_KEY, JOB_RESULT_TTL
from models import Job


# Lock prefix logic
LOCK_PREFIX = "job:lock:"

async def acquire_lock(r, job_id: str, ttl: int = 30) -> bool:
    key = f"{LOCK_PREFIX}{job_id}"
    return await r.set(key, "1", ex=ttl, nx=True)

async def release_lock(r, job_id: str):
    await r.delete(f"{LOCK_PREFIX}{job_id}")

async def refresh_lock(r, job_id: str, ttl: int = 30):
    result = await r.expire(f"{LOCK_PREFIX}{job_id}", ttl)
    if not result:
        raise RuntimeError(f"Lock lost for job {job_id}")


# Redis logic
async def get_redis():
    return await redis.from_url(REDIS_URL, decode_responses=True)

async def enqueue_job(r, job: Job):
    await r.lpush(JOB_QUEUE_KEY, job.model_dump_json())

async def dequeue_job(r):
    result = await r.brpop(JOB_QUEUE_KEY, timeout=2)
    if result:
        _, data = result
        return Job.model_validate_json(data)
    return None


# Job result prefix logic
JOB_RESULT_PREFIX = "job:result:"

async def store_result(r, job: Job):
    key = f"{JOB_RESULT_PREFIX}{job.id}"
    await r.set(key, job.model_dump_json(), ex=JOB_RESULT_TTL)

async def get_result(r, job_id: str):
    key = f"{JOB_RESULT_PREFIX}{job_id}"
    data = await r.get(key)
    if data:
        return Job.model_validate_json(data)
    return None
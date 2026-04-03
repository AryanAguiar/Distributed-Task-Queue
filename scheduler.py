import asyncio
from task_queue import get_redis, enqueue_job
from models import Job

SCHEDULES = [
    {"type": "summarise", "payload": {"text": "daily report"}, "interval": 3600},
]

async def schedule_loop():
    r = await get_redis()
    while True:
        for schedule in SCHEDULES:
            job = Job(type = schedule["type"], payload = schedule["payload"])
            await enqueue_job(r, job)
        await asyncio.sleep(60)

if __name__ == "__main__":
    from config import validate
    validate()
    asyncio.run(schedule_loop())

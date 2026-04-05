import asyncio
from task_queue import get_redis, enqueue_job
from models import Job


import time

SCHEDULES = [
    
]

async def schedule_loop():
    r = await get_redis()
    last_run = {s["type"]: 0 for s in SCHEDULES}

    while True:
        now = time.time()
        for schedule in SCHEDULES:
            job_type = schedule["type"]
            if now - last_run[job_type] >= schedule["interval"]:
                job = Job(
                    type=job_type, 
                    payload=schedule["payload"],
                    use_ai=True  
                )
                await enqueue_job(r, job)
                last_run[job_type] = now
        await asyncio.sleep(10)

if __name__ == "__main__":
    from config import validate
    validate()
    asyncio.run(schedule_loop())

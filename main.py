from config import JOB_QUEUE_KEY, validate
from fastapi import HTTPException, FastAPI, Depends, Request
from task_queue import get_result, enqueue_job, get_redis
from models import JobRequest, Job
from contextlib import asynccontextmanager
from prometheus_client import make_asgi_app
from metrics import get_metrics, queue_depth_gauge

validate()

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = await get_redis()
    yield
    await app.state.redis.close()

app = FastAPI(lifespan=lifespan)

metrics_app = make_asgi_app()
app.mount("/prometheus", metrics_app)

async def get_r(request: Request):
    return request.app.state.redis

# submit job to enqueue
@app.post('/jobs')
async def create_job(job_request: JobRequest, r=Depends(get_r)):
    job = Job(type=job_request.type, payload=job_request.payload)
    await enqueue_job(r, job)
    return {"job_id": job.id}
 
# client polling for job status
@app.get('/jobs/{job_id}')
async def get_job_status(job_id: str, r=Depends(get_r)):
    job = await get_result(r, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get('/queue/depth')
async def get_queue_depth(r=Depends(get_r)):
    depth = await r.llen(JOB_QUEUE_KEY)
    queue_depth_gauge.set(depth)
    return {"queue_depth": depth}

@app.get("/metrics/jobs")
async def job_metrics(r=Depends(get_r)):
    return await get_metrics(r)

@app.get("/health")
async def health(r=Depends(get_r)):
    try:
        await r.ping()
        return {"status": "ok", "redis": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Redis unavailable: {str(e)}")

# run with: uvicorn main:app --reload
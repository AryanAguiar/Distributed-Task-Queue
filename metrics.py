from prometheus_client import Gauge
 
 
queue_depth_gauge = Gauge("queue_depth", "Current queue depth") 

async def increment_jobs_processed(r):
    await r.incr("metrics:jobs_processed")

async def increment_jobs_failed(r): 
    await r.incr("metrics:jobs_failed")

async def get_metrics(r):
    return {
        "jobs_processed": int(await r.get("metrics:jobs_processed") or 0),
        "jobs_failed": int(await r.get("metrics:jobs_failed") or 0),
    }
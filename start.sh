#!/bin/bash
python workers/normal_worker.py &
python workers/ai_worker.py &
python scheduler.py &
uvicorn main:app --host 0.0.0.0 --port 8000
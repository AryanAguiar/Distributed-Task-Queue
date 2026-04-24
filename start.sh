#!/bin/bash
python workers/core/normal_worker.py &
python scheduler.py &
uvicorn main:app --host 0.0.0.0 --port 8000
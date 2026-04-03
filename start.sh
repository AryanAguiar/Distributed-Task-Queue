#!/bin/bash
python worker.py &
python scheduler.py &
uvicorn main:app --host 0.0.0.0 --port 8000
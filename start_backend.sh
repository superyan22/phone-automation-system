#!/bin/bash
cd /home/yan/phone-automation-system/backend
source /home/yan/litellm-venv/bin/activate
export DATABASE_URL="postgresql://postgres@localhost:5432/phone_automation"
export REDIS_URL="redis://:redis123@localhost:6379/1"
python -m uvicorn main:app --host 0.0.0.0 --port 8000

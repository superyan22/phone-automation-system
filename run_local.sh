#!/bin/bash
# Run backend directly on host for testing
cd "$(dirname "$0")/backend"
source /home/yan/litellm-venv/bin/activate

# Set database URL (use local PostgreSQL or SQLite for testing)
export DATABASE_URL="postgresql+asyncpg://postgres:***@localhost:5432/phone_automation"
export REDIS_URL="redis://localhost:6379/0"

# Start backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
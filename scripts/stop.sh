#!/bin/bash
# scripts/stop.sh

set -e

echo "Stopping Phone Automation System..."

# Stop all services
docker-compose down

echo "✅ Phone Automation System stopped successfully!"

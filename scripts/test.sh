#!/bin/bash
# scripts/test.sh

set -e

echo "Testing Phone Automation System..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Build and start services
echo "Building and starting services..."
docker-compose up -d --build

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 15

# Check backend health
echo "Checking backend health..."
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    docker-compose logs backend
    exit 1
fi

# Check frontend
echo "Checking frontend..."
if curl -s http://localhost:3000 | grep -q "Phone Automation"; then
    echo "✅ Frontend is accessible"
else
    echo "❌ Frontend check failed"
    docker-compose logs frontend
    exit 1
fi

# Check API documentation
echo "Checking API documentation..."
if curl -s http://localhost:8000/docs | grep -q "FastAPI"; then
    echo "✅ API documentation is accessible"
else
    echo "❌ API documentation check failed"
fi

echo ""
echo "✅ All tests passed!"
echo ""
echo "📊 Service URLs:"
echo "   - Frontend: http://localhost:3000"
echo "   - Backend API: http://localhost:8000"
echo "   - API Documentation: http://localhost:8000/docs"
echo ""
echo "📝 Useful commands:"
echo "   - View logs: docker-compose logs -f"
echo "   - Stop services: docker-compose down"
echo "   - Restart services: docker-compose restart"

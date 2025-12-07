#!/bin/bash
# Development Environment Startup Script

set -e

echo "🚀 Starting Orchestrator AI Development Environment"
echo "=================================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start services
echo "📦 Starting services (Redis, PostgreSQL)..."
docker-compose -f docker-compose.dev.yml up -d redis postgres

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check Redis
if docker exec orchestrator-ai-redis-1 redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is ready"
else
    echo "❌ Redis is not ready"
fi

# Check PostgreSQL
if docker exec orchestrator-ai-postgres-1 pg_isready -U orchestrator > /dev/null 2>&1; then
    echo "✅ PostgreSQL is ready"
else
    echo "❌ PostgreSQL is not ready"
fi

echo ""
echo "🎯 Starting API server..."
echo "   API will be available at: http://localhost:8000"
echo "   API docs at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Activate virtual environment and start server
source venv/bin/activate
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload


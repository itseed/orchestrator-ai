#!/bin/bash
# Rollback script for orchestrator-ai

set -e

PREVIOUS_VERSION=${1:-previous}

echo "Rolling back to version: $PREVIOUS_VERSION"

# Stop current services
echo "Stopping current services..."
docker-compose down

# Restore previous version
if [ ! -z "$DOCKER_REGISTRY" ]; then
    docker pull $DOCKER_REGISTRY/orchestrator-ai:$PREVIOUS_VERSION
    docker tag $DOCKER_REGISTRY/orchestrator-ai:$PREVIOUS_VERSION orchestrator-ai:latest
fi

# Start services with previous version
echo "Starting services with previous version..."
docker-compose up -d

# Wait for health checks
echo "Waiting for services to be healthy..."
sleep 10

# Health check
HEALTH_URL="http://localhost:8000/api/v1/health"
if curl -f $HEALTH_URL > /dev/null 2>&1; then
    echo "Rollback completed successfully!"
else
    echo "Rollback health check failed!"
    exit 1
fi


#!/bin/bash
# Deployment script for orchestrator-ai

set -e

ENVIRONMENT=${1:-production}
VERSION=${2:-latest}

echo "Deploying orchestrator-ai to $ENVIRONMENT (version: $VERSION)"

# Load environment-specific configuration
if [ -f ".env.$ENVIRONMENT" ]; then
    export $(cat .env.$ENVIRONMENT | xargs)
fi

# Build Docker image
echo "Building Docker image..."
docker build -t orchestrator-ai:$VERSION .

# Tag for registry (if needed)
if [ ! -z "$DOCKER_REGISTRY" ]; then
    docker tag orchestrator-ai:$VERSION $DOCKER_REGISTRY/orchestrator-ai:$VERSION
    docker push $DOCKER_REGISTRY/orchestrator-ai:$VERSION
fi

# Run database migrations
echo "Running database migrations..."
docker-compose run --rm orchestrator alembic upgrade head

# Deploy services
echo "Deploying services..."
docker-compose up -d

# Wait for health checks
echo "Waiting for services to be healthy..."
sleep 10

# Health check
echo "Performing health check..."
HEALTH_URL="http://localhost:8000/api/v1/health"
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f $HEALTH_URL > /dev/null 2>&1; then
        echo "Health check passed!"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Health check failed, retrying... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "Health check failed after $MAX_RETRIES retries"
    exit 1
fi

echo "Deployment completed successfully!"


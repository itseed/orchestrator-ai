# Deployment Guide

This directory contains deployment configurations and scripts for orchestrator-ai.

## Structure

```
deployment/
├── .env.example          # Environment configuration template
├── prometheus.yml        # Prometheus configuration
├── scripts/              # Deployment scripts
│   ├── deploy.sh        # Deployment script
│   └── rollback.sh      # Rollback script
├── kubernetes/           # Kubernetes manifests
│   ├── deployment.yaml  # Main application deployment
│   ├── configmap.yaml   # Configuration map
│   ├── redis.yaml       # Redis StatefulSet
│   ├── postgres.yaml    # PostgreSQL StatefulSet
│   └── README.md        # Kubernetes deployment guide
└── grafana/             # Grafana configuration
    ├── dashboards/      # Grafana dashboards
    └── datasources/     # Grafana datasources
```

## Docker Deployment

### Development

```bash
# Start development environment with hot reload
docker-compose -f docker-compose.dev.yml up

# Or use Dockerfile.dev
docker build -f Dockerfile.dev -t orchestrator-ai:dev .
docker run -p 8000:8000 orchestrator-ai:dev
```

### Production

```bash
# Build production image
docker build -t orchestrator-ai:latest .

# Start with docker-compose
docker-compose up -d

# Or use deployment script
./deployment/scripts/deploy.sh production latest
```

## Environment Configuration

1. Copy `.env.example` to `.env.production` or `.env.staging`
2. Fill in all required values
3. Use the appropriate environment file during deployment

## Kubernetes Deployment

See [kubernetes/README.md](kubernetes/README.md) for detailed Kubernetes deployment instructions.

## Health Checks

All services include health checks:
- Application: `GET /api/v1/health`
- Redis: `redis-cli ping`
- PostgreSQL: `pg_isready`

## Monitoring

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)
- Metrics endpoint: http://localhost:9090/metrics

## Rollback

```bash
./deployment/scripts/rollback.sh previous-version
```

Or for Kubernetes:
```bash
kubectl rollout undo deployment/orchestrator-ai
```


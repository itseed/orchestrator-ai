# Kubernetes Deployment

This directory contains Kubernetes manifests for deploying orchestrator-ai.

## Prerequisites

- Kubernetes cluster (1.20+)
- kubectl configured
- Docker registry access (if using private registry)

## Deployment Steps

1. **Create secrets:**
```bash
kubectl create secret generic orchestrator-secrets \
  --from-literal=database-url='postgresql://orchestrator:password@orchestrator-postgres:5432/orchestrator' \
  --from-literal=api-key='your-api-key' \
  --from-literal=secret-key='your-secret-key' \
  --from-literal=postgres-password='your-postgres-password' \
  --from-literal=openai-api-key='your-openai-key'
```

2. **Deploy infrastructure:**
```bash
kubectl apply -f redis.yaml
kubectl apply -f postgres.yaml
```

3. **Wait for infrastructure to be ready:**
```bash
kubectl wait --for=condition=ready pod -l app=orchestrator-redis --timeout=300s
kubectl wait --for=condition=ready pod -l app=orchestrator-postgres --timeout=300s
```

4. **Deploy application:**
```bash
kubectl apply -f configmap.yaml
kubectl apply -f deployment.yaml
```

5. **Check status:**
```bash
kubectl get pods
kubectl get services
kubectl get hpa
```

## Scaling

The deployment includes HorizontalPodAutoscaler (HPA) that automatically scales based on CPU and memory usage.

Manual scaling:
```bash
kubectl scale deployment orchestrator-ai --replicas=5
```

## Monitoring

Access Prometheus metrics:
```bash
kubectl port-forward svc/orchestrator-ai 9090:9090
```

## Rollback

Rollback to previous version:
```bash
kubectl rollout undo deployment/orchestrator-ai
```


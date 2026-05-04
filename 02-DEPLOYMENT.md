# Deployment Guide

**Get Mohawk Nexus running in production.**

## Deployment Options

Choose based on your needs:

| Option | Setup Time | Best For | Learning Curve |
|--------|-----------|----------|-----------------|
| Docker Compose | 5 min | Local dev, small deployments | Easy |
| Kubernetes | 20 min | Production, scaling | Medium |
| Managed K8s (EKS/GKE) | 30 min | Enterprise, multi-region | Medium |
| Docker Swarm | 15 min | Single-host clusters | Easy |

## Docker Compose (Development)

### Setup
```bash
cd Mohawk-Nexus
docker-compose -f docker/docker-compose.yml up -d
docker-compose logs -f
```

### What Starts
- ✓ Core runtime aggregator
- ✓ Python FL orchestrator
- ✓ Prometheus monitoring
- ✓ Grafana dashboards (localhost:3000)
- ✓ PostgreSQL for state

### Production Docker Compose
See `examples/docker-compose-prod.yml` for production hardening.

## Kubernetes (Production)

### Prerequisites
```bash
# Install tools
kubectl version --client
helm version

# Create namespace
kubectl create namespace mohawk
```

### Deploy
```bash
# Apply manifests
kubectl apply -f k8s/ -n mohawk

# Watch rollout
kubectl rollout status deployment/mohawk-core -n mohawk
kubectl rollout status deployment/mohawk-fl-orchestrator -n mohawk

# Verify pods
kubectl get pods -n mohawk

# Port forward
kubectl port-forward -n mohawk svc/mohawk-core 8080:8080
kubectl port-forward -n mohawk svc/grafana 3000:3000
```

### What Deploys
- ✓ 3× aggregator pods (BFT consensus)
- ✓ Orchestrator deployment
- ✓ Prometheus StatefulSet
- ✓ Grafana deployment
- ✓ PostgreSQL StatefulSet
- ✓ ConfigMaps & Secrets

### Configuration
Edit `k8s/configmap.yaml`:
```yaml
data:
  config.yaml: |
    consensus:
      max_faults: 1  # BFT can tolerate 1/3 failures
    aggregation:
      memory_limit: 1Gi
    monitoring:
      prometheus_enabled: true
```

### Scaling
```bash
# Scale aggregators
kubectl scale deployment mohawk-core --replicas=5 -n mohawk

# Scale orchestrator
kubectl scale deployment mohawk-fl-orchestrator --replicas=3 -n mohawk

# Check status
kubectl top nodes -n mohawk
kubectl top pods -n mohawk
```

## Cloud Platforms

### Amazon EKS

```bash
# Create cluster
eksctl create cluster --name mohawk-nexus --region us-east-1

# Connect
aws eks update-kubeconfig --name mohawk-nexus --region us-east-1

# Deploy
kubectl apply -f k8s/ -n mohawk

# Monitor
kubectl logs deployment/mohawk-core -f -n mohawk
```

### Google GKE

```bash
# Create cluster
gcloud container clusters create mohawk-nexus \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type n1-standard-4

# Connect
gcloud container clusters get-credentials mohawk-nexus

# Deploy
kubectl apply -f k8s/ -n mohawk
```

### Microsoft AKS

```bash
# Create cluster
az aks create --resource-group mohawk \
  --name mohawk-nexus \
  --node-count 3

# Connect
az aks get-credentials --resource-group mohawk --name mohawk-nexus

# Deploy
kubectl apply -f k8s/ -n mohawk
```

## Configuration Management

### Environment Variables
```bash
# Create .env file
cp .env.example .env

# Set values
CONSENSUS_MAX_FAULTS=1
AGGREGATION_MEMORY_LIMIT=2Gi
LOG_LEVEL=info
PROMETHEUS_ENABLED=true
```

### Secrets (Kubernetes)
```bash
# Create secrets
kubectl create secret generic mohawk-secrets \
  --from-literal=db-password=YOUR_PASSWORD \
  -n mohawk

# Reference in deployment
env:
  - name: DB_PASSWORD
    valueFrom:
      secretKeyRef:
        name: mohawk-secrets
        key: db-password
```

### ConfigMaps
```bash
# Create ConfigMap
kubectl create configmap mohawk-config \
  --from-file=config/production.yaml \
  -n mohawk

# Apply to pods
volumeMounts:
  - name: config
    mountPath: /etc/mohawk
```

## Monitoring & Observability

### Prometheus

```bash
# Port forward
kubectl port-forward -n mohawk svc/prometheus 9090:9090

# Access: http://localhost:9090

# Key metrics:
# - consensus_rounds_total
# - aggregation_latency_ms
# - nodes_participating
# - update_verification_errors
```

### Grafana

```bash
# Port forward
kubectl port-forward -n mohawk svc/grafana 3000:3000

# Access: http://localhost:3000
# Username: admin
# Password: (from ConfigMap)

# Dashboards:
# - Overview (aggregator health)
# - Consensus (BFT progress)
# - Performance (latency, throughput)
# - Nodes (participation, errors)
```

### Logging

```bash
# View logs
kubectl logs deployment/mohawk-core -f -n mohawk

# Multi-pod logs
kubectl logs -l app=mohawk-core -f -n mohawk

# Previous container (if crashed)
kubectl logs pod-name -c container-name --previous
```

## Security Hardening

### Network Policies

```bash
# Apply network policies
kubectl apply -f k8s/network-policy.yaml -n mohawk

# Restrict traffic:
# - Only allow core↔core communication
# - Only allow ingress on :8080
# - Block egress except DNS
```

### Pod Security

```bash
# Run as non-root
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false

# Resource limits
resources:
  limits:
    cpu: "2"
    memory: "2Gi"
  requests:
    cpu: "1"
    memory: "1Gi"
```

### Secrets Encryption

```bash
# Enable at-rest encryption
kubectl apply -f k8s/encryption-config.yaml

# Verify
kubectl describe secret mohawk-secrets -n mohawk
```

## Performance Tuning

### Memory Optimization
```yaml
# Reduce memory footprint
consensus:
  sketching:
    enable_incremental: true
    batch_size: 10000

# Result: 224x memory reduction
```

### Latency Optimization
```yaml
# Reduce consensus rounds
consensus:
  timeout_ms: 5000  # 5 second timeout
  max_rounds: 3

# Result: <500ms consensus latency
```

### Throughput Optimization
```yaml
# Parallel aggregation
aggregation:
  num_workers: 4
  buffer_size: 100000

# Result: 1M+ updates/second
```

## Backup & Recovery

### Database Backup
```bash
# Backup PostgreSQL
kubectl exec -n mohawk pod/postgresql \
  -- pg_dump -U postgres mohawk > backup.sql

# Restore
kubectl exec -n mohawk pod/postgresql \
  -- psql -U postgres < backup.sql
```

### Ledger Backup
```bash
# Backup consensus ledger
kubectl cp mohawk/mohawk-core:/data/ledger.db ./ledger-backup.db -n mohawk

# Restore
kubectl cp ./ledger-backup.db mohawk/mohawk-core:/data/ledger.db -n mohawk
```

## Disaster Recovery

### Single Aggregator Failure
```bash
# Automatic: Kubernetes reschedules pod
# BFT consensus: Still works (1/3 fault tolerance)

# Verify
kubectl get pods -n mohawk
# Should still show 2/3 aggregators healthy
```

### Multi-Aggregator Failure (>1/3)
```bash
# Consensus pauses (safety over availability)
# Manually:

# 1. Fix or replace failed nodes
kubectl delete pod aggregator-2 -n mohawk

# 2. Kubernetes reschedules
kubectl rollout status deployment/mohawk-core

# 3. Consensus resumes
kubectl logs deployment/mohawk-core -f
```

### Database Failure
```bash
# Restore from backup
kubectl apply -f k8s/statefulset-postgresql.yaml

# Restore data
kubectl cp ./backup.sql pod/postgresql:/tmp/ -n mohawk
kubectl exec pod/postgresql -- psql < /tmp/backup.sql
```

## Compliance & Auditing

### HIPAA (Healthcare)
```bash
# Enable HIPAA audit logging
kubectl set env deployment/mohawk-core \
  HIPAA_AUDIT=true \
  AUDIT_LOG_RETENTION_DAYS=90 \
  -n mohawk

# Verify logs stored
kubectl exec -n mohawk pod/mohawk-core \
  -- tail -f /var/log/hipaa-audit.log
```

### GDPR (Data Protection)
```bash
# Enable GDPR compliance checks
kubectl set env deployment/mohawk-core \
  GDPR_ENABLED=true \
  DATA_RETENTION_DAYS=90 \
  -n mohawk

# Generate DPIA
kubectl exec -n mohawk pod/mohawk-core \
  -- ./generate-dpia.sh > dpia-evidence.json
```

## Troubleshooting

See [`05-TROUBLESHOOTING.md`](05-TROUBLESHOOTING.md) for common issues.

### Quick Diagnostics
```bash
# Check cluster
kubectl cluster-info

# Check pods
kubectl get pods -n mohawk

# Check events
kubectl get events -n mohawk --sort-by='.lastTimestamp'

# Check logs
kubectl logs deployment/mohawk-core -n mohawk

# Describe pod
kubectl describe pod/aggregator-0 -n mohawk
```

## Next Steps

- Read [`03-CONTRIBUTING.md`](03-CONTRIBUTING.md) to contribute
- Check [`06-SECURITY.md`](06-SECURITY.md) for hardening
- See [`examples/`](../examples/) for complete setups
- Review [`docs/README.md`](README.md) for more docs

---

[← Back to Docs Index](README.md)

# Troubleshooting

**Fix common issues.**

## Docker Issues

### Docker not installed
```bash
# macOS
brew install docker

# Linux
sudo apt-get install docker.io docker-compose

# Windows
Download Docker Desktop from docker.com/download
```

### Container won't start
```bash
# Check logs
docker-compose logs aggregator

# Check image exists
docker images | grep mohawk

# Rebuild image
docker-compose build --no-cache

# Try again
docker-compose up
```

### Port already in use
```bash
# Find process using port
lsof -i :8080

# Kill process
kill -9 PID

# Or use different port
docker-compose -f docker-compose.yml -e PORT=8081 up
```

## Kubernetes Issues

### Pods not starting
```bash
# Check pod status
kubectl get pods -n mohawk

# Describe problematic pod
kubectl describe pod aggregator-0 -n mohawk

# Check events
kubectl get events -n mohawk --sort-by='.lastTimestamp'
```

### Pending pods
```bash
# Check node resources
kubectl top nodes

# Check pod resource requests
kubectl describe pod aggregator-0 -n mohawk | grep -A 5 Resources

# Scale down other pods or add nodes
kubectl scale deployment test-app --replicas=0
```

### CrashLoopBackOff
```bash
# Check logs
kubectl logs pod/aggregator-0 -n mohawk

# Previous container logs
kubectl logs pod/aggregator-0 -n mohawk --previous

# Increase timeout
kubectl patch deployment mohawk-core -n mohawk \
  -p '{"spec":{"template":{"spec":{"terminationGracePeriodSeconds":60}}}}'
```

## Network Issues

### Connection refused
```bash
# Check service exists
kubectl get svc -n mohawk

# Port forward for testing
kubectl port-forward svc/mohawk-core 8080:8080 -n mohawk

# Test
curl http://localhost:8080/health
```

### DNS resolution fails
```bash
# Check DNS pod
kubectl get pods -n kube-system | grep dns

# Restart DNS
kubectl rollout restart deployment/coredns -n kube-system

# Test from pod
kubectl run -it --rm debug --image=alpine --restart=Never -- \
  nslookup mohawk-core.mohawk.svc.cluster.local
```

### Firewall blocking traffic
```bash
# Check network policy
kubectl get networkpolicy -n mohawk

# Remove restrictive policy (if testing)
kubectl delete networkpolicy deny-all -n mohawk

# Apply correct policy
kubectl apply -f k8s/network-policy.yaml
```

## Performance Issues

### High latency
```bash
# Check aggregation latency
kubectl logs deployment/mohawk-core -n mohawk | grep latency

# Check pod CPU/memory
kubectl top pods -n mohawk

# Increase replicas
kubectl scale deployment mohawk-core --replicas=5 -n mohawk
```

### High memory usage
```bash
# Check memory limit
kubectl describe pod aggregator-0 -n mohawk

# Increase limit (edit k8s/configmap.yaml)
aggregation:
  memory_limit: 4Gi  # Increase from 1Gi

# Restart pods
kubectl rollout restart deployment/mohawk-core -n mohawk
```

### Slow builds
```bash
# Clear Docker cache
docker system prune -a

# Build with progress output
docker build --no-cache --progress=plain -f docker/Dockerfile.core .

# Check disk space
docker system df
```

## Cryptography Issues

### Proof verification fails
```bash
# Enable debug logging
kubectl set env deployment/mohawk-core DEBUG_CRYPTO=true -n mohawk

# Check logs
kubectl logs deployment/mohawk-core -n mohawk | grep "proof"

# Common causes:
# - Node TPM not working
# - Proof timeout (zk-SNARK took >10ms)
# - Incompatible crypto version
```

### Hardware attestation fails
```bash
# Check TPM status
cat /sys/devices/virtual/tpm0/tpm_version

# On macOS (simulated)
# TPM2 simulator may need restart
brew services restart tpm2-abrmd

# Check attestation logs
kubectl logs deployment/mohawk-core -n mohawk | grep "attestation"
```

### Signature verification fails
```bash
# Check key material
kubectl get secret tpm-keys -n mohawk -o yaml

# Verify XMSS setup
kubectl logs deployment/mohawk-core -n mohawk | grep "XMSS"

# Reset keys (WARNING: requires re-attestation)
kubectl delete secret tpm-keys -n mohawk
kubectl rollout restart deployment/mohawk-core -n mohawk
```

## Consensus Issues

### Consensus not finalizing
```bash
# Check fault tolerance
# > 1/3 aggregators down triggers safety mode

# Check which are healthy
kubectl get pods -n mohawk | grep aggregator

# Restart unhealthy aggregators
kubectl delete pod aggregator-2 -n mohawk

# Monitor consensus
kubectl logs -f deployment/mohawk-core -n mohawk | grep consensus
```

### Byzantine detected
```bash
# If consensus detects >1/3 malicious:
kubectl logs deployment/mohawk-core -n mohawk | grep "byzantine"

# This triggers safety - consensus pauses
# To recover:

# 1. Identify malicious nodes
# 2. Remove them
# 3. Restart aggregators
kubectl scale deployment mohawk-core --replicas=0 -n mohawk
kubectl scale deployment mohawk-core --replicas=3 -n mohawk
```

## Database Issues

### PostgreSQL connection fails
```bash
# Check PostgreSQL pod
kubectl get pods -n mohawk | grep postgres

# Check logs
kubectl logs pod/postgresql-0 -n mohawk

# Port forward and test
kubectl port-forward pod/postgresql-0 5432:5432 -n mohawk
psql -h localhost -U postgres -d mohawk
```

### Out of disk space
```bash
# Check PVC usage
kubectl get pvc -n mohawk

# Increase PVC size
kubectl patch pvc postgres-data -n mohawk -p \
  '{"spec":{"resources":{"requests":{"storage":"100Gi"}}}}'

# Or add new disk
# kubectl apply -f k8s/pvc-extra.yaml
```

## Monitoring Issues

### Prometheus not scraping metrics
```bash
# Check Prometheus targets
kubectl port-forward svc/prometheus 9090:9090 -n mohawk
# Visit http://localhost:9090/targets

# Check ServiceMonitor
kubectl get servicemonitor -n mohawk

# Apply monitor
kubectl apply -f k8s/servicemonitor.yaml
```

### Grafana dashboards empty
```bash
# Check Grafana logs
kubectl logs deployment/grafana -n mohawk

# Verify Prometheus datasource
kubectl port-forward svc/grafana 3000:3000 -n mohawk
# Visit http://localhost:3000
# Configuration > Data Sources > Check Prometheus

# Restart Grafana
kubectl rollout restart deployment/grafana -n mohawk
```

## Common Errors & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `imagePullBackOff` | Image not found | Build & push image, or use correct tag |
| `pending` | Not enough resources | Add nodes or scale down other pods |
| `OOMKilled` | Out of memory | Increase memory limit, scale aggregators |
| `connection refused` | Service not running | Check pod status, restart if needed |
| `timeout` | Consensus taking too long | Check node count, increase timeout |
| `proof failed` | zk-SNARK error | Check crypto version, restart nodes |

## FAQ

**Q: How do I see logs from all pods?**
```bash
kubectl logs -f -l app=mohawk-core -n mohawk
```

**Q: How do I scale to more nodes?**
```bash
kubectl scale deployment mohawk-core --replicas=10 -n mohawk
```

**Q: How do I check if consensus is working?**
```bash
kubectl logs deployment/mohawk-core -n mohawk | grep "consensus_round"
```

**Q: How do I reset everything?**
```bash
kubectl delete namespace mohawk
kubectl create namespace mohawk
kubectl apply -f k8s/ -n mohawk
```

**Q: How do I enable debug logging?**
```bash
kubectl set env deployment/mohawk-core DEBUG=true -n mohawk
kubectl rollout restart deployment/mohawk-core -n mohawk
```

See [`docs/README.md`](README.md) for more documentation.

---

[← Back to Docs Index](README.md)

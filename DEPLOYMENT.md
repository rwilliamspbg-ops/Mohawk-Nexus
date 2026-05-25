# Mohawk Nexus: Deployment guide (local dev + k8s)

This document outlines how to run a minimal full-stack deployment locally with Docker Compose and a skeleton Kubernetes deployment for production.

Prerequisites
- Docker & Docker Compose (for local dev)
- kubectl + a Kubernetes cluster (for production)
- Go 1.26.1 (pinned)
- Rust toolchain (for building datapath)
- Host NIC/kernel prerequisites for AF_XDP if using the high-performance datapath

Local (Docker Compose)

1. Build images and bring stack up

```bash
docker compose build
docker compose up -d
```

2. Services
- `control` - Go control plane (exposes 8080)
- `datapath` - Rust datapath
- `fl-coordinator` - placeholder FL coordinator (HTTP server 9000)
- `swip-client` - placeholder SWIP client

Kubernetes (skeleton)

Apply namespace and deployments:

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/control-deployment.yaml
kubectl apply -f k8s/datapath-deployment.yaml
kubectl apply -f k8s/fl-deployment.yaml
kubectl apply -f k8s/swip-deployment.yaml
```

Notes and next steps
- Replace placeholder FL and SWIP images with real service images (coordinator, clients, training jobs).
- For production, create NetworkPolicy, Service, Ingress, TLS secrets, and node affinity to schedule datapath on NIC-enabled nodes.
- Add Helm charts and CI image builds + pushed container registry for reproducible deployments.

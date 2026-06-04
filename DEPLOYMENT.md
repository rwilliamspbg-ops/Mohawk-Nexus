# Mohawk Nexus: Deployment guide (local dev + k8s)

This document outlines how to run a minimal full-stack deployment locally with Docker Compose and a skeleton Kubernetes deployment for production.

Prerequisites
- Docker & Docker Compose (for local dev)
- kubectl + a Kubernetes cluster (for production)
- Go 1.26.1 (pinned)
- Rust toolchain (for building datapath)
- Host NIC/kernel prerequisites for AF_XDP if using the high-performance datapath

Deployment profiles

- `portable`: cross-device mode for broad compatibility (control + FL + SWIP, no privileged datapath requirement).
- `accelerated`: Linux AF_XDP mode with privileged datapath.
- `experimental-nonpriv`: non-privileged datapath trial mode for compatibility testing only.

Local (Docker Compose)

1. Build images and bring stack up

```bash
docker compose build
docker compose up -d
```

2. Services
- `control` - Go control plane (exposes 8080)
- `datapath` - Rust datapath
- `fl-coordinator` - FL coordinator (API 9000, metrics 9001)
- `swip-client` - SWIP service (API 9100, metrics 9101)

Kubernetes (skeleton)

Apply namespace and deployments:

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/control-deployment.yaml
kubectl apply -f k8s/datapath-deployment.yaml
kubectl apply -f k8s/fl-deployment.yaml
kubectl apply -f k8s/swip-deployment.yaml
```

Portable mode (recommended for broad device coverage)

This mode avoids privileged datapath requirements and runs on most Kubernetes environments.

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/control-deployment.yaml
kubectl apply -f k8s/fl-deployment.yaml
kubectl apply -f k8s/swip-deployment.yaml
```

Accelerated mode (Linux AF_XDP)

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/control-deployment.yaml
kubectl apply -f k8s/datapath-deployment.yaml
kubectl apply -f k8s/fl-deployment.yaml
kubectl apply -f k8s/swip-deployment.yaml
```

Experimental non-privileged datapath mode

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/control-deployment.yaml
kubectl apply -f k8s/datapath-deployment-unprivileged.yaml
kubectl apply -f k8s/fl-deployment.yaml
kubectl apply -f k8s/swip-deployment.yaml
```

Note: `datapath-deployment-unprivileged.yaml` is intended for compatibility testing and may not provide AF_XDP throughput characteristics.

Notes and next steps
- For production, create NetworkPolicy, Service, Ingress, TLS secrets, and node affinity to schedule datapath on NIC-enabled nodes.
- Add Helm charts and CI image builds + pushed container registry for reproducible deployments.

Images published by CI are available at:

- `ghcr.io/rwilliamspbg-ops/mohawk-control:latest`
- `ghcr.io/rwilliamspbg-ops/mohawk-datapath:latest`
- `ghcr.io/rwilliamspbg-ops/mohawk-fl:latest`
- `ghcr.io/rwilliamspbg-ops/mohawk-swip:latest`

You can update `k8s/*-deployment.yaml` to reference GHCR images or use the local images built via `docker compose build`.

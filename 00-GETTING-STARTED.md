# Getting Started with Mohawk Nexus

**Complete your first Mohawk Nexus setup in 10 minutes.**

## What is Mohawk Nexus?

Mohawk Nexus is a **formally verified, Byzantine-tolerant sovereign federated intelligence layer** for planetary-scale collective learning without centralized data aggregation.

Key points:
- **Decentralized**: No central data repository. Nodes train locally.
- **Verified**: Mathematically proven correctness (Lean4 formal proofs)
- **Sovereign**: Policy-gated domains (HIPAA, GDPR, custom rules)
- **Scalable**: 10M–100M+ nodes with 224x memory reduction
- **Trustworthy**: Hardware-rooted attestation, post-quantum cryptography

## Key Features

| Feature | Benefit |
|---------|---------|
| **Mohawk Protocol** | 224x memory reduction for federated learning |
| **zk-SNARKs** | <10ms verification of node updates |
| **Byzantine Consensus** | Tolerates 1/3 malicious nodes |
| **Formal Verification** | Lean4 proofs of correctness |
| **Hardware Attestation** | TPM 2.0, XMSS, post-quantum (x25519-mlkem768) |
| **Policy Gating** | HIPAA/GDPR compliance automation |

## Prerequisites

### For Local Development (Docker recommended)
- Docker & Docker Compose
- ~4GB RAM, 10GB disk

### For Manual Setup
- **Go 1.21+** (for core runtime)
- **Python 3.11+** (for FL stack)
- **Node.js 20+** (for verticals)
- **Git**

### For Kubernetes Deployment
- kubectl 1.24+
- Kubernetes cluster (minikube, EKS, GKE, AKS)
- Helm 3+ (optional)

## Installation

### Option 1: Docker (Fastest - 2 minutes)

```bash
# Clone repository
git clone https://github.com/rwilliamspbg-ops/Mohawk-Nexus.git
cd Mohawk-Nexus

# Start with Docker Compose
docker-compose -f docker/docker-compose.yml up -d

# Watch logs
docker-compose logs -f

# Verify (should see running containers)
docker ps | grep mohawk
```

**Next**: Run `docker-compose logs -f` to see status

### Option 2: Manual Setup (All Components - 10 minutes)

```bash
# Clone
git clone https://github.com/rwilliamspbg-ops/Mohawk-Nexus.git
cd Mohawk-Nexus

# Run setup script
chmod +x scripts/setup.sh
./scripts/setup.sh

# This will:
# ✓ Check prerequisites
# ✓ Install Go dependencies
# ✓ Install Python packages
# ✓ Install Node packages
# ✓ Run basic tests
```

### Option 3: Kubernetes (Production - 15 minutes)

```bash
# Ensure kubectl configured
kubectl cluster-info

# Apply Kubernetes manifests
kubectl create namespace mohawk
kubectl apply -f k8s/ -n mohawk

# Watch rollout
kubectl rollout status deployment/mohawk-core -n mohawk

# Port forward to access
kubectl port-forward -n mohawk svc/mohawk-core 8080:8080

# Test
curl http://localhost:8080/health
```

## First Test (5 minutes)

### Run All Tests
```bash
# Using script (recommended)
./scripts/test.sh

# Or manually
cd modules/core/sovereign-mohawk-proto
go test ./...

cd ../../orchestration/python-sdk
pytest tests/

cd ../../verticals/oncology
npm test
```

### Expected Output
```
✓ Core runtime tests pass
✓ Python SDK tests pass
✓ Oncology vertical tests pass
✓ All module tests pass
```

## Quick Start Examples

### Example 1: Local Development (Docker)

```bash
cd Mohawk-Nexus

# Start dev environment
docker-compose -f docker/docker-compose.yml up -d

# Access containers
docker-compose exec core bash                    # Core runtime
docker-compose exec fl bash                      # FL stack
docker-compose exec dev bash                     # Dev environment

# View logs
docker-compose logs -f core
docker-compose logs -f fl

# Stop
docker-compose down
```

### Example 2: Run Core Runtime

```bash
cd modules/core/sovereign-mohawk-proto

# Build
go build -o node-agent ./cmd/node-agent

# Run
./node-agent --config ../../config/development.yaml

# Test
go test ./... -v
```

### Example 3: Run Python FL Stack

```bash
cd modules/orchestration/python-sdk

# Install
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Use SDK
python -c "
import mohawk
client = mohawk.Client()
print(client.version())
"
```

### Example 4: Deploy Oncology Vertical

```bash
cd modules/verticals/oncology

# Install
npm install

# Run locally
npm run dev

# Build Docker image
docker build -t mohawk-oncology .
docker run -d mohawk-oncology

# Deploy to K8s
kubectl apply -f k8s/
```

## Project Structure

```
Mohawk-Nexus/
├── README.md                  ← Main overview
├── docs/                      ← This documentation
│   ├── 00-GETTING-STARTED.md  (you are here)
│   ├── 01-ARCHITECTURE.md
│   ├── 02-DEPLOYMENT.md
│   └── ...
├── modules/                   ← Code
│   ├── core/                  Core runtime
│   ├── orchestration/         FL orchestration
│   ├── verticals/             Domain applications
│   └── infrastructure/        Supporting systems
├── docker/                    ← Container setup
├── k8s/                       ← Kubernetes setup
├── scripts/                   ← Automation
├── examples/                  ← Usage examples
└── config/                    ← Configuration
```

See [`docs/README.md`](README.md) for full documentation index.

## Next Steps

### Path 1: Understand the System (20 min)
1. Read [`01-ARCHITECTURE.md`](01-ARCHITECTURE.md)
2. Explore [`modules/`](../modules/)
3. Check [`docs/README.md`](README.md) for more

### Path 2: Deploy to Production (30 min)
1. Read [`02-DEPLOYMENT.md`](02-DEPLOYMENT.md)
2. Follow Kubernetes section
3. Configure using [`config/`](../config/)

### Path 3: Start Contributing (45 min)
1. Read [`03-CONTRIBUTING.md`](03-CONTRIBUTING.md)
2. Pick a module in [`modules/`](../modules/)
3. Submit a pull request

### Path 4: Run Complete Example (15 min)
1. Follow Option 1 (Docker) above
2. Run [`examples/`](../examples/)
3. Explore [`modules/verticals/`](../modules/verticals/)

## Common Tasks

### "How do I run just the core runtime?"
```bash
cd modules/core/sovereign-mohawk-proto
go build ./cmd/node-agent
./node-agent --config ../../config/development.yaml
```

### "How do I use the Python SDK?"
```bash
cd modules/orchestration/python-sdk
pip install -r requirements.txt
python -m mohawk.orchestrator --help
```

### "How do I deploy a vertical (e.g., oncology)?"
```bash
cd modules/verticals/oncology
npm install
npm run deploy  # or npm start for local dev
```

### "How do I run tests?"
```bash
# All tests
./scripts/test.sh

# Specific module
cd modules/verticals/oncology
npm test
```

### "How do I build Docker images?"
```bash
# Build all
./scripts/build-images.sh

# Or individual
docker build -f docker/Dockerfile.core -t mohawk-core .
docker build -f docker/Dockerfile.fl -t mohawk-fl .
```

### "How do I deploy to Kubernetes?"
```bash
kubectl create namespace mohawk
kubectl apply -f k8s/ -n mohawk
kubectl get pods -n mohawk
```

## Environment Variables

Create a `.env` file (see `.env.example`):

```bash
# GitHub (for CI/CD)
GITHUB_TOKEN=ghp_your_token
GITHUB_ACTOR=your_username

# Docker Registry
DOCKER_REGISTRY=docker.io
DOCKER_USERNAME=your_username
DOCKER_PASSWORD=your_password

# Kubernetes (if deploying)
KUBE_CLUSTER=your-cluster-name
KUBE_REGION=us-east-1

# Development
LOG_LEVEL=debug
RUST_BACKTRACE=1
```

## Troubleshooting

### "Docker not installed"
```bash
# Install Docker Desktop from https://docker.com/download
# Then verify
docker --version
docker-compose --version
```

### "Go version too old"
```bash
# Install Go 1.21+ from https://golang.org/dl
# Then verify
go version  # Should be 1.21+
```

### "Tests failing"
```bash
# See TROUBLESHOOTING.md for detailed solutions
cat docs/05-TROUBLESHOOTING.md

# Or run individual tests with verbose output
./scripts/test.sh -v
```

### "Permission denied on scripts"
```bash
# Make scripts executable
chmod +x scripts/*.sh
./scripts/setup.sh
```

## Support

- **Docs**: [`docs/README.md`](README.md)
- **Architecture**: [`01-ARCHITECTURE.md`](01-ARCHITECTURE.md)
- **Issues**: GitHub Issues (tag by module)
- **Security**: security@mohawk-nexus.org

## What's Next?

Choose your path:

- **Understand**: Read [`01-ARCHITECTURE.md`](01-ARCHITECTURE.md)
- **Deploy**: Follow [`02-DEPLOYMENT.md`](02-DEPLOYMENT.md)
- **Develop**: See [`03-CONTRIBUTING.md`](03-CONTRIBUTING.md)
- **Use SDK**: Check [`04-API-REFERENCE.md`](04-API-REFERENCE.md)
- **Debug**: Consult [`05-TROUBLESHOOTING.md`](05-TROUBLESHOOTING.md)

---

**Congratulations! You've completed the Getting Started guide. 🎉**

**Next**: Pick one of the "What's Next" options above and continue.

# Mohawk Nexus

**A formally verified, Byzantine-tolerant sovereign federated intelligence layer for planetary-scale collective learning without centralized data aggregation or trust in intermediaries.**

## 🚀 Quick Navigation

- **New to the project?** → Start with [`docs/00-GETTING-STARTED.md`](docs/00-GETTING-STARTED.md)
- **Want to understand the architecture?** → See [`docs/01-ARCHITECTURE.md`](docs/01-ARCHITECTURE.md)
- **Ready to deploy?** → Follow [`docs/02-DEPLOYMENT.md`](docs/02-DEPLOYMENT.md)
- **Want to contribute?** → Read [`docs/03-CONTRIBUTING.md`](docs/03-CONTRIBUTING.md)
- **Full documentation index?** → Check [`docs/README.md`](docs/README.md)

## 📋 Project Overview

Mohawk Nexus implements a **decentralized, mathematically enforceable global intelligence layer** that prioritizes sovereignty, verifiability, and real-world utility over data monopolies.

### Core Capabilities

| Feature | Value | Impact |
|---------|-------|--------|
| **Memory Reduction** | 224x | vs centralized federated learning |
| **Verification Speed** | <10ms | zk-SNARK proofs |
| **Node Scaling** | 10M–100M+ | Edge-first architecture |
| **Trust Model** | Hardware-rooted | TPM 2.0, XMSS, post-quantum |
| **Consensus** | Byzantine-tolerant | Formally verified (Lean4) |
| **Cryptography** | Post-quantum ready | x25519-mlkem768 hybrid |

## 🏗️ Repository Structure

```
Mohawk-Nexus/
│
├── README.md                          ← You are here
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                     ← CI/CD pipeline
│   │   └── deploy.yml                 ← Deployment automation
│   └── CODEOWNERS                     ← Module ownership
│
├── docs/                              ← COMPLETE DOCUMENTATION
│   ├── README.md                      ← Documentation index
│   ├── 00-GETTING-STARTED.md         ← First steps
│   ├── 01-ARCHITECTURE.md            ← System design
│   ├── 02-DEPLOYMENT.md              ← Deployment guide
│   ├── 03-CONTRIBUTING.md            ← Contributing guide
│   ├── 04-API-REFERENCE.md           ← API documentation
│   ├── 05-TROUBLESHOOTING.md         ← Debugging guide
│   ├── 06-SECURITY.md                ← Security policies
│   ├── 07-ROADMAP.md                 ← Feature roadmap
│   └── images/                        ← Architecture diagrams
│
├── modules/                           ← CONSOLIDATED MODULES
│   │
│   ├── core/                          ← Core Runtime
│   │   ├── sovereign-mohawk-proto/    ← Main consensus engine
│   │   ├── formal-verification/       ← Lean4 proofs
│   │   └── cryptography/              ← Crypto primitives
│   │
│   ├── orchestration/                 ← Orchestration Layer
│   │   ├── sovereign-map-v2/          ← Policy-gated orchestrator
│   │   └── python-sdk/                ← Python federated learning SDK
│   │
│   ├── verticals/                     ← Domain Applications
│   │   ├── oncology/                  ← Healthcare (HIPAA/GDPR)
│   │   ├── agriculture/               ← Farming & sustainability
│   │   ├── climate/                   ← Environmental intelligence
│   │   └── supply-chain/              ← Logistics optimization
│   │
│   ├── infrastructure/                ← Supporting Systems
│   │   ├── autonomous-mapping/        ← ZK-biometric identity
│   │   ├── nvflare/                   ← NVIDIA FL framework
│   │   ├── flower/                    ← Friendly FL framework
│   │   ├── therock/                   ← GPU acceleration (ROCm)
│   │   └── ethhub/                    ← Ethereum integration
│   │
│   └── website/                       ← Documentation Site
│       └── sovereign-map-website/     ← Web frontend
│
├── docker/                            ← CONTAINERIZATION
│   ├── Dockerfile.core                ← Core runtime image
│   ├── Dockerfile.fl                  ← FL stack image
│   ├── docker-compose.yml             ← Local development
│   └── Dockerfile.dev                 ← Development environment
│
├── k8s/                               ← KUBERNETES
│   ├── deployment.yaml                ← Aggregator deployment
│   ├── service.yaml                   ← Service definitions
│   ├── configmap.yaml                 ← Configuration
│   ├── statefulset.yaml               ← Stateful components
│   └── kustomization.yaml             ← Kustomize base
│
├── scripts/                           ← AUTOMATION
│   ├── setup.sh                       ← Initial setup
│   ├── test.sh                        ← Run all tests
│   ├── build-images.sh                ← Build Docker images
│   ├── deploy.sh                      ← Deploy to Kubernetes
│   └── init-repo.sh                   ← Repository initialization
│
├── examples/                          ← USAGE EXAMPLES
│   ├── local-development.md           ← Local setup
│   ├── docker-compose-prod.yml        ← Production Docker setup
│   ├── kubernetes-production.yaml     ← Production K8s setup
│   └── client-library/                ← SDK examples
│
├── config/                            ← CONFIGURATION
│   ├── default.yaml                   ← Default configuration
│   ├── production.yaml                ← Production settings
│   └── development.yaml               ← Development settings
│
└── .gitignore                         ← Git ignore rules
```

## 🎯 Key Modules (13 Consolidated)

### Core Runtime
- **Sovereign-Mohawk-Proto** — Byzantine consensus, Mohawk Protocol, zk-SNARKs (Go, Lean4)

### Orchestration
- **Sovereign-Map-V2** — Policy-gated domain management (TypeScript)
- **Sovereign-Map-FL** — Python federated learning SDK with observability (Python)

### Verticals (Policy-Gated Domains)
- **Oncology** — HIPAA/GDPR healthcare AI (Python, Flower)
- **Agriculture** — Farmer-sovereign sustainability (JavaScript)
- **Climate** — Nation-sovereign carbon tracking (JavaScript)
- **Supply Chain** — Enterprise disruption prediction (JavaScript)

### Infrastructure
- **Autonomous-Mapping** — ZK-biometric identity, ORB-SLAM3 (TypeScript)
- **NVFlare** — NVIDIA federated learning runtime (Python)
- **Flower** — Friendly federated learning framework (Python)
- **TheRock** — HIP/ROCm GPU acceleration (Python)
- **EthHub** — Ethereum integration reference
- **Sovereign-Map-Website** — Documentation site (HTML/Jekyll)

## 🔐 Security & Verification

- **Formally Verified**: Lean4 proofs for consensus correctness
- **Hardware-Rooted Trust**: TPM 2.0 attestation + XMSS signatures
- **Post-Quantum Ready**: x25519-mlkem768 hybrid key exchange
- **Zero-Knowledge Proofs**: zk-SNARKs for computation verification
- **Byzantine Resilient**: Consensus tolerable to 1/3 malicious nodes

## 📖 Documentation Structure

All documentation is organized in `docs/` with clear progression:

1. **00-GETTING-STARTED.md** — First steps, quick start, prerequisites
2. **01-ARCHITECTURE.md** — System design, trust boundaries, components
3. **02-DEPLOYMENT.md** — Docker, Kubernetes, production setup
4. **03-CONTRIBUTING.md** — Workflow, standards, code style
5. **04-API-REFERENCE.md** — API docs, SDK usage
6. **05-TROUBLESHOOTING.md** — Common issues & solutions
7. **06-SECURITY.md** — Security policies, best practices
8. **07-ROADMAP.md** — Future features, milestones

See [`docs/README.md`](docs/README.md) for full documentation index.

## 🚀 Quick Start (5 minutes)

### Prerequisites
```bash
- Git
- Docker & Docker Compose (for easy setup)
- OR: Go 1.21+, Python 3.11+, Node.js 20+
```

### Local Development
```bash
# Clone
git clone https://github.com/rwilliamspbg-ops/Mohawk-Nexus.git
cd Mohawk-Nexus

# Setup (choose one)

# Option 1: Docker (Easiest)
docker-compose -f docker/docker-compose.yml up -d
docker-compose logs -f

# Option 2: Manual
./scripts/setup.sh
./scripts/test.sh

# Option 3: Kubernetes
kubectl apply -f k8s/
kubectl get pods
```

### First Tests
```bash
# Run all tests
./scripts/test.sh

# Or individual modules
cd modules/core/sovereign-mohawk-proto
go test ./...
```

## 📚 Next Steps

- **Explore modules**: `cd modules/` and pick a vertical or core component
- **Run tests**: `./scripts/test.sh`
- **Read docs**: Start with [`docs/00-GETTING-STARTED.md`](docs/00-GETTING-STARTED.md)
- **Contribute**: Follow [`docs/03-CONTRIBUTING.md`](docs/03-CONTRIBUTING.md)
- **Deploy**: See [`docs/02-DEPLOYMENT.md`](docs/02-DEPLOYMENT.md)

## 🤝 Contributing

We welcome contributions! Please:

1. Read [`docs/03-CONTRIBUTING.md`](docs/03-CONTRIBUTING.md)
2. Follow code standards in that guide
3. Include tests for new features
4. Submit a pull request with detailed description

## 📄 License

- **Core Runtime**: Apache 2.0
- **Verticals**: MIT
- **Dependencies**: Respect upstream licenses

## 🔗 Resources

- **Documentation**: [`docs/README.md`](docs/README.md)
- **Issues**: GitHub Issues (tag by module)
- **Discussions**: GitHub Discussions for RFCs
- **Security**: security@mohawk-nexus.org (responsible disclosure)

---

**Built with sovereignty, verified with mathematics, operated by edges, owned by none.**

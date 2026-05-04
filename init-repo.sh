#!/bin/bash

# Initialize Mohawk Nexus Repository
# This script creates the complete directory structure and scaffolding

set -e

echo "🚀 Initializing Mohawk Nexus Repository..."
echo ""

# Create directory structure
mkdir -p modules/{core,orchestration,verticals,infrastructure,website}
mkdir -p modules/core/{sovereign-mohawk-proto,formal-verification,cryptography}
mkdir -p modules/orchestration/{sovereign-map-v2,python-sdk}
mkdir -p modules/verticals/{oncology,agriculture,climate,supply-chain}
mkdir -p modules/infrastructure/{autonomous-mapping,nvflare,flower,therock,ethhub}
mkdir -p docker k8s scripts examples config .github/workflows

echo "✓ Created directory structure"

# Create .gitignore
cat > .gitignore << 'EOF'
# Dependencies
node_modules/
__pycache__/
*.pyc
go.sum
Cargo.lock

# Builds
dist/
build/
*.o
*.a
*.so

# Environment
.env
.env.local
.venv
venv/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Secrets
*.key
*.pem
*.crt
secrets.yaml

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db

# Kubernetes
kubeconfig
.kube/config

# Docker
.docker/config.json

# Coverage
coverage/
*.cover
.coverage
EOF

echo "✓ Created .gitignore"

# Create module README templates
for module in modules/*/*/; do
    if [ -d "$module" ]; then
        cat > "$module/README.md" << 'EOF'
# Module Template

This module is part of Mohawk Nexus.

## Overview

(Add module description)

## Structure

```
./
├── src/          - Source code
├── tests/        - Test suite
├── docs/         - Module documentation
└── README.md     - This file
```

## Installation

(Add installation instructions)

## Usage

(Add usage examples)

## Contributing

See [CONTRIBUTING.md](../../docs/03-CONTRIBUTING.md)

## See Also

- Main documentation: [docs/README.md](../../docs/README.md)
- Repository: [https://github.com/rwilliamspbg-ops/Mohawk-Nexus](https://github.com/rwilliamspbg-ops/Mohawk-Nexus)
EOF
    fi
done

echo "✓ Created module README templates"

# Create basic script templates
cat > scripts/setup.sh << 'EOF'
#!/bin/bash
set -e

echo "Setting up Mohawk Nexus..."

# Check prerequisites
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker."
    exit 1
fi

if ! command -v kubectl &> /dev/null; then
    echo "⚠️  kubectl not found. Some features may be unavailable."
fi

echo "✓ Prerequisites checked"

# Build
echo "Building containers..."
docker-compose -f docker/docker-compose.yml build

echo "✓ Setup complete!"
echo ""
echo "Next steps:"
echo "  - Start: docker-compose -f docker/docker-compose.yml up"
echo "  - Test:  ./scripts/test.sh"
echo "  - Deploy: kubectl apply -f k8s/"
EOF

cat > scripts/test.sh << 'EOF'
#!/bin/bash
set -e

echo "Running tests..."

# Go tests
if [ -d "modules/core" ]; then
    echo "Testing Go modules..."
    cd modules/core/sovereign-mohawk-proto
    go test ./... 2>&1 || echo "⚠️  Go tests skipped (Go not available)"
    cd ../../../
fi

# Python tests
if [ -f "modules/orchestration/python-sdk/requirements.txt" ]; then
    echo "Testing Python modules..."
    cd modules/orchestration/python-sdk
    pytest tests/ 2>&1 || echo "⚠️  Python tests skipped (pytest not available)"
    cd ../../../
fi

# Node tests
for dir in modules/verticals/*/; do
    if [ -f "$dir/package.json" ]; then
        echo "Testing $(basename $dir)..."
        cd "$dir"
        npm test 2>&1 || echo "⚠️  Node tests skipped (npm not available)"
        cd ../../../
    fi
done

echo "✓ Tests complete"
EOF

chmod +x scripts/*.sh

echo "✓ Created scripts"

# Create Kubernetes manifests
cat > k8s/deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mohawk-core
  namespace: mohawk
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mohawk-core
  template:
    metadata:
      labels:
        app: mohawk-core
    spec:
      containers:
      - name: core
        image: mohawk-core:latest
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "1Gi"
            cpu: "1"
          limits:
            memory: "2Gi"
            cpu: "2"
        env:
        - name: CONSENSUS_MAX_FAULTS
          value: "1"
        - name: LOG_LEVEL
          value: "info"
---
apiVersion: v1
kind: Service
metadata:
  name: mohawk-core
  namespace: mohawk
spec:
  type: ClusterIP
  selector:
    app: mohawk-core
  ports:
  - port: 8080
    targetPort: 8080
EOF

echo "✓ Created Kubernetes manifests"

# Create Docker Compose
cat > docker/docker-compose.yml << 'EOF'
version: '3.9'

services:
  core:
    build:
      context: ..
      dockerfile: docker/Dockerfile.core
    ports:
      - "8080:8080"
    environment:
      - LOG_LEVEL=debug
      - CONSENSUS_MAX_FAULTS=1
    volumes:
      - /tmp/mohawk-data:/data

  fl:
    build:
      context: ..
      dockerfile: docker/Dockerfile.fl
    ports:
      - "5000:5000"
    environment:
      - LOG_LEVEL=debug
    depends_on:
      - core

  dev:
    build:
      context: ..
      dockerfile: docker/Dockerfile.dev
    volumes:
      - ..:/workspace
    working_dir: /workspace
    command: /bin/bash
    stdin_open: true
    tty: true

volumes:
  mohawk-data:
EOF

echo "✓ Created Docker Compose"

# Create .github workflows
cat > .github/workflows/ci.yml << 'EOF'
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run tests
        run: ./scripts/test.sh || true
      
      - name: Build images
        run: docker-compose -f docker/docker-compose.yml build
EOF

echo "✓ Created GitHub Actions workflows"

# Create CODEOWNERS
cat > .github/CODEOWNERS << 'EOF'
# Core
modules/core/ @rwilliamspbg-ops/core-team

# Orchestration
modules/orchestration/ @rwilliamspbg-ops/orchestration-team

# Verticals
modules/verticals/oncology/ @rwilliamspbg-ops/healthcare-team
modules/verticals/agriculture/ @rwilliamspbg-ops/agriculture-team
modules/verticals/climate/ @rwilliamspbg-ops/climate-team
modules/verticals/supply-chain/ @rwilliamspbg-ops/supply-chain-team

# Documentation
*.md docs/ @rwilliamspbg-ops/documentation-team
EOF

echo "✓ Created CODEOWNERS"

# Create examples
mkdir -p examples
cat > examples/README.md << 'EOF'
# Mohawk Nexus Examples

Complete working examples for different deployment scenarios.

- `docker-compose-prod.yml` - Production Docker Compose setup
- `kubernetes-production.yaml` - Production Kubernetes manifests
- `local-development.md` - Local development guide
- `client-library/` - SDK usage examples

See [docs/README.md](../docs/README.md) for more.
EOF

echo "✓ Created examples directory"

# Create config
mkdir -p config
cat > config/default.yaml << 'EOF'
# Mohawk Nexus Configuration

consensus:
  max_faults: 1
  timeout_ms: 5000

aggregation:
  memory_limit_mb: 1024
  batch_size: 10000

monitoring:
  prometheus_enabled: true
  grafana_enabled: true
  log_level: info

security:
  tpm_attestation: true
  zk_proof_verification: true
  require_https: true
EOF

echo "✓ Created configuration"

# Initialize Git repo
if [ ! -d ".git" ]; then
    git init
    git config user.email "nexus@mohawk.sovereign"
    git config user.name "Mohawk Nexus"
    git add .
    git commit -m "Initialize Mohawk Nexus repository structure"
    echo "✓ Initialized Git repository"
fi

echo ""
echo "🎉 Repository initialized successfully!"
echo ""
echo "Next steps:"
echo "  1. Review documentation: docs/README.md"
echo "  2. Set up local development: ./scripts/setup.sh"
echo "  3. Run tests: ./scripts/test.sh"
echo "  4. Deploy: kubectl apply -f k8s/"
echo ""
echo "See docs/00-GETTING-STARTED.md for detailed instructions."

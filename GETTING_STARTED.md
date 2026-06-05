# Getting Started

This guide gets a portable Mohawk Nexus stack running in about 5 minutes.

## 1. Prerequisites

- Docker + Docker Compose
- Python 3.11+
- Go 1.22+ (Go 1.26.1 recommended for CI parity)

## 2. Bootstrap the workspace

```bash
make setup
make status
```

## 3. Validate the bridge contract

```bash
make generate-bridge
make validate-bridge
make bridge-smoke
```

## 4. Run local FL demo services

```bash
docker-compose build fl-coordinator fl-client-1 fl-client-2
docker-compose up -d fl-coordinator fl-client-1 fl-client-2
docker-compose ps
```

## 5. Run verification tests

```bash
make test-all
```

## Optional: full workspace verification

```bash
make verify
```

## Common troubleshooting

- If Go is not found: install Go and ensure it is available in PATH.
- If Rust tests fail: install Rust toolchain with rustup.
- If Docker services fail to start: inspect logs with `docker-compose logs`.
- If bridge validation fails: regenerate and re-run `make validate-bridge`.

## Next reads

- README.md
- DEPLOYMENT.md
- SECURITY.md
- CONTRIBUTING.md

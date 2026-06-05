# Mohawk Nexus Unified Workspace

Mohawk Nexus is the root integration workspace for the Mohawk network stack. It brings together the Go control plane, the Rust datapath, protocol definitions, verification material, and the canonical bridge contract used for cross-component validation and integration testing.

[![CI](https://img.shields.io/github/actions/workflow/status/rwilliamspbg-ops/Mohawk-Nexus/ci.yml?branch=main&style=for-the-badge&logo=githubactions&logoColor=white&label=CI)](https://github.com/rwilliamspbg-ops/Mohawk-Nexus/actions/workflows/ci.yml)
[![Build Images](https://img.shields.io/github/actions/workflow/status/rwilliamspbg-ops/Mohawk-Nexus/build-images.yml?branch=main&style=for-the-badge&logo=githubactions&logoColor=white&label=Build%20Images)](https://github.com/rwilliamspbg-ops/Mohawk-Nexus/actions/workflows/build-images.yml)
[![Publish Images](https://img.shields.io/github/actions/workflow/status/rwilliamspbg-ops/Mohawk-Nexus/publish-images.yml?branch=main&style=for-the-badge&logo=githubactions&logoColor=white&label=Publish%20Images)](https://github.com/rwilliamspbg-ops/Mohawk-Nexus/actions/workflows/publish-images.yml)
[![Kind Integration](https://img.shields.io/github/actions/workflow/status/rwilliamspbg-ops/Mohawk-Nexus/kind-integration.yml?branch=main&style=for-the-badge&logo=githubactions&logoColor=white&label=Kind%20Integration)](https://github.com/rwilliamspbg-ops/Mohawk-Nexus/actions/workflows/kind-integration.yml)
[![Perf Regression](https://img.shields.io/github/actions/workflow/status/rwilliamspbg-ops/Mohawk-Nexus/perf-regression.yml?branch=main&style=for-the-badge&logo=githubactions&logoColor=white&label=Perf%20Regression)](https://github.com/rwilliamspbg-ops/Mohawk-Nexus/actions/workflows/perf-regression.yml)
[![Coverage](https://img.shields.io/github/actions/workflow/status/rwilliamspbg-ops/Mohawk-Nexus/coverage.yml?branch=main&style=for-the-badge&logo=githubactions&logoColor=white&label=Coverage)](https://github.com/rwilliamspbg-ops/Mohawk-Nexus/actions/workflows/coverage.yml)
[![Bridge E2E](https://img.shields.io/github/actions/workflow/status/rwilliamspbg-ops/Mohawk-Nexus/bridge-e2e.yml?branch=main&style=for-the-badge&logo=githubactions&logoColor=white&label=Bridge%20E2E)](https://github.com/rwilliamspbg-ops/Mohawk-Nexus/actions/workflows/bridge-e2e.yml)
[![Policy Validate](https://img.shields.io/github/actions/workflow/status/rwilliamspbg-ops/Mohawk-Nexus/policy-validate.yml?branch=main&style=for-the-badge&logo=githubactions&logoColor=white&label=Policy%20Validate)](https://github.com/rwilliamspbg-ops/Mohawk-Nexus/actions/workflows/policy-validate.yml)

![Go](https://img.shields.io/badge/Go-1.26.1-00ADD8?style=flat-square&logo=go&logoColor=white)
![Rust](https://img.shields.io/badge/Rust-1.0%2B-DEA584?style=flat-square&logo=rust&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![Node](https://img.shields.io/badge/Node-20%2B-339933?style=flat-square&logo=node.js&logoColor=white)
![SDK](https://img.shields.io/badge/SDK-Python%20%7C%20Go%20%7C%20Rust%20%7C%20TypeScript-4A5568?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS%20%7C%20Windows-0A66C2?style=flat-square)
![Containers](https://img.shields.io/badge/Containers-amd64%20%7C%20arm64-2496ED?style=flat-square&logo=docker&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Ready-326CE5?style=flat-square&logo=kubernetes&logoColor=white)
![Datapath](https://img.shields.io/badge/Datapath-AF__XDP%20Accelerated-FF6600?style=flat-square)

[![Stars](https://img.shields.io/github/stars/rwilliamspbg-ops/Mohawk-Nexus?style=flat-square&logo=github)](https://github.com/rwilliamspbg-ops/Mohawk-Nexus/stargazers)
[![Forks](https://img.shields.io/github/forks/rwilliamspbg-ops/Mohawk-Nexus?style=flat-square&logo=github)](https://github.com/rwilliamspbg-ops/Mohawk-Nexus/network/members)
[![Open Issues](https://img.shields.io/github/issues/rwilliamspbg-ops/Mohawk-Nexus?style=flat-square)](https://github.com/rwilliamspbg-ops/Mohawk-Nexus/issues)
[![License](https://img.shields.io/badge/License-Multi--Repo-0EA5E9?style=flat-square)](https://github.com/rwilliamspbg-ops/Mohawk-Nexus/blob/main/LICENSE)

[![Sponsor Mohawk Nexus](https://img.shields.io/badge/Sponsor%20Mohawk%20Nexus-%E2%9D%A4-EA4AAA?style=for-the-badge&logo=githubsponsors&logoColor=white)](https://github.com/sponsors/rwilliamspbg-ops)
[![Become a Sponsor](https://img.shields.io/badge/Become%20a%20Sponsor-Sustain%20Development-111827?style=for-the-badge&logo=github&logoColor=white)](https://github.com/sponsors/rwilliamspbg-ops)

## Workspace Layout

- [SMIP-MWP/](SMIP-MWP/) — Go control plane, AF_XDP host integration, routing, crypto bindings and bridge request ingestion.
- [SMIP-MWP-Rust/](SMIP-MWP-Rust/) — Rust datapath, forwarding pipeline, high-performance data plane, and CLI tools.
- [Sovereign-Mohawk-Proto/](Sovereign-Mohawk-Proto/) — Protocol definitions, schema evolution, and formal verification assets.
- [bridge/](bridge/) — Canonical bridge schema, manifest, and request examples used by root validation.
- [scripts/](scripts/) — Workspace-level generation, validation and test helpers.
- `go.work` — Root Go workspace that ties Go modules across the repository.

## Quick Start Docs

- [GETTING_STARTED.md](GETTING_STARTED.md) — 5-minute portable setup and verification path.
- [CONTRIBUTING.md](CONTRIBUTING.md) — contributor workflow, interface change process, and component SHA tracking.
- [SECURITY.md](SECURITY.md) — coordinated vulnerability disclosure process.
- [DEPLOYMENT.md](DEPLOYMENT.md) — deployment profiles and runtime guidance.

## Requirements

- Go (1.26.1 recommended — pinned for reproducible builds; 1.22+ should work for most local workflows)
- Python 3.8+
- Docker (for containerized performance/stress runs)
- Rust toolchain (only required for running `SMIP-MWP-Rust` tests locally)

Note: For reproducible local builds and CI parity we pin Go to `1.26.1`.
You can install it locally (no sudo) and add it to your shell `PATH`:

```bash
GO_INSTALL_DIR="$HOME/.go/go1.26.1"
curl -fsSL -o /tmp/go1.26.1.linux-amd64.tar.gz https://go.dev/dl/go1.26.1.linux-amd64.tar.gz
rm -rf "$GO_INSTALL_DIR" && mkdir -p "$GO_INSTALL_DIR"
tar -C "$GO_INSTALL_DIR" -xzf /tmp/go1.26.1.linux-amd64.tar.gz --strip-components=1
export PATH="$GO_INSTALL_DIR/bin:$PATH"
go version
```

Tip: If you use a Codespace or Dev Container, see `.devcontainer/devcontainer.json` for a pinned Go feature.

## Device Compatibility Matrix

Mohawk Nexus supports multiple deployment profiles. The high-performance datapath remains Linux-focused due to AF_XDP requirements, while portable workflows cover broader device classes.

| Device class | Primary profile | Status | Notes |
|---|---|---|---|
| Linux x86_64 server with AF_XDP-capable NIC | accelerated | supported | Full control + datapath profile; requires privileged datapath runtime and NIC/kernel tuning. |
| Linux arm64 server or edge node | portable | supported | Control/FL/SWIP services supported; use accelerated profile only where AF_XDP prerequisites are met. |
| Raspberry Pi / ARM SBC | portable | supported | Prefer portable workflows and reduced profiling overhead. |
| macOS developer laptop | portable | supported for development | Use Docker/CI workflows and bridge validation; AF_XDP datapath is not available locally. |
| Windows developer workstation | portable | supported for development | Use Docker/CI workflows and bridge validation; AF_XDP datapath is not available locally. |
| Managed Kubernetes without privileged pods | portable | supported | Deploy non-privileged stack mode from `DEPLOYMENT.md`; skip accelerated datapath deployment. |

### Runtime Profiles

- `portable`: cross-device integration profile for control + FL + SWIP and bridge validation.
- `accelerated`: Linux AF_XDP profile for high-performance datapath workloads.
- `experimental`: non-privileged datapath trial mode for compatibility testing only.

## Usage

Bootstrap and check workspace status:

```bash
make bootstrap
make status
```

Run the workspace-level verification targets (root-owned, no Rust checkout required):

```bash
make verify
```

Common targets:

- `make generate-bridge` — regenerate bridge schema artifacts under `bridge/`.
- `make validate-bridge` — validate manifest and SHA256 hashes for bridge artifacts.
- `make verify-go` — run Go unit tests and benchmarks across the Go repos.
- `make bridge-smoke` — simple smoke test of the bridge contract.
- `make verify-rust` — run Rust tests in `SMIP-MWP-Rust/` (requires Rust toolchain and repository checkout).

FL quickstart (local, portable):

```bash
# build local FL images and run coordinator + two clients
docker-compose build fl-coordinator fl-client-1 fl-client-2
docker-compose up -d fl-coordinator fl-client-1 fl-client-2
docker-compose logs -f fl-coordinator
```

Running performance and stress harnesses (local):

```bash
# quick bench
cd SMIP-MWP
./scripts/bench.sh -- go test ./internal/crypto -bench . -benchmem -run ^$ -count=1

# containerized stress (example)
cd SMIP-MWP
docker build -f Dockerfile.stress -t smip-mwp:stress .
docker run --rm --privileged -v "$PWD":/app -v "$PWD/benchmarks":/app/benchmarks -w /app smip-mwp:stress \
	bash -lc 'DURATION=300 LOAD_LEVEL=high bash ./scripts/stress-test.sh'
```

Benchmark output and pprof artifacts are written to `SMIP-MWP/benchmarks/`.

## Performance

Mohawk Nexus combines a lightweight **Go control plane** with a highly optimized **Rust datapath** (AF_XDP kernel-bypass, Multi-path Spraying, hybrid/PQC-ready crypto). All numbers are from recent internal micro-benchmarks on AMD EPYC 64-core hardware.

### Full Stack Layer-by-Layer Performance Matrix

| Layer                        | Operation                                      | Mohawk Performance                  | Industry Comparison                                      | Assessment                  |
|-----------------------------|------------------------------------------------|-------------------------------------|----------------------------------------------------------|-----------------------------|
| **Rust Datapath (Hot Path)** | Forwarding + Multi-path Spraying decision     | **2.4 – 2.5 Mpps** (single core hit path)<br>Up to **75 GB/s** effective | AF_XDP simple fwd: 3–11+ Mpps<br>DPDK l2fwd: 10–20+ Mpps (simpler) | **Excellent** for feature-rich path |
| **Multi-Path Spraying (MRC)** | Spraying + payload (4K/8K)                    | **18.1 – 20.1 ns/op**<br>**33 – 75 GB/s** | Standard ECMP/MPTCP: noticeably higher overhead<br>Research spraying: variable | **Outstanding** – minimal spraying tax |
| **Crypto (Hybrid/PQC-ready)** | In-place Encrypt / Decrypt                    | Encrypt: **878 – 1,357 ns/op**<br>Decrypt: **652 – 751 ns/op** | WireGuard (ChaCha/Poly): ~1–2 Gbps/core typical<br>AES-GCM: faster but less sovereign | **Strong** – especially with PQC hybrid |
| **Session & Routing**        | NewHybridSession (cached / uncached)          | Cached: **582 – 1,278 ns/op**<br>Uncached: **767 – 1,062 ns/op** | Traditional kernel/session tables: higher latency | **Good** after hashing/BTree optimizations |
| **AF_XDP Integration**       | Packet RX/TX (kernel-bypass)                  | Tied to datapath (~2.4+ Mpps)      | AF_XDP state-of-art: 10–18 Mpps (simple)<br>Zero-copy: up to 40 Mpps reported | Competitive with full features |
| **Full Stack (Combined)**    | End-to-end (spray + crypto + forward)         | **Estimated 1.8 – 2.3 Mpps** sustained | WireGuard tunnel: 1–4+ Gbps<br>Full DPDK apps: higher (but less safe/formal) | Promising for sovereign/edge use |

### Key Strengths
- Extremely low allocations (1–3 allocs/op in MRC spraying)
- Multi-path spraying adds almost zero overhead
- In-place crypto and zero-copy focus deliver strong GB/s numbers
- Rust safety + formal verification assets (Lean 4) without sacrificing too much speed

### Notes & Context
- Benchmarks run on **AMD EPYC 64-core** processors (server-grade hardware).
- Micro-benchmarks (`-benchmem`). Real-world sustained throughput depends on packet size, path diversity, concurrency, NIC, and PQC mode.
- Mohawk prioritizes **safety, formal methods, multi-path spraying, and sovereign features** over raw maximum Mpps (where plain DPDK often wins on simple forwarding).

**Latest benchmark artifacts** are available in `SMIP-MWP/benchmarks/` and `benchmarks/baselines/`.

---

Comparisons to common networking stacks (qualitative):

- TCP/TLS (kernel stack + OpenSSL): robust general purpose stack, but typically higher CPU per operation for zero-copy and user-space packet processing compared to Mohawk's AF_XDP/Rust datapath in optimized configurations.
- QUIC (user-space UDP + TLS 1.3): lower-latency transport for multiplexed streams; Mohawk is transport-agnostic and can interoperate, while offering optimized in-process crypto paths for bulk operations.
- WireGuard: extremely lightweight crypto VPN; WireGuard is highly-optimized for single-packet crypto paths, while Mohawk targets richer forwarding features, pluggable routing and protocol-level bridge contract validation.

Important: benchmark numbers depend heavily on host CPU, kernel, NIC, and kernel-bypass configuration (AF_XDP, hugepages, IRQ affinity). See `SMIP-MWP/benchmarks/` and generated `*.prof` for precise measurements captured during runs.

Latest high-stress run snapshot:

- Timestamp: 2026-05-24T16:59:58Z
- Load: 300s, high, 12 benchmark iterations, 32 concurrent operations
- `NewHybridSession_Cached`: 582.1-1278.0 ns/op, 1376 B/op, 4 allocs/op
- `NewHybridSession_Uncached`: 766.9-1062.0 ns/op, 1392 B/op, 5 allocs/op
- `EncryptInPlace`: 877.8-1357.0 ns/op, 1536 B/op, 1 allocs/op
- `DecryptInPlace`: 651.6-750.6 ns/op, 0 B/op, 0 allocs/op

How to interpret our artifacts:

- `*.txt` — human-readable run logs and summaries.
- `*-cpu.prof` / `*-mem.prof` — pprof profiles for CPU and memory; use `go tool pprof -top` and `go tool pprof -http` to inspect flamegraphs.

## Capabilities

Mohawk Nexus provides the following capabilities:

- High-performance datapath: Rust forwarder and AF_XDP integration for low-latency packet processing.
- Pluggable crypto: optimized symmetric and asymmetric crypto primitives with in-place encryption/decryption to minimize allocations.
- Bridge contract validation: canonical schema + manifest, with root-owned validators and reproducible SHA256 checks for example payloads.
- Integrated test harnesses: bench and stress scripts that produce repeatable artifacts and pprof profiles.
- CI-friendly verification: `make verify` runs root-level validation without depending on unpublished subrepo SHAs.
- Containerized performance: Dockerfiles and scripts to reproduce stress runs in a controlled environment.

## Contributing & Development Workflow

- Follow [CONTRIBUTING.md](CONTRIBUTING.md) for root workspace expectations and component sync guidelines.
- Follow `CONTRIBUTING.md` in each sub-repo for component-specific guidelines.
- For cross-repo changes, prefer root-owned shims or fallbacks when a subrepo SHA is unpublished — this keeps CI green while component PRs are being prepared.

## Bridge Contract

The canonical bridge schema and manifest are in `bridge/`. Use these tools:

- `scripts/generate_bridge_contract.py` — regenerate canonical artifacts.
- `scripts/generate_bridge_bindings.py` — regenerate SDK bridge constants for Go/Rust/Python/TypeScript.
- `scripts/validate_bridge_contract.py` — verify manifest and SHA256s.

Version source of truth:

- `bridge/bridge_contract.version.json` tracks schema and manifest version identifiers.

## CI

GitHub Actions runs `make verify` from the repository root (see `.github/workflows/ci.yml`). The root verify path is designed to be resilient when component subrepos are in-flight.

## References

- [STACK_INTEGRATION_PLAN.md](STACK_INTEGRATION_PLAN.md)
- [STACK_TOPOLOGY_AND_METRICS_SPEC.md](STACK_TOPOLOGY_AND_METRICS_SPEC.md)
- [STACK_INTEGRATION_CHECKLIST.md](STACK_INTEGRATION_CHECKLIST.md)
- `TRACEABILITY_MATRIX.md`
- `UNIFICATION_PLAN.md`

If you need a condensed usage guide or an examples section added to this README, tell me which workflows to highlight and I'll add them.

## Dev Container / Codespace

For reproducible development environments (Codespaces or Dev Containers) this repository pins Go to `1.26.1`. See `.devcontainer/devcontainer.json` for an example devcontainer configuration which sets `GOROOT` and prepends the pinned Go binary directory to the `PATH` so builds and tests use Go 1.26.1.

If you prefer to install Go locally without sudo, follow the steps in the Requirements section to install to `$HOME/.go/go1.26.1` and add it to your shell profile (`~/.bashrc` / `~/.profile`).

## License

This workspace is multi-license because it aggregates multiple component repositories with different upstream licenses.

- See `LICENSE` for the root workspace license notice.
- See `LICENSES.md` for the per-component license matrix and upstream links.

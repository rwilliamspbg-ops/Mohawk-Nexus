# Mohawk Nexus Unified Workspace

Mohawk Nexus is the root integration workspace for the Mohawk network stack. It brings together the Go control plane, the Rust datapath, protocol definitions, verification material, and the canonical bridge contract used for cross-component validation and integration testing.

## Workspace Layout

- [SMIP-MWP/](SMIP-MWP/) — Go control plane, AF_XDP host integration, routing, crypto bindings and bridge request ingestion.
- [SMIP-MWP-Rust/](SMIP-MWP-Rust/) — Rust datapath, forwarding pipeline, high-performance data plane, and CLI tools.
- [Sovereign-Mohawk-Proto/](Sovereign-Mohawk-Proto/) — Protocol definitions, schema evolution, and formal verification assets.
- [bridge/](bridge/) — Canonical bridge schema, manifest, and request examples used by root validation.
- [scripts/](scripts/) — Workspace-level generation, validation and test helpers.
- `go.work` — Root Go workspace that ties Go modules across the repository.

## Requirements

- Go (1.26+ recommended)
- Python 3.8+
- Docker (for containerized performance/stress runs)
- Rust toolchain (only required for running `SMIP-MWP-Rust` tests locally)

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

Overview: Mohawk targets a low-latency, high-throughput datapath by combining a lightweight Go control plane with a Rust-based datapath where tight loops and cryptography run. Performance tradeoffs and focal points:

- Throughput: optimized datapath and crypto primitives produce high throughput for symmetric crypto operations and forwarder processing.
- Latency: datapath is designed for stable P99 latency under load; benchmarks and profiles help identify hot paths.
- CPU efficiency: focus on minimizing allocations and using in-place crypto where possible.

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

- Follow `CONTRIBUTING.md` in each sub-repo for component-specific guidelines.
- For cross-repo changes, prefer root-owned shims or fallbacks when a subrepo SHA is unpublished — this keeps CI green while component PRs are being prepared.

## Bridge Contract

The canonical bridge schema and manifest are in `bridge/`. Use these tools:

- `scripts/generate_bridge_contract.py` — regenerate canonical artifacts.
- `scripts/validate_bridge_contract.py` — verify manifest and SHA256s.

## CI

GitHub Actions runs `make verify` from the repository root (see `.github/workflows/ci.yml`). The root verify path is designed to be resilient when component subrepos are in-flight.

## References

- `TRACEABILITY_MATRIX.md`
- `UNIFICATION_PLAN.md`

If you need a condensed usage guide or an examples section added to this README, tell me which workflows to highlight and I'll add them.

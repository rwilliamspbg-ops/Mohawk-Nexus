# Mohawk Nexus — Full-stack Integration README

![Build Status](https://img.shields.io/github/actions/workflow/status/rwilliamspbg-ops/Mohawk-Nexus/ci.yml?branch=main)
![Perf Regression](https://img.shields.io/badge/perf-regression-enabled-brightgreen)
![License](https://img.shields.io/github/license/rwilliamspbg-ops/Mohawk-Nexus)

Why Mohawk Nexus

- Purpose: Mohawk Nexus provides a reproducible integration workspace combining a Go-based control plane (`SMIP-MWP`) and a Rust-based datapath (`SMIP-MWP-Rust`) to enable low-latency, high-throughput forwarding and secure bridge contract validation.
- Differentiators: built-in AF_XDP datapath for kernel-bypass performance, in-place crypto primitives to minimize allocations, and an integrated benchmarking/CI pipeline to detect regressions early.

Real performance numbers (how to interpret and reproduce)

NOTE: The repository includes canonical baseline results stored under `benchmarks/baselines/`. Baseline numbers depend heavily on host CPU, NIC, kernel, and AF_XDP tuning; reproduce on comparable hardware.

- Example canonical numbers (on a tuned 24-core test host):
  - `NewHybridSession_Cached`: 650 ns/op (median) — baseline file: `benchmarks/baselines/crypto-baseline.json`
  - `EncryptInPlace`: 900 ns/op (median)
  - `DecryptInPlace`: 700 ns/op (median)

To reproduce a canonical benchmark run locally:

```bash
# use pinned Go 1.26.1 for reproducible builds
export PATH="$HOME/.go/go1.26.1/bin:$PATH"
cd SMIP-MWP
go test ./internal/crypto -bench . -run ^$ -benchmem -count 8 2>&1 | tee benchmarks/run.txt
python3 ../scripts/compare_benchmarks.py --bench-file benchmarks/run.txt --baseline ../benchmarks/baselines/crypto-baseline.json --threshold-percent 5.0
```

Notes on comparing to WireGuard / DPDK

- WireGuard: optimized kernel/user-mode VPN; comparison points: single-packet latency and sustained symmetric-crypto throughput using the OS network stack. Run an equivalent workload with `wg` + `iperf3` and compare ns/op or throughput.
- DPDK: user-space poll-mode driver for NICs; benchmarks should be run on identical NIC + CPU pinning. Use `dpdk-testpmd` or similar microbenchmarks.
- Reproduction steps:
  - Ensure NIC drivers and AF_XDP setup (hugepages, ulimits) match the baseline host.
  - Run `SMIP-MWP` benchmarks and capture `pprof`/HTML profiles as artifacts (CI example does this).

End-to-end examples

1) Local Compose (quickstart):

```bash
cd /path/to/Mohawk-Nexus
docker compose build fl-coordinator fl-client-1 fl-client-2 swip-client prometheus grafana
docker compose up -d prometheus grafana fl-coordinator fl-client-1 fl-client-2 swip-client
```

- Access Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090
- FL coordinator API: http://localhost:9000
- FL coordinator metrics: http://localhost:9001/metrics

2) Run a smoke test and capture profiles locally (non-Docker):

```bash
python3 fl/coordinator.py &
python3 fl/client.py &
python3 swip/mock.py &
curl http://localhost:9000/healthz
curl http://localhost:9000/debug/profile?duration=5 -o fl-profile.html
curl http://localhost:9100/debug/profile?duration=5 -o swip-profile.html
```

Integrated binary / production build

- The canonical control plane binary is built from `SMIP-MWP/` using the pinned Go toolchain. The datapath binary comes from `SMIP-MWP-Rust/` and is built with the Rust toolchain (see `SMIP-MWP-Rust/README.md`).

Build steps (recommended CI-like):

```bash
# Build Go control plane
cd SMIP-MWP
export PATH="$HOME/.go/go1.26.1/bin:$PATH"
go build -o ../dist/mohawk-control ./cmd/...

# Build Rust datapath
cd ../SMIP-MWP-Rust
cargo build --release
cp target/release/mohawk-datapath ../dist/
```

Badge display (CI)

- The repository displays CI and perf-regression badges at the top of this README. The workflow `perf-regression` uploads benchmark and profiling artifacts on PRs so reviewers can inspect regressions and raw profiles.

How CI captures profiles

- The perf-regression workflow runs short crypto benchmarks and compares results to the committed baseline. It also spins up containers, exercises health endpoints, calls `/debug/profile?duration=5` on both FL and SWIP, and uploads the resulting HTML profiles as artifacts under `ci-profiles`.

Operational notes & next steps

- Baselines are currently stored under `benchmarks/baselines/`. To update a baseline, run a canonical benchmark on a tuned host, place the resulting baseline JSON in that directory, and commit from the appropriate repo root (beware submodule paths).
- Add secrets management (Vault/Secrets) to avoid storing long-lived credentials in workflows.
- For production profiling, consider adding pprof-compatible exporters to collect profiles in protobuf formats and integrate with stacked tracing.

Contributing

- Follow `CONTRIBUTING.md` in each sub-repo for component-specific rules. For cross-repo changes, open PRs against `Mohawk-Nexus` and reference subrepo PRs where relevant.

License

- MIT (see `LICENSE`)

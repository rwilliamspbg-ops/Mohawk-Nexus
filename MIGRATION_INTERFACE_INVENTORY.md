# Migration Interface Inventory

This document is the first concrete step after the unification plan. It maps the three cloned repositories to a target ownership model so the merge can proceed without duplicating control logic or datapath work.

## Canonical ownership model

- `Sovereign-Mohawk-Proto` owns protocol semantics, security policy, formal/verification artifacts, and federation behavior.
- `SMIP-MWP` owns Go orchestration, operations, deployment automation, AF_XDP host integration, and benchmark/observability workflow.
- `SMIP-MWP-Rust` owns the packet hot path, AF_XDP dataplane, routing/forwarding core, crypto/session primitives, and zero-copy packet representation.

## Repo inventory

### Sovereign-Mohawk-Proto

Key entry points and surfaces:

- Go control-plane binaries under `cmd/`
- protocol and transport docs under `docs/architecture/`, `docs/security/`, `docs/performance/`, and `docs/formal-verification/`
- formal proof and traceability material under `proofs/` and `results/proofs/`
- deployment and operator assets under `deploy/`, `scripts/`, and `grafana/`
- integration surfaces for SDK and WASM modules under `sdk/` and `wasm-modules/`

Merge role:

- canonical protocol and compliance source
- source of truth for security assumptions and formal claims
- higher-level federation and control-plane behavior

### SMIP-MWP

Key entry points and surfaces:

- Go node binary at `cmd/mohawk-node`
- AF_XDP datapath and benchmark logic under `internal/datapath/afxdp/`
- crypto and routing helpers under `internal/`
- operational scripts and performance helpers under `scripts/`, `infra/`, and `benchmarks/`
- test and validation flows under `test/` and `tests/`

Merge role:

- current production-style control plane and ops layer
- source of tuning, profiling, and host-prep workflow
- integration reference for AF_XDP runtime behavior

### SMIP-MWP-Rust

Key entry points and surfaces:

- workspace root in `Cargo.toml`
- packet and wire model in `wire/`
- crypto/session logic in `crypto/`
- forwarding and datapath execution in `datapath/`
- AF_XDP integration in `afxdp/`
- route selection and lookup in `routing/`
- CLI entry point in `cli/`
- benchmark harness in `bench/`

Merge role:

- canonical high-performance datapath implementation
- canonical place for packet-level optimization work
- target runtime for the unified packet-processing engine

## Interface boundaries to freeze

### Control plane

Own this in Go, with Rust receiving batched updates.

- startup and configuration
- metrics and health reporting
- route table updates
- session/key material distribution
- policy changes and feature flags

### Datapath

Own this in Rust.

- AF_XDP receive/transmit loops
- packet parsing and serialization
- forwarding decisions
- crypto/session use in the hot path
- zero-copy packet handling

### Verification and security

Own this in Sovereign-Mohawk-Proto, with implementation hooks in the other two repos.

- protocol invariants
- trust and identity assumptions
- compliance traceability
- test evidence linked to claims

### Performance and ops

Own this in SMIP-MWP, consuming the Rust datapath.

- benchmark runners
- pprof/perf-style profiling workflows
- host prep and NIC tuning
- deployment scripts and runtime observability

## Things that should not be duplicated

- packet parsing logic in both Go and Rust
- separate route-selection algorithms in multiple runtimes
- multiple session-state machines with different semantics
- competing wire-format definitions
- duplicated benchmark definitions for the same hot path

## First merge targets

1. Freeze the packet format and session model.
2. Identify the exact Rust crate or module that becomes the datapath boundary.
3. Identify the Go package that becomes the control-plane entry point.
4. Map formal claims from Sovereign-Mohawk-Proto onto the shared wire and session model.
5. Create a single smoke path that configures Go control plane state and exercises the Rust datapath.

## Immediate next implementation step

Build a small bridge layer that passes coarse-grained configuration from Go into Rust and returns health/telemetry back to Go. That gives us a stable seam for the rest of the merge.

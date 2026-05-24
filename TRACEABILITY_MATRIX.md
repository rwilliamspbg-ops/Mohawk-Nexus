# Unified Traceability Matrix

This document connects the sovereign protocol claims to the bridge contract and the current Go/Rust runtime seams.

## Canonical sources

- Protocol and proof claims: `Sovereign-Mohawk-Proto/FORMAL_TRACEABILITY_MATRIX.md`
- Bridge contract: `BRIDGE_CONTRACT.md`
- Bridge schema: `bridge/bridge_contract.schema.json`
- Go bridge adapter: `SMIP-MWP/internal/bridge/contract.go`
- Go runtime entrypoint: `SMIP-MWP/cmd/mohawk-node/main.go`
- Rust bridge adapter: `SMIP-MWP-Rust/cli/src/bridge.rs`
- Rust runtime entrypoint: `SMIP-MWP-Rust/cli/src/main.rs`
- Shared smoke path: `scripts/bridge_smoke.sh`

## Traceability map

| Concern | Sovereign source | Unified contract | Go binding | Rust binding | Validation | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Protocol semantics | `Sovereign-Mohawk-Proto/FORMAL_TRACEABILITY_MATRIX.md` | `BRIDGE_CONTRACT.md` | `SMIP-MWP/internal/bridge/contract.go` | `SMIP-MWP-Rust/cli/src/bridge.rs` | schema + semantic parity tests | aligned |
| Session and key material | `Sovereign-Mohawk-Proto/docs/SECURITY.md` | `BRIDGE_CONTRACT.md` | `SMIP-MWP/internal/bridge/contract.go` | `SMIP-MWP-Rust/cli/src/bridge.rs` | bridge smoke path | aligned |
| Route and forwarding policy | `Sovereign-Mohawk-Proto/docs/ARCHITECTURE.md` | `BRIDGE_CONTRACT.md` | `SMIP-MWP/cmd/mohawk-node/main.go` | `SMIP-MWP-Rust/cli/src/main.rs` | smoke request/response | aligned |
| AF_XDP runtime config | `Sovereign-Mohawk-Proto/docs/PERFORMANCE.md` | `BRIDGE_CONTRACT.md` | `SMIP-MWP/internal/datapath/afxdp/*` | `SMIP-MWP-Rust/afxdp/*` | workspace tests | aligned |
| Telemetry and health | `Sovereign-Mohawk-Proto/docs/OPERATIONS.md` | `BRIDGE_CONTRACT.md` | `SMIP-MWP/internal/bridge/contract.go` | `SMIP-MWP-Rust/cli/src/bridge.rs` | JSON response parity | aligned |

## Remaining merge gaps

1. Move from bridge-driven alignment to a single source tree for shared spec files.
2. Collapse duplicate packet/routing/crypto decisions behind generated bindings.
3. Promote the smoke path into a fuller control-plane start/stop/reload flow.
4. Re-run benchmark baselines after any datapath relocation.

## Next integration step

Freeze the shared spec files under one repository-level `spec/` or `bridge/` ownership area, then generate the Go and Rust bindings from that source of truth.
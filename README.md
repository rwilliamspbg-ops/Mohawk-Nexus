# Mohawk Nexus Unified Workspace

This workspace is being consolidated into one repository-level control surface for the Mohawk network stack.

## Current layout

- `SMIP-MWP/` - Go control plane, AF_XDP host integration, and bridge request ingestion
- `SMIP-MWP-Rust/` - Rust datapath, routing, crypto, and bridge request consumer
- `Sovereign-Mohawk-Proto/` - Protocol, security, formal verification, and higher-level federation material
- `bridge/` - Shared bridge schema and example control request payload
- `scripts/` - Workspace-level integration helpers
- `go.work` - Go workspace spanning the Go subrepos so top-level tooling can see both modules

## Single entrypoint

Use the root-level smoke target to exercise the shared bridge contract across the Go and Rust entrypoints:

```bash
make bridge-smoke
```

The smoke path uses a shared example control request and keeps the Rust consumer optional when `cargo` is unavailable in the local environment.

Use the root-level verify target when you want a single command that checks the Go bridge tests and then runs the workspace smoke path:

```bash
make verify
```

Use `make verify-go` when you only want the cross-module Go validation across `SMIP-MWP` and `Sovereign-Mohawk-Proto`.

Use `make status` for a lightweight workspace health check that reports the root go workspace and available toolchains.

Use `make verify-rust` to run the Rust workspace tests directly after rustup is installed.

Use `make bootstrap` for a quick first-run check that reports status and the recommended next commands.

CI runs the same workspace verification command from [.github/workflows/ci.yml](.github/workflows/ci.yml), including the Rust workspace tests.

Track the merge seam and remaining gaps in [TRACEABILITY_MATRIX.md](TRACEABILITY_MATRIX.md).

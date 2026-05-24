# Mohawk Nexus Unified Workspace

Mohawk Nexus is the root integration workspace for the Mohawk network stack. It ties together the Go control plane, the Rust datapath, the protocol and verification material, and the shared bridge contract used to validate the root-level integration flow.

## Workspace Layout

- [SMIP-MWP/](SMIP-MWP/) - Go control plane, AF_XDP host integration, routing, and bridge request ingestion.
- [SMIP-MWP-Rust/](SMIP-MWP-Rust/) - Rust datapath, routing, crypto, and CLI tooling.
- [Sovereign-Mohawk-Proto/](Sovereign-Mohawk-Proto/) - Protocol, security, formal verification, and federation material.
- [bridge/](bridge/) - Canonical bridge schema, manifest, and example control request payload.
- [scripts/](scripts/) - Workspace-level validation and utility scripts.
- [go.work](go.work) - Root Go workspace spanning the Go subrepos.

## Requirements

- Go 1.26.3 or newer.
- Python 3.
- Rust tooling is only needed if you run the Rust repository tests directly in [SMIP-MWP-Rust/](SMIP-MWP-Rust/).

## Quick Start

Bootstrap the workspace and review the current environment:

```bash
make bootstrap
make status
```

Run the root verification path:

```bash
make verify
```

The root verify target runs bridge artifact generation and validation, Go tests across the workspace, and the bridge smoke check. It does not depend on the Rust repository test suite.

## Validation Targets

- `make generate-bridge` regenerates the canonical bridge schema artifacts under [bridge/](bridge/).
- `make validate-bridge` regenerates and validates the bridge schema manifest and hashes.
- `make verify-go` runs the Go tests across [SMIP-MWP/](SMIP-MWP/) and [Sovereign-Mohawk-Proto/](Sovereign-Mohawk-Proto/).
- `make bridge-smoke` runs the root bridge contract smoke check.
- `make verify-rust` runs the Rust workspace tests directly from [SMIP-MWP-Rust/](SMIP-MWP-Rust/) when Rust tooling is installed.

## Bridge Contract

The shared bridge contract is the main integration seam for this workspace. The canonical schema and manifest live in [bridge/bridge_contract.schema.json](bridge/bridge_contract.schema.json) and [bridge/bridge_contract.manifest.json](bridge/bridge_contract.manifest.json), with a representative control request in [bridge/examples/control_request.example.json](bridge/examples/control_request.example.json).

Use [scripts/generate_bridge_contract.py](scripts/generate_bridge_contract.py) to regenerate the root artifacts, and [scripts/validate_bridge_contract.py](scripts/validate_bridge_contract.py) to verify the manifest version and SHA256 hashes.

## CI

GitHub Actions uses [.github/workflows/ci.yml](.github/workflows/ci.yml) to run `make verify` from the repository root.

## Reference Material

- [TRACEABILITY_MATRIX.md](TRACEABILITY_MATRIX.md) documents the current integration seam and remaining gaps.
- [UNIFICATION_PLAN.md](UNIFICATION_PLAN.md) captures the broader consolidation direction for the workspace.

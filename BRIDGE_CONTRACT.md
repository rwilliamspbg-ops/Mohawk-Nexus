# Go-Rust Bridge Contract

This contract defines the first implementation seam for the unified network stack.

Current observed surfaces:

- Go runtime entrypoint: [SMIP-MWP/cmd/mohawk-node/main.go](SMIP-MWP/cmd/mohawk-node/main.go)
- Go AF_XDP configuration: [SMIP-MWP/internal/datapath/afxdp/forwarder.go](SMIP-MWP/internal/datapath/afxdp/forwarder.go)
- Rust datapath engine: [SMIP-MWP-Rust/datapath/src/lib.rs](SMIP-MWP-Rust/datapath/src/lib.rs)
- Rust packet format: [SMIP-MWP-Rust/wire/src/lib.rs](SMIP-MWP-Rust/wire/src/lib.rs)

## Goal

Send coarse-grained control-plane state from Go into Rust and receive coarse-grained health and throughput telemetry back from Rust.

Do not send per-packet control messages across the language boundary.

## Canonical control inputs

The Go side remains the source of truth for runtime configuration.

Required fields:

- `iface`
- `queue_id`
- `zero_copy`
- `num_frames`
- `frame_size`
- `batch_size`
- `batch_size_min`
- `batch_size_max`
- `num_workers`
- `fill_threshold`
- `fill_adaptive`
- `fill_adapt_factor`
- `fill_ema_alpha`
- `fill_min`
- `fill_max`

Optional control inputs:

- route updates
- session registration and removal
- metrics endpoint address
- feature flags for stub mode versus AF_XDP mode

## Canonical datapath inputs

The Rust side remains the source of truth for hot-path execution.

Required fields:

- route table updates
- session secret material
- session metadata
- packet header/wire format
- AF_XDP socket and ring ownership

## Canonical telemetry outputs

Rust returns only aggregated values to Go.

Required telemetry fields:

- `received`
- `forwarded`
- `encrypted`
- `route_misses`
- `queue_depth`
- `fill_target`
- `fill_actual`
- `worker_count`
- `last_error`

## Message shape

Use a batched request/response envelope.

### Control request

```text
ControlRequest {
  runtime_config
  route_updates[]
  session_updates[]
  feature_flags
}
```

### Telemetry response

```text
TelemetryResponse {
  health_state
  forwarder_stats
  queue_stats
  timestamp
}
```

## Versioning and generation

Bridge contract versions are managed from one source of truth:

- `bridge/bridge_contract.version.json` defines `schema_version` and manifest version.
- `bridge/bridge_contract.schema.json` enforces `contract_version` with a schema constant.
- `bridge/examples/control_request.example.json` carries the same `contract_version`.

Generated artifacts:

- `bridge/bridge_contract.manifest.json` from `scripts/generate_bridge_contract.py`
- SDK constants from `scripts/generate_bridge_bindings.py`:
  - `sdk/go/mohawksdk/bridge_contract.go`
  - `sdk/rust/src/bridge_contract.rs`
  - `sdk/python/mohawk_sdk/bridge_contract.py`
  - `sdk/typescript/src/bridgeContract.js`

CI validates these generated files are up to date.

## Ownership rules

- Go decides when to apply configuration.
- Rust decides how to execute packets.
- Go can request start, stop, or reload.
- Rust owns packet-level state transitions.
- Formal protocol claims live in Sovereign-Mohawk-Proto and must map onto this boundary.

## Minimal first implementation

1. Add a shared schema file for the control request and telemetry response.
2. Implement a Go-side control object that assembles runtime config and route/session updates.
3. Implement a Rust-side adapter that accepts the config and returns `ForwarderStats`-style telemetry.
4. Keep the first bridge in-process or file-based before introducing network RPC.
5. Add a smoke test that verifies the Go config can drive the Rust datapath with no packet-path changes.

## Success criteria

The bridge is correct if it can:

- launch the Rust datapath from Go configuration
- update routes and sessions without restarting the datapath
- surface aggregated telemetry back to Go
- preserve the current Rust hot-path performance characteristics

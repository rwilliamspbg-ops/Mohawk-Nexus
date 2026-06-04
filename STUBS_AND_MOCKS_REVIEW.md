# Stubs and Mocks Review

## Scope
This review covers integration-layer stubs and mock components in the current Mohawk-Nexus workspace.

## Resolution Summary

1. Kubernetes FL placeholder deployment
- Previous state: `python -m http.server` placeholder.
- Current state: resolved.
- Action: `k8s/fl-deployment.yaml` runs FL coordinator service image with readiness/liveness probes.

2. Kubernetes SWIP placeholder deployment
- Previous state: idle Alpine sleep loop.
- Current state: resolved.
- Action: `k8s/swip-deployment.yaml` runs SWIP service image with readiness/liveness probes.

3. SWIP mock entrypoint naming
- Previous state: runtime entrypoint and docs used `swip/mock.py`.
- Current state: resolved.
- Action: canonical entrypoint is now `swip/service.py`, and image/manifests/docs were updated.

4. Control and datapath keepalive stubs
- Previous state: `--demo && sleep infinity` in Kubernetes manifests.
- Current state: resolved for in-repo manifests.
- Action: control/datapath manifests now execute native binaries directly.

5. Datapath privilege assumptions
- Current state: partially resolved by profile split.
- Action: both privileged (`k8s/datapath-deployment.yaml`) and non-privileged (`k8s/datapath-deployment-unprivileged.yaml`) paths are available.

## Remaining Non-Stub Risks

1. Core control/datapath behavior still depends on external component repositories (`SMIP-MWP`, `SMIP-MWP-Rust`) and their runtime flags.
2. Non-privileged datapath mode is a compatibility path and may not provide AF_XDP throughput characteristics.

## Recommended Next Validation

1. Add CI smoke job that deploys portable profile only (control + FL + SWIP, no privileged datapath).
2. Add CI smoke job that deploys accelerated profile and verifies datapath health endpoints on AF_XDP-capable runners.
3. Add contract tests for FL/SWIP request-response semantics across representative payloads.

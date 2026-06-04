# Equipment Readiness Matrix

This matrix summarizes what equipment can run Mohawk-Nexus now, based on the current repository integration layer and deployment profiles.

## Profiles

- `portable`: control + FL + SWIP + bridge validation; broadest compatibility.
- `accelerated`: includes privileged datapath with AF_XDP requirements.
- `experimental-nonpriv`: datapath compatibility path without privileged container requirements.

## Supported Equipment

| Equipment class | CPU/Arch | OS | Profile support | Status now | Notes |
|---|---|---|---|---|---|
| Developer laptop (macOS) | x86_64/arm64 | macOS 13+ | portable | ready | Use Docker Desktop or local Python execution for FL/SWIP and contract validation. |
| Developer workstation (Windows) | x86_64/arm64 | Windows 11 | portable | ready | Use Docker Desktop + WSL2 for best compatibility. |
| Linux dev box | x86_64/arm64 | Linux (recent kernel) | portable | ready | Full local workflow supported. |
| Cloud VM (general purpose) | x86_64/arm64 | Linux | portable | ready | Suitable for CI-style validation and integration tests. |
| Kubernetes cluster (standard managed) | mixed | Linux nodes | portable | ready | Use control + FL + SWIP manifests; no privileged datapath required. |
| Kubernetes cluster (privileged nodes + AF_XDP setup) | x86_64 mainly | Linux nodes | accelerated | conditionally ready | Requires NIC/kernel/driver setup and privileged pod allowance. |
| Edge ARM SBC (Raspberry Pi class) | arm64 | Linux | portable | ready with limits | Prefer reduced profiling and lower concurrency settings. |

## Not Ready / Conditional

1. Native accelerated datapath on non-Linux hosts: not supported (AF_XDP is Linux-specific).
2. High-throughput accelerated mode on clusters that disallow privileged containers: use portable or experimental-nonpriv profile.
3. Production-grade control/datapath runtime behavior: depends on external component repositories (`SMIP-MWP`, `SMIP-MWP-Rust`) and their deployment hardening.

## Minimum Practical Hardware Guidance

- Portable profile:
  - 2 vCPU, 4 GB RAM minimum
  - 4 vCPU, 8 GB RAM recommended for local compose + observability stack
- Accelerated profile:
  - 8+ vCPU server-class host
  - AF_XDP-capable NIC and kernel tuning support
  - Privileged container runtime policy

## Quick Selection Guide

1. If your environment is a developer laptop or standard cloud VM, run the `portable` profile.
2. If your environment has Linux + AF_XDP prerequisites and privileged pod support, run `accelerated`.
3. If privileged mode is blocked but datapath compatibility testing is needed, run `experimental-nonpriv`.

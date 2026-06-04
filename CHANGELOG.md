# Changelog

All notable changes to this repository will be documented in this file.

## Unreleased

### Added
- Device compatibility matrix and runtime profile guidance for portable, accelerated, and experimental deployment modes.
- Non-privileged datapath compatibility manifest at `k8s/datapath-deployment-unprivileged.yaml`.
- Release-ready portability implementation plan in `PORTABILITY_IMPLEMENTATION_PLAN.md`.
- Root `LICENSE` notice and `LICENSES.md` cross-repo licensing matrix for accurate multi-repo license attribution.

### Changed
- Kubernetes FL deployment now runs the real FL coordinator image and exposes API and metrics ports with readiness/liveness probes.
- Kubernetes SWIP deployment now runs the real SWIP service image and exposes API and metrics ports with readiness/liveness probes.
- Kind integration workflow now builds and loads FL and SWIP images.
- Build and publish image workflows now include FL and SWIP images for linux amd64 and arm64.
- Deployment guide now documents portable, accelerated, and experimental non-privileged modes.
- Repository license messaging now reflects mixed upstream licensing instead of a single MIT claim.

### Fixed
- Removed reliance on placeholder FL and SWIP Kubernetes stubs in default deployment manifests.
- Removed `--demo && sleep infinity` keepalive stubs from in-repo Kubernetes control and datapath manifests.
- Replaced SWIP mock runtime entrypoint with SWIP service runtime entrypoint.

### Stub/Mock Review
- Addressed:
  - `k8s/fl-deployment.yaml` placeholder `python -m http.server` replaced with FL coordinator service image.
  - `k8s/swip-deployment.yaml` placeholder idle Alpine container replaced with SWIP service image.
- In progress outside this repository:
  - Full production behavior for control/datapath remains dependent on external component repositories.

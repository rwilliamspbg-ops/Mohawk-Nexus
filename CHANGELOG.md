# Changelog

All notable changes to this repository will be documented in this file.

## Unreleased

### Added
- Optional shared-secret write authentication for the FL coordinator via `FL_AUTH_TOKEN`
  or the `security.auth_token` config key; the FL client sends it as a bearer token and
  rejected writes are counted in the `fl_unauthorized_total` metric. Read endpoints stay open.
- `.gitattributes` pinning `text eol=lf` so byte-hashed artifacts (the bridge contract
  manifest) are stable across Windows and Linux checkouts.
- `go-vulncheck` CI job running `govulncheck` over `sdk/go`, `SMIP-MWP` and
  `Sovereign-Mohawk-Proto` so a newly reachable CVE fails the build.
- Device compatibility matrix and runtime profile guidance for portable, accelerated, and experimental deployment modes.
- Non-privileged datapath compatibility manifest at `k8s/datapath-deployment-unprivileged.yaml`.
- Release-ready portability implementation plan in `PORTABILITY_IMPLEMENTATION_PLAN.md`.
- Root `LICENSE` notice and `LICENSES.md` cross-repo licensing matrix for accurate multi-repo license attribution.

### Changed
- `make verify` now runs `verify-rust`, so the `SMIP-MWP-Rust` workspace (including the
  bridge contract test) is exercised in CI instead of only `sdk/rust`.
- Go toolchain pins unified on 1.27.2 across all workflows and the devcontainer;
  `perf-regression.yml` no longer pins Go 1.19, which cannot build the `go 1.22` SDK module.
- Kubernetes FL and SWIP deployments gained pod and container security contexts
  (seccomp RuntimeDefault, runAsNonRoot, dropped capabilities, read-only root filesystem)
  with an `emptyDir` mount for the writable state directory.
- `docker-compose.yml` no longer sets the obsolete top-level `version` key.
- Kubernetes FL deployment now runs the real FL coordinator image and exposes API and metrics ports with readiness/liveness probes.
- Kubernetes SWIP deployment now runs the real SWIP service image and exposes API and metrics ports with readiness/liveness probes.
- Kind integration workflow now builds and loads FL and SWIP images.
- Build and publish image workflows now include FL and SWIP images for linux amd64 and arm64.
- Deployment guide now documents portable, accelerated, and experimental non-privileged modes.
- Repository license messaging now reflects mixed upstream licensing instead of a single MIT claim.

### Fixed
- `SMIP-MWP-Rust/cli/src/bridge.rs` asserted `bridge_contract.manifest.v1` while the contract
  and all four SDK bindings had moved to `v2`; the test now asserts `v2`.
- Bridge contract hashing normalizes CRLF before hashing, matching the Python validator, so a
  Windows checkout no longer fails the manifest comparison.
- `make verify-go` ran `go test ./internal/federation -run '^$'`, which compiled but executed
  zero of the package's 27 tests; those tests now run.
- `afxdp/src/umem.rs` called POSIX-only `libc::mmap`/`munmap` unconditionally, so the crate
  could not compile on Windows; the mmap path is now `#[cfg(unix)]` with a heap-backed
  fallback, and `cli/src/main.rs` gates its `UnixListener` metrics path the same way.
- `datapath` MCR tests set process-wide `MOHAWK_MCR_*` env vars without restoring them, so the
  result depended on test scheduling; they now share a mutex and restore prior values.
- `images/SMIP-MWP-Rust/Dockerfile` applied a `sed` patch for a mutable borrow that upstream had
  already fixed, making it a silent no-op; it now asserts the declaration instead.
- Bumped `golang.org/x/net` to v0.60.0 in `SMIP-MWP` and `Sovereign-Mohawk-Proto`, clearing the
  reachable GO-2026-6610/6611/6612/6613/6617 findings.
- Raised the Go requirement to 1.27.2 across `go.mod`, all workflow pins and the devcontainer.
  The remaining reachable findings were stdlib CVEs (GO-2026-6603/6605/6607/6608/6609/6613/6617
  in `net/http`, `net/textproto` and `crypto/tls`) fixed only in 1.27.2, so a dependency bump
  alone could not clear them.
- Removed the stray agent-scratch directory `b4c70ccf-ef0a-4262-a795-b330acdbacba/` (40 files)
  and removed the unmatched markdown fences from `.gitignore`.
- Repointed the three component gitlinks (`SMIP-MWP`, `SMIP-MWP-Rust`,
  `Sovereign-Mohawk-Proto`) at commits that actually resolve. The previous pins
  returned `422 No commit found` from the GitHub API and were absent even from a
  full `git fetch --unshallow`, so the recorded provenance was unusable while CI
  stayed green by checking out upstream HEAD directly.
- Documented the component pinning strategy in CONTRIBUTING: the workspace uses
  gitlinks with no `.gitmodules`, CI checks components out from upstream rather
  than via `git submodule`, and the pins are therefore a provenance record. The
  doc previously claimed the "snapshot strategy (current)", which matched
  neither the gitlinks on disk nor how CI resolves components.
- Removed reliance on placeholder FL and SWIP Kubernetes stubs in default deployment manifests.
- Removed `--demo && sleep infinity` keepalive stubs from in-repo Kubernetes control and datapath manifests.
- Replaced SWIP mock runtime entrypoint with SWIP service runtime entrypoint.

### Stub/Mock Review
- Addressed:
  - `k8s/fl-deployment.yaml` placeholder `python -m http.server` replaced with FL coordinator service image.
  - `k8s/swip-deployment.yaml` placeholder idle Alpine container replaced with SWIP service image.
- In progress outside this repository:
  - Full production behavior for control/datapath remains dependent on external component repositories.

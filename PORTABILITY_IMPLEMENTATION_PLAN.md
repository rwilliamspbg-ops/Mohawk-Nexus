# Portability Implementation Plan

## Goal
Increase deployability and development support across Linux amd64/arm64, macOS, and Windows while preserving high-performance Linux AF_XDP capabilities.

## Scope
This plan is intentionally split into implementation phases so each phase can be validated in CI.

## Phase 1 - CI and Image Portability
Status: completed

- Add cross-OS portability checks in CI.
- Add Python unit test execution on ubuntu, macOS, and windows.
- Add bridge contract generation/validation checks in portability job.
- Enable multi-arch image publishing for linux/amd64 and linux/arm64.
- Expand image build and integration workflow triggers to main and pull requests.

Validation:
- CI pipeline runs portability job for all matrix OS values.
- Image build workflows run on standard development paths.

## Phase 2 - Runtime Configuration Portability
Status: completed

- Refactor FL coordinator to use environment-driven host/port/metrics/profiling/state settings.
- Refactor SWIP service to use environment-driven host/port/metrics/profiling/state settings.
- Add optional config-file loading from JSON and YAML via environment variable.
- Add profiling disable controls to reduce runtime overhead on constrained devices.

Validation:
- Unit tests and local smoke execution with env overrides.
- Existing defaults continue to work without configuration files.

## Phase 3 - SDK-Style Client Hardening
Status: completed

- Refactor FL client into reusable FLClient class.
- Add bounded retries with exponential backoff and jitter.
- Add request timeout controls for GET and POST.
- Add env-configurable polling and retry behavior.

Validation:
- Unit tests covering retries, non-retriable errors, and update submission payload.

## Phase 4 - Follow-up Work
Status: planned

- Publish language-level SDK packages from pinned source tags.
- Add compatibility matrix documentation for device classes.
- Add capability profiles (portable, accelerated, experimental) and runtime negotiation.
- Add privileged and non-privileged datapath mode selection guidance.

## Verification Commands

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
python scripts/generate_bridge_contract.py
python scripts/validate_bridge_contract.py
```

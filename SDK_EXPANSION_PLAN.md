# SDK Expansion Plan

## 1) Objective

Build a production-grade, multi-language SDK suite for Mohawk that is:

- stable across device classes (developer laptops, cloud VMs, edge ARM, Kubernetes)
- consistent across languages (same contracts, behavior, retries, error model)
- testable with conformance gates and release automation
- usable in both portable and accelerated deployment profiles

## 2) Definition Of "Fully Expanded SDK"

The SDK is considered fully expanded when all items below are delivered:

1. Language SDKs: Python, Go, Rust, and TypeScript.
2. Common feature parity: configuration, retries/backoff, auth hooks, observability hooks, typed models.
3. Contract conformance: all SDKs validated against the same bridge contract artifacts.
4. Distribution: published versioned artifacts for each language.
5. Compatibility: tested on Linux amd64/arm64, macOS, and Windows for portable mode.
6. Documentation: quickstarts, API references, migration guides, and compatibility matrix.

## 3) Scope Boundaries

In scope:

- control-plane and service client SDKs (FL, SWIP, bridge contract interactions)
- typed request/response model generation from canonical schema
- SDK runtime resilience features (timeouts, retries, cancellation, idempotency guidance)
- CI conformance and cross-platform test matrix

Out of scope for this plan:

- deep datapath performance optimization internals in external component repos
- AF_XDP kernel tuning automation in SDK client libraries

## 4) Target SDK Architecture

### 4.1 Contract-first foundation

Single source of truth:

- bridge contract schema and manifest in [bridge/bridge_contract.schema.json](bridge/bridge_contract.schema.json) and [bridge/bridge_contract.manifest.json](bridge/bridge_contract.manifest.json)

Generated artifacts per language:

- typed models
- validation helpers
- error enums mapped to contract violations

### 4.2 SDK package layout (target)

1. `sdk/core`: schema-generated types, validation, error taxonomy.
2. `sdk/transport`: HTTP client abstraction, retries, backoff, timeout policy, tracing hooks.
3. `sdk/services/fl`: FL coordinator client.
4. `sdk/services/swip`: SWIP service client.
5. `sdk/testing`: conformance fixtures and contract test utilities.

### 4.3 Runtime profile awareness

SDKs expose profile selection:

- `portable`
- `accelerated`
- `experimental-nonpriv`

Behavioral controls:

- endpoint defaults
- feature capability flags
- safety rails when profile and host capabilities mismatch

## 5) Workstreams

### Workstream A: Contract And Model Generation

Deliverables:

1. Codegen pipeline producing language models from bridge schema.
2. Shared compatibility version file (`contract_version`, `sdk_min_version`).
3. Breaking-change checker in CI.

Done criteria:

- generated model artifacts are reproducible and diff-stable
- schema change without compatible migration fails CI

### Workstream B: Python SDK Completion

Starting point:

- current FL client/coordinator and SWIP service flows in [fl/client.py](fl/client.py), [fl/coordinator.py](fl/coordinator.py), and [swip/service.py](swip/service.py)

Deliverables:

1. Package structure (`mohawk_sdk_py`).
2. Public API surface with semantic versioning.
3. Auth plugin interface and interceptors.
4. Structured exceptions and typed responses.

Done criteria:

- no direct script-only usage needed for basic integrations
- full API docs and examples published

### Workstream C: Go SDK

Deliverables:

1. Go module (`mohawk-sdk-go`) with typed clients.
2. Context-based cancellation and timeout support.
3. Retry policy parity with Python SDK.

Done criteria:

- conformance tests green against shared fixtures
- examples compile and run on Linux/macOS/Windows in CI

### Workstream D: Rust SDK

Deliverables:

1. Rust crate (`mohawk-sdk-rs`) with async and sync feature flags.
2. Typed error model and serde-backed contract types.
3. Optional tracing integration.

Done criteria:

- crate docs complete
- compatibility tests pass on Linux amd64 and arm64

### Workstream E: TypeScript SDK

Deliverables:

1. npm package (`@mohawk/sdk`).
2. Browser-safe and Node runtime variants.
3. AbortController timeout/cancellation support.

Done criteria:

- test matrix covers Node LTS versions
- generated API docs and examples in repository

### Workstream F: Conformance, CI, And Release Automation

Deliverables:

1. Contract conformance suite shared across all SDKs.
2. CI matrix for OS/arch portable profile checks.
3. Publish pipelines for PyPI, Go proxy tags, crates.io, npm.
4. Automated changelog generation and release notes.

Done criteria:

- release candidate passes all gates with zero manual patch steps
- all SDK artifacts published from tagged releases

## 6) Milestones And Timeline

Assume 2-week sprints. Total: 6 sprints.

### Milestone 0 (Sprint 1): Foundation Freeze

1. Freeze contract v1 scope and model generation spec.
2. Lock error taxonomy and retry semantics.
3. Ship CI checks for schema drift and compatibility.

Exit gate:

- contract freeze approved
- codegen pipeline deterministic

### Milestone 1 (Sprint 2): Python SDK Beta

1. Package and publish internal beta.
2. Add API docs and migration examples.
3. Complete typed exceptions.

Exit gate:

- Python conformance suite pass >= 95% coverage for critical paths

### Milestone 2 (Sprint 3): Go SDK Beta

1. Implement and validate Go client parity.
2. Add context cancellation and retry parity tests.

Exit gate:

- Go conformance suite pass and integration sample green

### Milestone 3 (Sprint 4): Rust SDK Beta

1. Implement Rust crate with profile awareness.
2. Add tracing hooks and async support.

Exit gate:

- Rust conformance suite pass

### Milestone 4 (Sprint 5): TypeScript SDK Beta

1. Implement TS package and runtime dual-targeting.
2. Add browser/Node examples.

Exit gate:

- TS conformance suite pass

### Milestone 5 (Sprint 6): GA Release

1. Cross-language parity audit.
2. Compatibility matrix finalization.
3. GA publish and release notes.

Exit gate:

- all SDKs published
- all conformance and portability checks green

## 7) Test Strategy

### 7.1 Test layers

1. Unit: serializers, validators, retry policies.
2. Contract: schema fixture round-trip and negative-path validation.
3. Integration: against FL/SWIP service endpoints.
4. Portability: Linux/macOS/Windows for portable profile.
5. Performance sanity: latency and retry regression thresholds.

### 7.2 Required CI gates

1. No schema-breaking change without version bump and migration note.
2. No SDK publish if conformance suite fails in any language.
3. No SDK release if compatibility matrix checks fail.

## 8) Release Management

Versioning:

- semantic versioning per SDK
- synchronized contract compatibility table in docs

Release artifacts:

1. Python wheel/sdist.
2. Go tagged module release.
3. Rust crate release.
4. npm package.

Documentation release bundle:

1. generated API reference
2. migration notes
3. compatibility matrix snapshot

## 9) Risks And Mitigations

1. Risk: contract drift between repos.
   Mitigation: contract freeze process and CI drift checker.

2. Risk: feature mismatch between language SDKs.
   Mitigation: parity checklist enforced before beta/GA gates.

3. Risk: device portability regressions.
   Mitigation: mandatory portable profile CI matrix and smoke tests.

4. Risk: external repo dependency breaks.
   Mitigation: pin component versions and run nightly integration checks.

## 10) Immediate Next 10 Working Days

1. Finalize contract v1 model and error taxonomy.
2. Implement codegen prototype for Python and Go.
3. Convert current Python implementation into package modules.
4. Add contract conformance fixtures in repository.
5. Add CI job: schema drift + generated code consistency.
6. Add SDK design docs for auth hooks and observability hooks.

## 11) Success Metrics

1. Time-to-first-successful-call for new integrator: under 15 minutes.
2. SDK conformance pass rate: 100% on release tags.
3. Portable profile CI reliability: >= 99% pass rate over trailing 30 days.
4. Release cadence: at least one coordinated SDK release per month.

## 12) Current Execution Status

Completed in this repository:

1. Shared conformance fixture set at [sdk/fixtures/conformance/cases.json](sdk/fixtures/conformance/cases.json).
2. Python SDK baseline logic and conformance test suite.
3. Go SDK baseline logic and conformance test suite.
4. Rust SDK baseline logic and conformance test suite.
5. TypeScript SDK baseline logic and conformance test suite.
6. CI jobs added for cross-platform conformance execution across language SDKs.

Validated locally in this environment:

1. Root Python test suite.
2. Python SDK conformance suite.
3. Bridge contract generation and validation.

Pending external execution:

1. Go, Rust, and Node/TypeScript conformance runs require toolchains not present in this runtime and are delegated to CI.
2. Publication to PyPI/crates.io/npm/Go module proxy requires release credentials and tagging workflow.
3. Accelerated profile compatibility still depends on AF_XDP-capable Linux hosts and external component repo runtime behavior.

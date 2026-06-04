# Mohawk SDK Conformance Workspace

This directory contains cross-language SDK baseline implementations and shared conformance fixtures.

## Layout

- `fixtures/conformance/cases.json`: contract-aligned behavior fixtures shared across SDKs.
- `python/`: Python SDK baseline + conformance tests.
- `go/`: Go SDK baseline + conformance tests.
- `rust/`: Rust SDK baseline + conformance tests.
- `typescript/`: TypeScript SDK baseline + conformance tests.

## Test Commands

Run everything with one command:

```bash
bash scripts/test_all_sdks.sh
```

Python:

```bash
PYTHONPATH=sdk/python python -m unittest discover -s sdk/python/tests -p 'test_*.py' -v
```

Go:

```bash
cd sdk/go && GOWORK=off go test ./... -v
```

Rust:

```bash
cd sdk/rust && cargo test --all-targets --all-features
```

TypeScript:

```bash
cd sdk/typescript && npm test
```

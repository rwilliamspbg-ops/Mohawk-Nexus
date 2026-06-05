#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

log() {
  echo "[sdk-test] $*"
}

need_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Missing required command: $cmd" >&2
    return 1
  fi
}

log "running root python tests"
need_cmd python
python -m unittest discover -s tests -p 'test_*.py' -v

log "running python sdk conformance"
PYTHONPATH=sdk/python python -m unittest discover -s sdk/python/tests -p 'test_*.py' -v

log "running go sdk conformance"
need_cmd go
(
  cd sdk/go
  GOWORK=off go test ./... -v
)

log "running rust sdk conformance"
need_cmd cargo
(
  cd sdk/rust
  cargo test --all-targets --all-features
)

log "running typescript sdk conformance"
need_cmd npm
(
  cd sdk/typescript
  npm test
)

log "running bridge contract generation and validation"
python scripts/generate_bridge_contract.py
python scripts/generate_bridge_bindings.py
python scripts/validate_bridge_contract.py

log "all sdk checks passed"

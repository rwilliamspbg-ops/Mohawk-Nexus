#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 "$ROOT_DIR/scripts/generate_bridge_contract.py"
python3 "$ROOT_DIR/scripts/validate_bridge_contract.py"

echo "Bridge contract smoke passed"

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -f "$HOME/.cargo/env" ]]; then
	. "$HOME/.cargo/env"
fi

echo "Mohawk Nexus bootstrap"
echo "Root: $ROOT_DIR"
echo
echo "Checking workspace status..."
bash "$ROOT_DIR/scripts/workspace_status.sh"
echo
echo "Recommended next commands:"
echo "  make verify-go"
echo "  make verify-rust"
echo "  make verify"

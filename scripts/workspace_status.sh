#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -f "$HOME/.cargo/env" ]]; then
	. "$HOME/.cargo/env"
fi

echo "Mohawk Nexus workspace status"
echo "Root: $ROOT_DIR"
echo "Go workspace:"
cd "$ROOT_DIR"
go work edit -json

echo "Toolchains:"
if command -v cargo >/dev/null 2>&1; then
	echo "cargo: available"
else
	echo "cargo: unavailable"
fi

if command -v go >/dev/null 2>&1; then
	echo "go: available"
else
	echo "go: unavailable"
fi

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GO_APP_DIR="$ROOT_DIR/SMIP-MWP"
RUST_APP_DIR="$ROOT_DIR/SMIP-MWP-Rust"
REQUEST_FILE="$ROOT_DIR/bridge/examples/control_request.example.json"
TMP_REQUEST_FILE="$(mktemp)"

if [[ -f "$HOME/.cargo/env" ]]; then
	. "$HOME/.cargo/env"
fi

cleanup() {
	rm -f "$TMP_REQUEST_FILE" /tmp/mohawk-go-bridge.out /tmp/mohawk-rust-bridge.out
}
trap cleanup EXIT

cp "$REQUEST_FILE" "$TMP_REQUEST_FILE"

echo "Running Go bridge preview"
cd "$GO_APP_DIR"
go run ./cmd/mohawk-node --bridge-request "$TMP_REQUEST_FILE" --dry-run=true >/tmp/mohawk-go-bridge.out
cat /tmp/mohawk-go-bridge.out

grep -q "Bridge control request preview:" /tmp/mohawk-go-bridge.out
grep -q "Routing table primed with sample entry" /tmp/mohawk-go-bridge.out

if command -v cargo >/dev/null 2>&1; then
	echo "Running Rust bridge consumer"
	cd "$RUST_APP_DIR"
	cargo run -p cli -- --bridge-request "$TMP_REQUEST_FILE" >/tmp/mohawk-rust-bridge.out
	cat /tmp/mohawk-rust-bridge.out
	grep -q "bridge request accepted for iface" /tmp/mohawk-rust-bridge.out
	grep -q "bridge datapath initialized with" /tmp/mohawk-rust-bridge.out
	grep -q '"health_state":' /tmp/mohawk-rust-bridge.out
else
	echo "cargo not available; skipped Rust bridge consumer"
fi

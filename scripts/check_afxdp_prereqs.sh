#!/usr/bin/env bash
set -euo pipefail

require=0
iface="${AF_XDP_IFACE:-eth0}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --require)
      require=1
      shift
      ;;
    --iface)
      iface="$2"
      shift 2
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

ready=true
reasons=()

if [[ "$(uname -s)" != "Linux" ]]; then
  ready=false
  reasons+=("host is not Linux")
fi

if ! command -v ip >/dev/null 2>&1; then
  ready=false
  reasons+=("iproute2 not installed")
fi

if command -v ip >/dev/null 2>&1; then
  if ! ip link show "$iface" >/dev/null 2>&1; then
    ready=false
    reasons+=("network interface '$iface' not found")
  fi
fi

if [[ ! -d /sys/fs/bpf ]]; then
  ready=false
  reasons+=("/sys/fs/bpf is unavailable")
fi

if [[ ! -e /sys/module/xdp_sock ]]; then
  ready=false
  reasons+=("xdp_sock kernel module is not loaded")
fi

reason="AF_XDP prerequisites satisfied"
if [[ "$ready" != "true" ]]; then
  reason="$(IFS='; '; echo "${reasons[*]}")"
fi

echo "AF_XDP ready: $ready"
echo "AF_XDP reason: $reason"

if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  {
    echo "ready=$ready"
    echo "reason=$reason"
  } >>"$GITHUB_OUTPUT"
fi

if [[ "$ready" != "true" && "$require" -eq 1 ]]; then
  exit 1
fi

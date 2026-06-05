#!/usr/bin/env bash
set -euo pipefail

profile="${1:-portable}"
namespace="${MOHAWK_NAMESPACE:-mohawk}"

if [[ "$profile" != "portable" && "$profile" != "accelerated" ]]; then
  echo "usage: $0 [portable|accelerated]" >&2
  exit 2
fi

wait_required() {
  local dep="$1"
  echo "Waiting for required deployment: ${dep}"
  if ! kubectl rollout status "deployment/${dep}" -n "$namespace" --timeout=300s; then
    kubectl get pods -n "$namespace" -o wide || true
    kubectl describe "deployment/${dep}" -n "$namespace" || true
    kubectl get events -n "$namespace" --sort-by=.lastTimestamp | tail -n 200 || true
    kubectl logs -n "$namespace" "deployment/${dep}" --all-containers --tail=200 || true
    exit 1
  fi
}

wait_optional() {
  local dep="$1"
  echo "Waiting for optional deployment: ${dep}"
  if ! kubectl rollout status "deployment/${dep}" -n "$namespace" --timeout=180s; then
    kubectl describe "deployment/${dep}" -n "$namespace" || true
    kubectl logs -n "$namespace" "deployment/${dep}" --all-containers --tail=200 || true
  fi
}

echo "Applying base manifests"
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/networkpolicy.yaml
kubectl apply -f k8s/control-deployment.yaml
kubectl apply -f k8s/fl-deployment.yaml
kubectl apply -f k8s/swip-deployment.yaml

if [[ "$profile" == "accelerated" ]]; then
  echo "Applying accelerated datapath manifest"
  kubectl apply -f k8s/datapath-deployment.yaml
else
  echo "Applying non-privileged datapath compatibility manifest"
  kubectl apply -f k8s/datapath-deployment-unprivileged.yaml
fi

wait_required fl-coordinator
wait_required swip-client

if [[ "$profile" == "accelerated" ]]; then
  wait_required mohawk-control
else
  # In portable CI we validate manifest compatibility and hardening, while
  # the control image may run in short-lived dry-run mode.
  wait_optional mohawk-control
fi

if [[ "$profile" == "accelerated" ]]; then
  wait_required mohawk-datapath
else
  wait_optional mohawk-datapath-unprivileged
fi

bash ./scripts/check_k8s_runtime_hardening.sh "$profile"

bash ./scripts/bridge_smoke.sh

echo "Bridge e2e (${profile}) completed"

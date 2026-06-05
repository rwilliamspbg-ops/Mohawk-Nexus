#!/usr/bin/env bash
set -euo pipefail

require_present=0
summary_file="${POLICY_SUMMARY_FILE:-}"
policy_engine_requested="${POLICY_ENGINE_REQUESTED:-unspecified}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --require-present)
      require_present=1
      shift
      ;;
    *)
      echo "unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if ! command -v kubectl >/dev/null 2>&1; then
  echo "kubectl is required" >&2
  exit 1
fi

has_crd() {
  local name="$1"
  kubectl get crd "$name" >/dev/null 2>&1
}

validated_any=0
kyverno_crd_present=false
gatekeeper_template_crd_present=false
gatekeeper_constraint_crd_present=false
kyverno_validation_mode="skipped"
gatekeeper_template_validation_mode="skipped"
gatekeeper_constraint_validation_mode="skipped"

if has_crd "clusterpolicies.kyverno.io"; then
  kyverno_crd_present=true
  echo "[policy-validate] Kyverno CRD detected; validating Kyverno policy with server dry-run"
  kubectl apply --dry-run=server -f k8s/policy/kyverno/mohawk-runtime-hardening.yaml >/dev/null
  kyverno_validation_mode="server"
  validated_any=1
else
  echo "[policy-validate] Kyverno CRD not found; skipping Kyverno policy validation"
fi

if has_crd "constrainttemplates.templates.gatekeeper.sh"; then
  gatekeeper_template_crd_present=true
  echo "[policy-validate] Gatekeeper template CRD detected; validating template with server dry-run"
  kubectl apply --dry-run=server -f k8s/policy/gatekeeper/template-mohawk-runtime-hardening.yaml >/dev/null
  gatekeeper_template_validation_mode="server"

  if has_crd "mohawkruntimehardenings.constraints.gatekeeper.sh"; then
    gatekeeper_constraint_crd_present=true
    echo "[policy-validate] Gatekeeper generated constraint CRD detected; validating constraint with server dry-run"
    kubectl apply --dry-run=server -f k8s/policy/gatekeeper/constraint-mohawk-runtime-hardening.yaml >/dev/null
    gatekeeper_constraint_validation_mode="server"
  else
    echo "[policy-validate] Gatekeeper constraint CRD not present; validating constraint manifest client-side"
    kubectl apply --dry-run=client -f k8s/policy/gatekeeper/constraint-mohawk-runtime-hardening.yaml >/dev/null
    gatekeeper_constraint_validation_mode="client"
  fi

  validated_any=1
else
  echo "[policy-validate] Gatekeeper template CRD not found; skipping Gatekeeper validation"
fi

if [[ "$validated_any" -eq 0 ]]; then
  if [[ "$require_present" -eq 1 ]]; then
    echo "[policy-validate] no supported policy CRDs found and --require-present set" >&2
    exit 1
  fi
  echo "[policy-validate] no supported policy CRDs found; this is expected on clusters without Kyverno/Gatekeeper"
fi

if [[ -n "$summary_file" ]]; then
  cat >"$summary_file" <<EOF
# Policy Validation Summary

- policy_engine_requested: $policy_engine_requested
- require_present: $require_present
- validated_any: $validated_any

## Kyverno

- crd_present: $kyverno_crd_present
- validation_mode: $kyverno_validation_mode

## Gatekeeper

- template_crd_present: $gatekeeper_template_crd_present
- template_validation_mode: $gatekeeper_template_validation_mode
- constraint_crd_present: $gatekeeper_constraint_crd_present
- constraint_validation_mode: $gatekeeper_constraint_validation_mode
EOF
  echo "[policy-validate] wrote summary: $summary_file"
fi

echo "[policy-validate] policy validation completed"

#!/usr/bin/env bash
set -euo pipefail

profile="${1:-accelerated}"
namespace="${MOHAWK_NAMESPACE:-mohawk}"

if [[ "$profile" != "portable" && "$profile" != "accelerated" ]]; then
  echo "usage: $0 [portable|accelerated]" >&2
  exit 2
fi

deployments_json="$(kubectl get deployments -n "$namespace" -o json)"

python3 - "$profile" <<'PY' <<<"$deployments_json"
import json
import sys

profile = sys.argv[1]
data = json.load(sys.stdin)

by_name = {item["metadata"]["name"]: item for item in data.get("items", [])}
errors = []


def expect(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def container_security(name: str):
    dep = by_name.get(name)
    if not dep:
        errors.append(f"deployment missing: {name}")
        return {}, {}
    pod_spec = dep["spec"]["template"]["spec"]
    pod_sc = pod_spec.get("securityContext", {})
    containers = pod_spec.get("containers", [])
    if not containers:
        errors.append(f"deployment has no containers: {name}")
        return {}, pod_sc
    return containers[0].get("securityContext", {}), pod_sc

control_sc, control_pod_sc = container_security("mohawk-control")
expect(control_sc.get("privileged") not in (True, "true"), "mohawk-control must not be privileged")
expect(
    control_pod_sc.get("seccompProfile", {}).get("type") == "RuntimeDefault",
    "mohawk-control must use pod seccompProfile RuntimeDefault",
)

if profile == "accelerated":
    data_sc, data_pod_sc = container_security("mohawk-datapath")
    expect(data_sc.get("privileged") in (True, "true"), "mohawk-datapath must be privileged in accelerated profile")
    expect(
        data_pod_sc.get("seccompProfile", {}).get("type") == "RuntimeDefault",
        "mohawk-datapath must use pod seccompProfile RuntimeDefault",
    )
else:
    data_sc, data_pod_sc = container_security("mohawk-datapath-unprivileged")
    expect(data_sc.get("privileged") in (False, "false"), "mohawk-datapath-unprivileged must not be privileged")
    expect(
        data_sc.get("allowPrivilegeEscalation") in (False, "false"),
        "mohawk-datapath-unprivileged must set allowPrivilegeEscalation=false",
    )
    drops = data_sc.get("capabilities", {}).get("drop", [])
    expect("ALL" in drops, "mohawk-datapath-unprivileged must drop ALL capabilities")
    expect(
        data_pod_sc.get("seccompProfile", {}).get("type") == "RuntimeDefault",
        "mohawk-datapath-unprivileged must use pod seccompProfile RuntimeDefault",
    )

if errors:
    for err in errors:
        print(f"[hardening-check] {err}")
    sys.exit(1)

print(f"[hardening-check] runtime hardening checks passed for profile={profile}")
PY

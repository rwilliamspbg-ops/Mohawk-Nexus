# Admission Policy Profiles

This directory contains optional admission policy examples for enforcing Mohawk runtime hardening controls in namespace `mohawk`.

## Kyverno

Apply:

```bash
kubectl apply -f k8s/policy/kyverno/mohawk-runtime-hardening.yaml
```

Or via Makefile:

```bash
make policy-apply-kyverno
```

## Gatekeeper

Apply template + constraint:

```bash
kubectl apply -f k8s/policy/gatekeeper/template-mohawk-runtime-hardening.yaml
kubectl apply -f k8s/policy/gatekeeper/constraint-mohawk-runtime-hardening.yaml
```

Or via Makefile:

```bash
make policy-apply-gatekeeper
```

## Enforced controls

- `mohawk-control` must use pod `seccompProfile.type=RuntimeDefault` and non-privileged containers.
- `mohawk-datapath` must use pod `seccompProfile.type=RuntimeDefault` and privileged containers in accelerated profile.
- `mohawk-datapath-unprivileged` must use pod `seccompProfile.type=RuntimeDefault`, `allowPrivilegeEscalation=false`, and drop `ALL` capabilities.

## Validation

Local check (requires a Kubernetes context):

```bash
make policy-validate
```

CI workflow:


Strict server-side mode (workflow dispatch):

 - The strict job also publishes the same summary to the GitHub workflow Step Summary panel.

Local strict mode:

```bash
make policy-validate-strict
```

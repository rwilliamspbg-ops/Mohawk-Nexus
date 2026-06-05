# Security Policy

## Supported versions

Security fixes are prioritized for the latest main branch and the most recent tagged release.

## Reporting a vulnerability

Please do not open a public issue for vulnerabilities.

Report privately with:

- Affected component(s)
- Reproduction steps
- Impact assessment
- Suggested remediation (if available)

Preferred contact path:

- Open a private security advisory in GitHub for this repository.

If private advisory access is not available, contact maintainers through the repository owner profile and request secure handling.

## Disclosure process

1. Maintainers acknowledge receipt within 5 business days.
2. Maintainers triage and reproduce.
3. A fix and release window is coordinated.
4. Public disclosure follows patch availability.

## Security hardening scope

For AF_XDP and privileged deployments, review:

- SECURITY_SECRETS.md
- DEPLOYMENT.md
- k8s manifests for capabilities and runtime security context

## Operational hardening checklist

For accelerated AF_XDP environments, verify the following before production rollout:

- Runtime confinement:
- Pod seccomp profile is `RuntimeDefault`.
- Only datapath runs with `privileged: true` in accelerated profile.
- Non-accelerated datapath uses `allowPrivilegeEscalation: false` and drops all capabilities.

- Host and kernel controls:
- Dedicated datapath nodes with constrained scheduling.
- IRQ affinity, hugepage sizing, and NIC queue pinning are explicitly configured.
- Unused kernel modules are disabled on datapath nodes.

- Cluster policy:
- Admission policy restricts privileged pods to namespace `mohawk` and expected service accounts only.
- NetworkPolicy is enforced for control/datapath/FL/SWIP traffic boundaries.
- Apply one policy engine profile from `k8s/policy/` (Kyverno or Gatekeeper) to enforce runtime hardening at admission time.

- Verification gates:
- Run `bash scripts/check_afxdp_prereqs.sh --require` for accelerated hosts.
- Run `bash scripts/check_k8s_runtime_hardening.sh accelerated` after deployment.
- Ensure `bridge-e2e` workflow accelerated job passes before promotion.

## Dependency security

This repository uses automated dependency update tooling and CI security checks where possible.

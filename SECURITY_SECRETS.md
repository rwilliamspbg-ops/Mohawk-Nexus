# Secrets & Credentials

This file explains recommended practices for handling secrets (credentials, API tokens, TLS keys) for the Mohawk Nexus workspace.

Local development
- Use `.env` (copy from `.env.example`) for local values. Do NOT commit `.env` to Git.
- Example: `cp .env.example .env && edit .env`.

CI / Production
- Use your CI provider's secret store or a dedicated secrets manager (HashiCorp Vault, AWS Secrets Manager, GitHub Secrets).
- When building/pushing images in CI, inject credentials as environment variables rather than saving them to disk.

Grafana
- Set `GF_SECURITY_ADMIN_PASSWORD` via CI secret or Vault. Avoid embedding plaintext passwords in repository files.

GHCR
- When publishing images to GitHub Container Registry, use `GHCR_USERNAME` and `GHCR_TOKEN` from your CI secrets.

TLS and certificates
- Store TLS keys in a secrets manager or Kubernetes `Secret` objects. Mount them into containers at runtime or use sidecar injection.

Rotating and revoking
- Use short-lived tokens where possible and rotate credentials regularly.

# Security & Compliance

**Protecting data, ensuring compliance.**

## Security Policies

### Password Requirements
- Minimum 14 characters
- 1 uppercase, 1 lowercase, 1 digit, 1 special character
- No dictionary words
- Changed every 90 days

### Access Control
- RBAC enforced at all levels
- MFA required for production access
- API keys rotated monthly
- SSH keys: ed25519, no older than 2 years

### Network Security
- TLS 1.3 for all connections
- mTLS between aggregators
- Rate limiting: 1000 req/min per API key
- DDoS protection enabled

## HIPAA Compliance (Healthcare)

### Data Protection
- Patient data stays on-device (hospital only)
- Models aggregate without revealing source data
- Encryption in transit (TLS 1.3)
- Encryption at rest (AES-256-GCM)

### Access Control
```yaml
Healthcare Deployment:
  authentication:
    - MFA required
    - SAML/OAuth for hospitals
    - API keys for services
  authorization:
    - RBAC (Role-Based Access Control)
    - Data access logs audited
    - Patient ID never stored
```

### Audit Logging
- All API calls logged with timestamp
- User identity recorded
- Data access tracked
- Retention: 6 years (HIPAA requirement)

### Breach Notification
```bash
# If breach suspected:
1. Contact security@mohawk-nexus.org
2. Incident response within 24 hours
3. Notification to affected hospitals
4. Report to HHS (if required)
```

## GDPR Compliance (Data Protection)

### Data Minimization
- Only necessary data collected
- Automatic purge after retention period
- No profiling without consent
- Right to erasure honored

### Article 32: Technical Safeguards
```yaml
Implementation:
  pseudonymization: "Patient IDs hashed with salt"
  encryption: "AES-256 at rest, TLS 1.3 in transit"
  availability: "Byzantine consensus ensures 99.99%"
  resilience: "Backup restore in <1 hour"
  testing: "Annual penetration testing"
```

### DPIA (Data Protection Impact Assessment)
```bash
# Automatic DPIA generation
kubectl exec -n mohawk pod/mohawk-core -- \
  ./generate-dpia.sh > dpia-evidence.json

# Evidence includes:
# - Data collection methods
# - Processing purposes
# - Legitimate interests
# - Risk assessment
# - Mitigation measures
```

### Consent Management
- Explicit consent obtained
- Easy withdrawal of consent
- Records maintained
- Shared with data processors

## Cryptographic Standards

### Key Exchange
```
Phase 1 (Now):
  - x25519: NIST-approved (256-bit security)
  - Expires: 2030 (when quantum threat emerges)

Phase 2 (2026):
  - Hybrid: x25519-mlkem768
  - x25519: NIST-approved
  - MLKem768: Post-quantum (NIST selected)
  - Protection: Both must break for compromise
```

### Signatures
```
Short-term (Update signing):
  - ECDSA over x25519
  - Speed: <1ms per signature
  - Usage: Update authentication

Long-term (Node identity):
  - XMSS (eXtendable Merkle Signature)
  - Speed: 10-100ms per signature
  - Advantage: Post-quantum secure
  - Key size: 4KB
```

### Hashing
```
Standard: SHA-3-256
Usage: Gradient compression, proof generation
Output size: 256 bits (256-bit security)
```

## Hardware Attestation

### TPM 2.0 Quotes
```bash
# TPM quotes node identity & platform state
# Ensures node hasn't been tampered with

# Flow:
1. Node generates TPM quote (10-100ms)
2. Quote includes: PCR values, firmware version
3. Aggregator verifies quote signature
4. Reject if PCR changed (firmware modified)
```

### XMSS Long-Term Verification
```
Backup verification without TPM:
  - XMSS provides post-quantum signature
  - Used if TPM fails
  - Slower (100ms) but verifiable
  - Prevents single-point failure
```

## Vulnerability Reporting

### Responsible Disclosure
```
Found a vulnerability?

1. DO NOT open public issue
2. Email: security@mohawk-nexus.org
3. Include:
   - Component affected
   - Vulnerability type
   - Reproduction steps
   - Impact assessment
   - Suggested fix (optional)

4. Timeline:
   - 24h: Acknowledgment
   - 7d: Initial assessment
   - 30d: Fix or mitigation plan
   - 60d: Public disclosure (coordinated)
```

### Bounty Program
- Critical ($5000): RCE, data breach, consensus breaking
- High ($1000): Auth bypass, privilege escalation
- Medium ($500): Information disclosure
- Low ($100): DoS, performance issues

## Audit Checklist

Before production deployment:

- [ ] TLS 1.3 enforced everywhere
- [ ] mTLS between aggregators
- [ ] API authentication enabled
- [ ] RBAC properly configured
- [ ] Audit logging active
- [ ] Regular backups tested
- [ ] Disaster recovery plan
- [ ] Security training completed
- [ ] Penetration test passed
- [ ] Compliance audit passed

## Rate Limiting

### API Rate Limits
```
Per API Key:
  - 1000 requests/minute (general)
  - 100 requests/minute (update submission)
  - 10 requests/minute (model download)

Per IP:
  - 10000 requests/minute

WebSocket:
  - 10 connections per IP
  - 1 message per second per connection
```

### Consensus Rate Limit
```
Update submission frequency:
  - Every 5-10 minutes (consensus cycle)
  - Faster submission triggers queuing
  - Queue limit: 10,000 updates
  - Overflow: Rejected with 503
```

## Secret Management

### API Keys
- Generated: 32-byte random
- Format: `mk_live_abcd1234...` or `mk_test_xyz...`
- Rotation: Monthly
- Revocation: Immediate

### Database Credentials
```bash
# Store in Kubernetes Secret
kubectl create secret generic db-creds \
  --from-literal=password=YOUR_PASSWORD \
  -n mohawk

# Reference in deployment
valueFrom:
  secretKeyRef:
    name: db-creds
    key: password
```

### TPM Keys
- Stored: Hardware TPM 2.0
- Not exportable
- Protected by: Chip firmware
- Rotation: Annual

## Monitoring Security

### Security Events
```bash
# Monitor security logs
kubectl logs deployment/mohawk-core -n mohawk | grep "security"

# Check authentication failures
kubectl logs deployment/mohawk-core -n mohawk | grep "auth_fail"

# Monitor proof failures
kubectl logs deployment/mohawk-core -n mohawk | grep "proof_failed"
```

### Intrusion Detection
```yaml
Monitored:
  - Failed authentication attempts (trigger alert at 5/min)
  - Invalid proofs (trigger alert at 10/hour)
  - Unauthorized API access (trigger alert immediately)
  - Rate limit exceeded (logged, client throttled)
```

## Disaster Recovery

### Backup Strategy
```
Frequency: Daily
Retention: 30 days
Encryption: AES-256-GCM
Location: Off-site (encrypted)

Components backed up:
  - PostgreSQL state
  - Consensus ledger
  - Configuration
  - Key material (encrypted)
```

### Recovery Procedure
```bash
# 1. Verify backup integrity
./verify-backup.sh backup-2026-05-04.tar.gz

# 2. Restore database
kubectl exec pod/postgresql -- \
  pg_restore < backup.sql

# 3. Verify consensus
kubectl logs deployment/mohawk-core | grep "consensus"

# 4. Test recovery
curl http://localhost:8080/health
```

## Incident Response

### 24-Hour Response
```
If security incident detected:

1. Hour 0: Acknowledge, isolate affected systems
2. Hour 1: Gather evidence, preserve logs
3. Hour 4: Initial assessment, notify stakeholders
4. Hour 8: Mitigation deployed
5. Hour 24: Post-incident review scheduled
```

### Escalation
```
Level 1 (Developer): Debug logs, minor issues
Level 2 (Security team): Vulnerabilities, auth failures
Level 3 (Management): Data breach, compliance issue
Level 4 (Board): Multi-hospital impact, regulatory
```

---

See [`docs/README.md`](README.md) for full documentation.

---

[← Back to Docs Index](README.md)

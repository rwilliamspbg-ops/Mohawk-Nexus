# CONTRIBUTING.md

## Contributing to Mohawk Nexus

Thank you for your interest in building sovereign, verifiable AI infrastructure. This guide covers contribution workflows, standards, and security practices.

## Code of Conduct

We enforce a **no-trolling, no-harassment** standard. Violations result in immediate issue closure and contributor ban.

## Contribution Categories

### 1. Core Runtime (Sovereign-Mohawk-Proto)
**Requires**: Go, Lean4, cryptographic literacy

- **Bug Fixes**: File issue with reproducer; PRs welcome
- **Feature Additions**: Require RFC (design doc) + security review
- **Consensus Changes**: Require formal Lean4 proof of correctness
- **Cryptographic Changes**: Require 3rd-party crypto audit before merge

### 2. Federated Learning Stack (Sovereign-Map*, Sovereign_Map_FL)
**Requires**: Python, distributed systems knowledge

- **New Aggregation Methods**: Benchmarks + convergence proofs required
- **Policy Additions**: Must NOT break existing policies
- **Observability**: Prometheus/Grafana expertise welcome

### 3. Vertical Applications (Oncology, Agriculture, Climate, SupplyChain)
**Requires**: Domain-specific ML expertise + compliance knowledge

- **Healthcare (Oncology)**: HIPAA compliance officer review
- **Agriculture**: Sustainability data science expertise
- **Climate**: Environmental modeling expertise
- **Supply Chain**: Logistics optimization expertise

### 4. Infrastructure (NVFlare, Flower, TheRock)
**Requires**: Dependency maintenance + benchmarking

- **Version Bumps**: Automated dependency updates welcome
- **Optimization**: Performance improvements with benchmarks
- **Compatibility**: New hardware support (TPU, NPU, ROCm)

### 5. Documentation & Website
**Requires**: Writing, diagramming, UX clarity

- **API Docs**: Auto-generated from code; PRs for manual docs welcome
- **Tutorials**: New deployment scenarios + step-by-step guides
- **Architecture Diagrams**: Mermaid, PlantUML, or Figma

## Workflow

### 1. Fork & Clone
```bash
git clone https://github.com/YOUR-USERNAME/Mohawk-Nexus.git
cd Mohawk-Nexus
git remote add upstream https://github.com/rwilliamspbg-ops/Mohawk-Nexus.git
```

### 2. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 3. Develop & Test

#### For Core Runtime:
```bash
cd modules/Sovereign-Mohawk-Proto
go test ./...
cargo test --release  # if Rust component
lean4 verify --all    # formal proofs
```

#### For FL Stack:
```bash
cd modules/Sovereign_Map_Federated_Learning
pytest tests/
python -m black --check .
python -m pylint --rating-scale=10 mohawk/
```

#### For Verticals:
```bash
cd modules/Sovereign_Mohawk_Oncology_Global
npm test
npm run lint
```

### 4. Commit with Audit Trail
```bash
git commit -m "Add post-quantum key exchange verification" \
           -m "" \
           -m "- Implements x25519-mlkem768 hybrid KEX
              - Adds Lean4 proof of IND-CCA2 security
              - Benchmarks: <5ms key derivation overhead
              - Breaks: None; backward-compatible via fallback" \
           -m "Assisted-By: Mohawk-Nexus"
```

### 5. Push & Open PR
```bash
git push origin feature/your-feature-name
# Open PR on GitHub; include:
# - What problem does this solve?
# - Metrics (performance, security, compliance impact)
# - Testing performed
# - Breaking changes (if any)
```

### 6. Address Review Feedback
```bash
# Iterate on feedback; avoid force-pushing unless explicitly asked
git commit --amend  # for cosmetic fixes
git commit          # for substantive changes (preserves history)
git push origin feature/your-feature-name
```

### 7. Merge (Maintainer Action)
Once approved:
```bash
# Squash small commits; preserve history for major changes
git merge --squash feature/your-feature-name  # OR
git merge feature/your-feature-name
git push upstream main
```

## Standards & Requirements

### Security Reviews

**High-Risk Changes** (require external review before merge):
- Cryptographic algorithms or key management
- Consensus protocol modifications
- Network protocol changes
- Data serialization/deserialization

**Checklist**:
- [ ] No hardcoded secrets
- [ ] No eval() / unsafe deserialization
- [ ] Input validation on all external inputs
- [ ] No timing attacks (if cryptographic)
- [ ] Rate limiting on network I/O

### Formal Verification (Core Runtime Only)

For consensus or cryptographic changes:
```lean4
-- Example: Prove Byzantine consensus correctness with ≤1/3 faults
theorem consensus_correct (fault_nodes : ℕ) (total : ℕ) :
  fault_nodes ≤ (total / 3) → eventually_agree_all_honest := by
  sorry  -- Your proof here
```

Submit `.lean` proofs alongside code PRs.

### Testing

**Core Runtime**: >90% code coverage
```bash
go test -cover ./...
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

**FL Stack**: >80% code coverage + property-based tests
```bash
pytest --cov=mohawk tests/ --cov-report=html
hypothesis examples/  # property-based tests
```

**Verticals**: >70% + integration tests with real data (anonymized)
```bash
npm test --coverage
npm run test:integration
```

### Performance Benchmarks

**Required for**:
- Consensus algorithm changes
- Aggregation protocol changes
- Cryptographic modifications

**Format**:
```markdown
## Benchmark Results

| Operation | Before | After | % Change |
|-----------|--------|-------|----------|
| zk-SNARK verify | 12ms | 9.5ms | -21% |
| BFT round | 250ms | 240ms | -4% |
| Memory/1M nodes | 2.1GB | 1.9GB | -10% |

Tested on: AWS c6i.4xlarge (16 vCPU, 32GB RAM)
```

### Compliance Documentation

For vertical applications (healthcare, agriculture, climate, supply chain):

**HIPAA** (Oncology):
```markdown
## Compliance Evidence

- [ ] Data Access Control: RBAC enforced
- [ ] Audit Logging: All model aggregations logged
- [ ] Encryption: Data encrypted at rest (AES-256) & in transit (TLS 1.3)
- [ ] Data Retention: Automatic purge after 90 days
- [ ] DPIA: Automated evidence generation (attached)
```

**GDPR** (All):
```markdown
## GDPR Article 32 (Security)

- [ ] Pseudonymization: Patient IDs hashed with salt
- [ ] Encryption: All keys >256 bits
- [ ] Integrity checks: zk-SNARKs verify computation
- [ ] Resilience: Byzantine consensus tolerates 1/3 failures
- [ ] Testing: Annual penetration testing required
```

## Code Style

### Go
- Follow [Effective Go](https://golang.org/doc/effective_go)
- `gofmt`, `goimports`, `golangci-lint` required

### Python
- Black formatting, Pylint, Type hints (mypy)
- 79-char line limit (PEP 8)
- Docstrings on all public functions (Google style)

### JavaScript/TypeScript
- ESLint + Prettier
- No `any` types (strict mode)
- Unit tests for all exported functions

### Lean4
- Proof mode preferred over tactic mode (where readable)
- Document all theorems with `/-! ... -/` comments
- No `sorry` on main branch

## Release Process

### Version Numbering
```
v{major}.{minor}.{patch}-{tag}
v1.2.3-alpha       # Alpha release
v1.2.3-rc.1        # Release candidate
v1.2.3             # Stable release
v1.2.4-post-quantum # Post-quantum variant
```

### Changelog
All releases must include:
- [ ] `CHANGELOG.md` updated
- [ ] Security fixes flagged as `[SECURITY]`
- [ ] Breaking changes flagged as `[BREAKING]`
- [ ] Performance improvements quantified

### Tagging
```bash
git tag -a v1.2.3 -m "Release 1.2.3: PQC roadmap milestone" \
  -m "- x25519-mlkem768 hybrid KEX deployed" \
  -m "- 100M node scaling verified" \
  -m "- HIPAA audit evidence generation"
git push upstream v1.2.3
```

## Getting Help

- **Architecture Questions**: GitHub Discussions `[architecture]`
- **Security Bugs**: security@mohawk-nexus.org (responsible disclosure)
- **General Questions**: GitHub Issues with `[question]` tag
- **Design Feedback**: RFC issues `[rfc]`

## Maintainer Guidelines

Only repository admins can:
- [ ] Merge PRs
- [ ] Create releases
- [ ] Modify CI/CD
- [ ] Close security issues (after fix deployed)

---

**Thank you for building sovereign AI infrastructure with us!**

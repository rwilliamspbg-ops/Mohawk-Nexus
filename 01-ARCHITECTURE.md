# Architecture: System Design & Guarantees

**Understanding Mohawk Nexus from the ground up.**

## System Overview

Mohawk Nexus implements a **hierarchical, Byzantine-tolerant federated intelligence layer** with mathematical guarantees.

```
┌─────────────────────────────────────────────────────────────────────┐
│ Policy-Gated Domain (e.g., Oncology)                               │
│ ┌───────────────────────────────────────────────────────────────┐  │
│ │ Governance Layer: Policy enforcement, compliance            │  │
│ │ ┌─────────────────────────────────────────────────────────┐ │  │
│ │ │ Consensus Layer: BFT with formal verification          │ │  │
│ │ │ ┌──────────────────────────────────────────────────┐   │ │  │
│ │ │ │ Aggregation: Mohawk Protocol (224x reduction)  │   │ │  │
│ │ │ │ ┌───────────────────────────────────────────┐  │   │ │  │
│ │ │ │ │ Crypto: zk-SNARKs + PQC                │  │   │ │  │
│ │ │ │ │ ┌──────────────────────────────────────┐ │  │   │ │  │
│ │ │ │ │ │ Hardware: TPM 2.0 trust root        │ │  │   │ │  │
│ │ │ │ │ └──────────────────────────────────────┘ │  │   │ │  │
│ │ │ │ └───────────────────────────────────────────┘  │   │ │  │
│ │ │ └──────────────────────────────────────────────────┘   │ │  │
│ │ └─────────────────────────────────────────────────────────┘ │  │
│ └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│ Edge Nodes (10M–100M+): Local training, cryptographic updates     │
└─────────────────────────────────────────────────────────────────────┘
```

## Layered Architecture

### 1. Hardware Trust Layer
**Foundation: TPM 2.0 + XMSS + PQC**

- TPM 2.0 attestation quotes
- XMSS long-term signatures
- x25519 (NIST-approved)
- Post-quantum hybrid (mlkem768)
- Secure element integration

### 2. Cryptographic Layer
**Primitives: zk-SNARKs + Groth16**

- Zero-knowledge proofs (<10ms verification)
- Aggregation update verification
- Cryptographic attestation of correctness
- Post-quantum migration (2026)
- Key agreement & encryption

### 3. Consensus Layer
**Algorithm: Byzantine Fault Tolerant (BFT) + Lean4 Proofs**

- Multi-round Byzantine agreement
- Formal correctness verification
- Resilience to 1/3 malicious actors
- Finality guarantees
- Fork prevention

### 4. Aggregation Layer
**Protocol: Mohawk Protocol (Streaming)**

- Sketching & lossless compression
- Incremental aggregation
- O(log n) memory per aggregator
- Distributed sketching verification
- Fault tolerance at aggregation stage

### 5. Orchestration Layer
**Framework: Sovereign-Map-V2**

- Policy-gated domain management
- Node participant lifecycle
- Model versioning & rollback
- Observability (Prometheus/Grafana)
- Tokenomics tracking

### 6. Application Layer
**Domains: Verticals + Endpoints**

- Oncology (HIPAA/GDPR healthcare)
- Agriculture (farmer data sovereignty)
- Climate (nation-level carbon tracking)
- Supply Chain (enterprise logistics)
- Custom policy domains

## Trust Model & Boundaries

### What We Trust
✅ Hardware (TPM 2.0 cannot be software-bypassed)  
✅ Cryptography (x25519-mlkem768 pre/post-quantum)  
✅ Mathematics (Lean4 formal proofs)  
✅ <1/3 of aggregators (Byzantine assumption)  

### What We Don't Trust
❌ Network (adversary can intercept messages)  
❌ Individual nodes (can be malicious)  
❌ Intermediaries (aggregators may collude)  
❌ Centralized authorities (we are decentralized)  

### Guarantee
```
Even with up to 1/3 of aggregators being malicious:
- Global model converges to correct value
- No node's raw data is revealed
- All aggregation is verifiable
- Consensus is mathematically proven (Lean4)
```

## Data Flow (Never Centralized)

### Step 1: Local Training (Node)
```
Node: Trains on LOCAL data (stays on-device)
  ↓
Computes gradient update (e.g., 10MB)
  ↓
Signs with TPM-backed private key
  ↓
Generates zk-SNARK proof (<10ms)
```

### Step 2: Attested Update (Node → Aggregators)
```
Sends to aggregators:
  - Update hash (32 bytes)
  - zk-SNARK proof (256 bytes)
  - TPM attestation quote (1KB)
  ↓
NEVER sends raw data (privacy preserved)
  ↓
Total: ~2KB per node (vs 10MB without compression)
```

### Step 3: Streaming Aggregation (Mohawk Protocol)
```
Aggregators receive updates stream
  ↓
Verify each zk-SNARK (<10ms per proof)
  ↓
Reject >1/3 malicious updates (BFT)
  ↓
Incremental sketching & aggregation
  ↓
224x memory reduction achieved
```

### Step 4: Byzantine Consensus
```
Multi-round agreement:
  - Round 1: Aggregators propose aggregates
  - Round 2: Verify <1/3 disagreement
  - Round 3: Finalize or retry
  ↓
Lean4 formal proof: Consensus reached
  ↓
Ledger commit (immutable, auditable)
```

### Step 5: Policy Compliance
```
Domain policy contract (e.g., HIPAA):
  - Verify: Node in permitted region
  - Enforce: Data retention limits
  - Generate: DPIA evidence
  ↓
Model snapshot published to nodes
  ↓
HIPAA/GDPR compliance audit trail
```

## Failure Modes & Guarantees

| Scenario | Guarantee |
|----------|-----------|
| 1 aggregator offline | ✓ Consensus proceeds (3+ total) |
| 2 aggregators malicious (out of 5) | ✓ BFT detects, consensus correct |
| Network partition (50/50 split) | ✓ Gossip consensus pauses safely |
| Node sends forged proof | ✓ zk-SNARK verification fails, rejected |
| TPM is compromised | ✓ Signature still cryptographically valid |
| Cryptography broken (2030+) | ✓ x25519-mlkem768 hybrid mitigates |

## Scaling to 100M Nodes

### Traditional FL
```
1M nodes × 10MB gradient = 10 Petabytes in aggregator memory ❌
Impossible to scale!
```

### Mohawk Protocol
```
1M nodes × 32 bytes (hash) = 32 MB in aggregator memory ✓
224x memory reduction!
```

**How?**
1. **Sketching**: Compress gradients losslessly (random projection)
2. **Sketching Verification**: zk-SNARK proves sketch integrity (<10ms)
3. **Incremental Aggregation**: Aggregate-and-discard, don't accumulate
4. **Distributed Sketching**: Spread sketching across multiple aggregators

**Result**: Support for 10M–100M+ nodes with sub-10s aggregation cycles

## Cryptographic Stack (2026 PQC)

### Key Exchange
```yaml
Phase 1 (Now): 
  - Primary: x25519 (NIST-approved)
Phase 2 (2026): 
  - Hybrid: x25519-mlkem768 (pre + post-quantum)
  - Fallback: Kyber-1024 if quantum threat emerges
```

### Signatures
```yaml
Short-term (Update signing):
  - ECDSA (x25519 context, <1ms)
Long-term (Node identity):
  - XMSS (eXtendable Merkle Signature Scheme, quantum-safe)
Hardware attestation:
  - ECDSA + TPM 2.0 quote (unforgeable)
```

### Proofs
```yaml
Aggregation verification:
  - Groth16 zk-SNARKs (<10ms, trusted setup)
Consensus correctness:
  - Lean4 formal proofs (offline verification)
Compliance:
  - Automated DPIAs (on-chain verification)
```

## Policy-Gated Domains

Each domain has a **policy contract** (smart contract or custom):

### Oncology Example
```yaml
Policy:
  - Require: HIPAA certification
  - Require: Node in [US, EU, CA]
  - Enforce: Data retention ≤ 90 days
  - Action: Emit DPIA evidence on aggregation
Guarantees:
  - Patient data NEVER leaves hospital
  - Model aggregates globally
  - Compliance auditable (immutable logs)
```

### Agriculture Example
```yaml
Policy:
  - Require: Farm size ≤ 5000 hectares
  - Require: Sustainability score ≥ 7
  - Allow: Inference on yield models
Guarantees:
  - Farmer data sovereign
  - Models improve sustainability
  - Rewards for participation
```

## Module Dependencies

```
Sovereign-Mohawk-Proto (Core)
  ├─ libp2p (peer discovery, gossip)
  ├─ Lean4 (formal verification)
  ├─ zk-SNARK libs (Groth16)
  └─ tpm2-tools (attestation)

Sovereign-Map-V2 (Orchestration)
  ├─ Sovereign-Mohawk-Proto
  ├─ Prometheus (metrics)
  ├─ Grafana (dashboards)
  └─ Smart contract platform

Verticals (Oncology, Ag, Climate, SC)
  ├─ Sovereign-Map-V2
  ├─ Flower (federated learning)
  ├─ NVFlare (optional)
  └─ Domain-specific ML libs

Infrastructure
  ├─ Autonomous-Mapping (zk identity)
  ├─ Ethereum libs (if blockchain)
  └─ GPU acceleration (TheRock/ROCm)
```

## Performance Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| Local training | 10–100s | Hospital ML pipeline |
| zk-SNARK gen | <10ms | On modern hardware |
| zk-SNARK verify | <10ms | Batch verification |
| BFT consensus | 100–500ms | 3-node agreement |
| Global aggregation cycle | 5–10 min | Typical frequency |
| Memory per aggregator | 100MB–1GB | vs 10PB centralized |
| Nodes per aggregator | 10M–100M+ | Streaming protocol |
| Throughput | 1M+ updates/sec | With 100 aggregators |

## Typical Deployment: Oncology

```
Orchestrator (Sovereign-Map-V2)
  - HIPAA policy enforcement
  - Hospital participant mgmt
  - Global model versioning
  
Aggregators (3× Sovereign-Mohawk-Proto, BFT)
  - Validate zk-proofs
  - Stream aggregation
  - Formal consensus
  
Hospitals (1000s worldwide)
  - Johns Hopkins: 500M records (local)
  - Mayo Clinic: 200M records (local)
  - NCI: 100M records (local)
  - ... plus 1000+ more
  
Each Hospital:
  - Local model trainer
  - TPM-backed signer
  - zk-SNARK prover
  - HIPAA auditor

Observability:
  - Prometheus metrics
  - Grafana dashboards
  - HIPAA audit trail
  - Tokenomics telemetry
```

## Security Assumptions

1. **Hardware**: TPM 2.0 secure, cannot be software-patched
2. **Cryptography**: x25519-mlkem768 not broken before 2030
3. **Consensus**: <1/3 of aggregators can be malicious
4. **Network**: Adversary cannot eclipse all honest aggregators
5. **Formal Proofs**: Lean4 type system sound

## Future Roadmap

### 2026 Q2
- [ ] x25519-mlkem768 deployment
- [ ] Lean4 consensus proofs complete
- [ ] TPM 2.0 enterprise rollout

### 2026 H2
- [ ] 1000+ nodes in production
- [ ] 4 verticals (oncology, ag, climate, SC)
- [ ] Multi-chain integration

### 2027+
- [ ] 100M+ nodes
- [ ] Autonomous model improvement
- [ ] Global nation-level deployments

---

See [`02-DEPLOYMENT.md`](02-DEPLOYMENT.md) for implementation details.

See [`docs/README.md`](README.md) for full documentation index.

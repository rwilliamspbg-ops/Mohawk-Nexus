# API Reference

**SDK and API Documentation.**

## Python SDK

### Installation
```bash
pip install mohawk-nexus
```

### Basic Usage
```python
import mohawk

# Initialize client
client = mohawk.Client(
    orchestrator_url="http://localhost:8080",
    domain="oncology",
    node_id="hospital-123"
)

# Get client version
print(client.version())  # "v1.0.0"

# Participate in federated learning
model = client.get_latest_model()
loss = client.train_local(model, local_data)
update = model.compute_gradient()
client.submit_update(update)

# Get updated model
new_model = client.get_latest_model()
```

### Training Loop
```python
from mohawk import Client, LocalTrainer

client = Client(orchestrator_url="http://localhost:8080")

for epoch in range(10):
    # Download global model
    global_model = client.get_model()
    
    # Train locally
    trainer = LocalTrainer(global_model)
    new_weights = trainer.fit(local_data, epochs=1)
    
    # Submit update
    proof = client.generate_proof(new_weights)
    client.submit_update(new_weights, proof)
    
    # Evaluate
    accuracy = trainer.evaluate(test_data)
    print(f"Epoch {epoch}: {accuracy:.2%}")
```

## Go API

### Installation
```bash
go get github.com/rwilliamspbg-ops/mohawk-nexus/consensus
```

### Basic Usage
```go
package main

import (
    "github.com/rwilliamspbg-ops/mohawk-nexus/consensus"
)

func main() {
    // Create aggregator
    agg := consensus.NewAggregator(
        consensus.WithMaxFaults(1),
        consensus.WithMemoryLimit(1024 * 1024 * 1024),
    )
    
    // Start consensus
    agg.Start()
    defer agg.Stop()
    
    // Receive updates
    for update := range agg.Updates() {
        verified, err := agg.Verify(update)
        if verified {
            agg.Aggregate(update)
        }
    }
}
```

## TypeScript API

### Installation
```bash
npm install @mohawk-nexus/orchestration
```

### Basic Usage
```typescript
import { Orchestrator } from '@mohawk-nexus/orchestration';

const orchestrator = new Orchestrator({
  domain: 'oncology',
  policyUrl: 'http://policy-contract.local',
  nodeLimit: 10000000,
});

// Enroll node
const enrollment = await orchestrator.enrollNode({
  nodeId: 'hospital-123',
  region: 'US',
  capabilities: ['federated-learning', 'zk-proofs'],
});

// Get model
const model = await orchestrator.getLatestModel();

// Submit update
await orchestrator.submitUpdate({
  nodeId: 'hospital-123',
  update: modelUpdate,
  proof: zkProof,
});
```

## REST API

### Health Check
```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "version": "v1.0.0",
  "aggregators": 3,
  "nodes": 1234567
}
```

### Get Model
```bash
GET /api/v1/model/latest
```

Response:
```json
{
  "version": 42,
  "weights": [...],
  "timestamp": "2026-05-04T10:30:00Z"
}
```

### Submit Update
```bash
POST /api/v1/update/submit

{
  "node_id": "hospital-123",
  "update": [...weights...],
  "proof": "0xzk_snark_proof",
  "attestation": "tpm_quote"
}
```

Response:
```json
{
  "accepted": true,
  "update_id": "upd_abc123",
  "next_aggregation_in_seconds": 300
}
```

### Get Metrics
```bash
GET /metrics
```

Returns Prometheus-format metrics:
```
# HELP consensus_rounds_total Total consensus rounds
# TYPE consensus_rounds_total counter
consensus_rounds_total 1234

# HELP aggregation_latency_ms Aggregation latency in ms
# TYPE aggregation_latency_ms histogram
aggregation_latency_ms_bucket{le="10"} 100
aggregation_latency_ms_bucket{le="100"} 500
```

## WebSocket API

### Connect
```javascript
const ws = new WebSocket('ws://localhost:8080/stream/updates');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log('New model aggregated:', update.model_version);
};
```

### Subscribe to Events
```javascript
ws.send(JSON.stringify({
  event: 'subscribe',
  channel: 'model_updates'
}));

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  if (message.type === 'model_update') {
    console.log('New model version:', message.version);
  }
};
```

## Error Handling

### Python
```python
from mohawk.exceptions import (
    ProofVerificationError,
    PolicyViolation,
    NetworkError
)

try:
    client.submit_update(update, proof)
except ProofVerificationError as e:
    print(f"Proof invalid: {e}")
except PolicyViolation as e:
    print(f"Policy check failed: {e}")
except NetworkError as e:
    print(f"Network error: {e}")
```

### Go
```go
update, err := agg.Verify(rawUpdate)
if err != nil {
    switch err.(type) {
    case *consensus.ProofError:
        // Handle proof verification failure
    case *consensus.PolicyError:
        // Handle policy violation
    default:
        // Handle other errors
    }
    return
}
```

## Authentication

### API Key
```bash
curl -H "X-API-Key: your-api-key" \
  http://localhost:8080/api/v1/model/latest
```

### Client Certificates (for production)
```bash
curl --cert client.crt --key client.key \
  https://production.mohawk.local/api/v1/model/latest
```

## Rate Limiting

- 1000 requests per minute per API key
- WebSocket connections: 10 per IP
- Update submissions: Limited by consensus cycle (5-10 min)

## Code Examples

### Python: Full Training Loop
```python
from mohawk import Client, LocalTrainer
from data import load_dataset

client = Client(orchestrator_url="https://api.mohawk.local")
train_data, test_data = load_dataset()

for round in range(100):
    # Get current model
    model = client.get_model()
    
    # Train locally
    trainer = LocalTrainer(model, batch_size=32, epochs=1)
    new_weights = trainer.fit(train_data)
    
    # Generate proof
    proof = client.generate_proof(new_weights)
    
    # Submit
    result = client.submit_update(new_weights, proof)
    print(f"Round {round}: {result.status}")
    
    # Evaluate on test set
    accuracy = trainer.evaluate(test_data)
    print(f"  Accuracy: {accuracy:.2%}")
```

### Go: Custom Aggregation
```go
package main

import (
    "log"
    "github.com/rwilliamspbg-ops/mohawk-nexus/consensus"
)

func main() {
    agg := consensus.NewAggregator(consensus.WithMaxFaults(1))
    agg.Start()
    defer agg.Stop()
    
    for {
        select {
        case update := <-agg.Updates():
            proof := update.Proof
            verified, err := consensus.VerifyProof(proof)
            if verified {
                agg.Aggregate(update)
            } else {
                log.Printf("Proof verification failed: %v", err)
            }
        }
    }
}
```

### TypeScript: Monitoring
```typescript
import { Orchestrator } from '@mohawk-nexus/orchestration';

const orchestrator = new Orchestrator({
  domain: 'agriculture',
  metricsUrl: 'http://prometheus:9090'
});

const metrics = await orchestrator.getMetrics();
console.log(`
  Consensus Rounds: ${metrics.consensusRoundsTotal}
  Aggregation Latency: ${metrics.aggregationLatencyMs}avg ms
  Active Nodes: ${metrics.activeNodes}
  Model Version: ${metrics.latestModelVersion}
`);
```

See [`docs/README.md`](README.md) for full documentation.

---

[← Back to Docs Index](README.md)

# Context Appetite Pilot

`context-appetite` tests whether an agent should answer, acquire more evidence,
or stop because the available evidence cannot justify an answer. This first
five-task pilot is for learning and verifier validation, not leaderboard use.

| Task | Initial context | Hidden truth | Available observations and evidence cost | Valid terminal response | Targeted failure mode |
| --- | --- | --- | --- | --- | --- |
| `deployment-outage` | Checkout began returning HTTP 500 errors at 14:32 UTC after several systems changed. | `checkout-api-2026.07.22.4` was the deployment rolled back immediately before recovery. | `record-c` (300): incident timing, no deployment ID; `record-a` (2,000): operation and rollback IDs; `record-d` (8,000): responder conclusions without the exact ID; `record-b` (12,000): service metrics without operation IDs. | `checkout-api-2026.07.22.4`, after opening `record-a`. | Treating a reasonable cheap first read or corroborating read as irrational. Extra acquisition is reported only as a hindsight cost gap. |
| `answer-now` | The approved ticket already names the rolled-back deployment and records recovery. | `billing-api-2026.07.22.7` was rolled back immediately before invoice generation recovered. | `record-b` (450): recovery health check, no ID; `record-c` (1,500): unrelated worker rollout; `record-d` (3,200): responder discussion, no exact ID; `record-a` (9,000): redundant change archive. | `billing-api-2026.07.22.7` without opening evidence. | Reflexive tool use, distraction by nearby changes, and failure to trust sufficient initial context. |
| `complementary-evidence` | Export request `req-7f9` moved protected data, but its tenant and credential are not identified initially. | The request used `key-prod-19`, owned by `tenant-orchid`. | `record-a` (300): unrelated customer notice; `record-d` (700): request-to-key gateway mapping; `record-b` (1,800): key-to-tenant registry mapping; `record-c` (6,000): object counts without identity. | `tenant-orchid:key-prod-19`, after opening `record-d` and `record-b`. | Stopping after one plausible partial record instead of joining complementary evidence. |
| `insufficient-evidence` | Search latency rose after two near-simultaneous component changes. | The corpus identifies both candidates but cannot distinguish which one caused the incident. | `record-c` (500): the two deployment IDs and times; `record-a` (1,400): simultaneous anomalies without directionality; `record-d` (2,200): bundled rollback and recovery; `record-b` (9,000): customer impact without causal evidence. | `INSUFFICIENT:search-api-2026.07.22.5,cache-router-2026.07.22.2`, after opening `record-c`, `record-a`, and `record-d`. | Guessing from temporal proximity, omitting the candidates, or treating bundled recovery as unique causal attribution. |
| `unreliable-or-conflicting-evidence` | Quote `Q-884` overstated available H100 capacity. | Its stored payload came from `feed-west`. | `record-a` (300): unsigned note claiming `feed-north`; `record-d` (500): immutable quote-to-payload-hash ledger; `record-b` (1,700): signed payload-hash-to-feed receipt; `record-c` (2,400): generated summary derived only from `record-a`. | `feed-west`, after opening `record-d` and `record-b`. | Counting correlated claims as independent confirmation or ignoring source provenance. |

Across the pilot, exact task success and verifier integrity are the hard gate.
Observed evidence cost is reported separately. `hindsight_minimum_cost`,
`hindsight_cost_gap`, and `sources_outside_hindsight_minimum` describe the
completed trajectory; they do not claim that the agent acted irrationally
under uncertainty.

## What This Measures

The pilot measures exact decisions over a free metadata catalog and synthetic
priced evidence. `evidence list` and `evidence status` cost zero credits but are
logged. Opening a record logs its synthetic evidence credits, UTF-8 payload
bytes, and a deterministic token proxy of `ceil(bytes / 4)`. The proxy is not
the agent model's token usage; Harbor trajectory telemetry remains the source
for real model tokens and provider cost.

`unreliable-or-conflicting-evidence` is intentionally a metadata-reliability
condition: the free catalog exposes provenance classes such as signed,
generated, and immutable. It does not test discovering reliability labels from
the payload alone.

Each task has one deterministic proof contract. Benchmark reward is binary:
the exact answer or valid structured abstention, required evidence, and
verifier integrity must all pass. Evidence cost, source sequence, catalog
calls, actual payload size, and hindsight gaps stay separate diagnostics. An
expensive correct path therefore remains a success, while a cheap wrong or
memorized answer receives zero.

## Architecture

The Harbor `main` service runs the agent as a non-root user and contains only
the `evidence` CLI. A separate non-root evidence sidecar owns the closed corpus
and append-only event ledger. Its final snapshot requires a random credential
created inside that sidecar's filesystem; loopback access from the agent is not
enough to finalize it. Harbor's normal separate-verifier flow stops the main
service before running the authenticated collect hook. The first valid hook
finalizes the ledger, later calls are rejected, and a missing or malformed
artifact fails closed. Harbor then rehydrates the snapshot at
`/evidence-artifacts/state.json` in a separate no-network verifier. The
deterministic verifier image contains the expected answer and scoring contract.

Agent-authored probe telemetry is deliberately not trusted. Separation is an
integration invariant covered by image/config tests and the Modal Oracle smoke.

## Security Boundary

The task declares public agent egress. Harbor 0.20's default Modal Compose
path runs nested Docker under gVisor with host networking; in our Terminus 2
preflight, that path also prevented `tmux` from forking. Real-agent runs use
Harbor's experimental `modal_vm_runtime=true` path instead. It retains normal
Docker bridge networking between services, but it does not turn the agent's
public egress into a closed-corpus guarantee.

The protected sidecar prevents direct answer or ledger access, but a public
static task contract can be fetched from its repository after publication.
These five tasks are development and plumbing cases, not a secure held-out
evaluation or public leaderboard.

Model pilots should run before the repaired contracts are published, or from
private/runtime-generated task packages. A defensible public evaluation also
needs enforced closed egress or opaque generated instances. Record
`agent_egress` and `contract_visibility` in every run manifest.

## Runbook

Pin the Modal extra directly:

```bash
uvx --from 'harbor[modal]==0.20.0' harbor run \
  -p tasks/context-appetite \
  -a oracle \
  -e modal \
  -o jobs-scratch \
  --job-name context-appetite-v0.2.1-oracle-smoke-001 \
  -n 2 \
  --ek modal_vm_runtime=true
```

Before making a model call, verify Terminus 2 setup in the same runtime:

```bash
uvx --from 'harbor[modal]==0.20.0' harbor run \
  -p tasks/context-appetite \
  -i deployment-outage \
  -a terminus-2 \
  -m openrouter/deepseek/deepseek-v4-flash \
  -e modal \
  -o jobs-scratch \
  --job-name context-appetite-v0.2.1-modal-vm-t2-preflight-001 \
  --install-only \
  --max-retries 0 \
  -n 1 \
  --ek modal_vm_runtime=true
```

After the Oracle and install-only preflight are green, run the inexpensive
Terminus 2 canary:

```bash
uvx --from 'harbor[modal]==0.20.0' harbor run \
  -p tasks/context-appetite \
  -a terminus-2 \
  -m openrouter/deepseek/deepseek-v4-flash \
  -e modal \
  -o jobs-scratch \
  --job-name context-appetite-v0.2.1-openrouter-canary-001 \
  --max-retries 0 \
  -n 1 \
  --ek modal_vm_runtime=true
```

Oracle, install checks, and canaries belong in `jobs-scratch/`. Predeclared
model pilots belong in `jobs/`, including their infrastructure failures. Raw
Harbor jobs are retained; the website and reports should consume only
versioned files matching [`results/manifests/schema-v1.json`](../../results/manifests/schema-v1.json).
Oracle success proves solvability and plumbing, never model performance.

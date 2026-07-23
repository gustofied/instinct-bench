# Instinct Bench: Context Appetite v0.3.0

## Status

This document preregisters the v0.3.0 development and evaluation protocol. It
is the implementation contract for the next release and supersedes the earlier
72-trial presentation-control proposal. The frozen v0.2.1 pilot and its raw
results remain unchanged.

## Naming And Scope

- Suite: **Instinct Bench**
- Domain and Harbor dataset: `context-appetite`
- Release: **Instinct Bench: Context Appetite v0.3.0**
- Public development dataset: `instinct-bench/context-appetite-dev@v0.3.0`
- Intended held-out dataset ref: `instinct-bench/context-appetite@v0.3.0`

The five labels below are experimental conditions, not another family layer:

1. `answer-now`
2. `single-source`
3. `complementary-evidence`
4. `insufficient-evidence`
5. `reliability-conflict`

One Harbor task is one instruction, environment, and verifier. The Harbor
dataset is the collection of tasks. Conceptually, the project remains
suite -> domain -> tasks.

## Claim

Context Appetite v0.3.0 measures whether an agent can **answer, look, abstain,
or stop** while acquiring priced evidence in a declared information
environment. It reports valid decision-making and evidence use separately.

It does not test a clarification action, establish Bayes-optimality, measure
model intelligence in isolation, or support a general model leaderboard. The
official run characterizes one model-harness-sandbox configuration.

## Population And Split

The generator creates matched blocks. Each block expresses one latent decision
problem under all five evidence-necessity conditions.

- Development: 6 blocks x 5 conditions = 30 committed public tasks.
- Held-out evaluation: 15 new blocks x 5 conditions = 75 private tasks.
- Split unit: scenario block/template, never individual rows.
- Official model protocol: pass@1, one rollout per held-out task.

The exact 75-trial matrix is therefore:

```text
15 independent matched scenario blocks
x 5 evidence-necessity conditions
x 1 fixed model-harness rollout
= 75 unique trials
```

Held-out task IDs use the exact opaque set `ca-eval-001` through
`ca-eval-075`, assigned to condition/block cells through a release-secret-keyed
permutation. Dataset order is independently permuted from the same secret so it
does not reveal the condition cycle or create a fixed scheduling pattern.
Condition and block live in private release metadata. The release secret and
truth stay outside public metadata and outside the agent image.

## Decision Contract

Every task uses one short neutral instruction and exposes:

- initial-context authority and provenance;
- opaque evidence source IDs;
- source cost;
- authority class;
- declared reliability;
- correlation or lineage group;
- the same terminal payoff table.

Price and list position are counterbalanced independently of evidentiary role
across the release. Opaque identifiers are HMAC-derived. Authority,
reliability, and lineage are deliberately declared properties of the source
model rather than randomized noise; payload bytes are measured as a separate
diagnostic. Source costs are drawn from `1`, `2`, `4`, and `8`; the total
possible acquisition cost is `15`.

Within each matched block, the designated first proof source has the same
price and list position across the four evidence-requiring conditions. This
holds presentation constant for the within-block condition comparison. Across
the 15 evaluation blocks, that source occupies 15 distinct price-position
cells out of the 16 possible, once per condition. Analyses therefore block on
scenario rather than treating price or position as independently sampled on
all 75 rows.

The disclosed diagnostic policy utility is:

```text
supported correct answer       +100
supported INSUFFICIENT         +100
wrong or unsupported answer    -200
unjustified abstention           -50
opened evidence                -sum(source credits)
```

Wrong-answer loss dominates the complete acquisition budget. Harbor's primary
reward remains strict binary all-pass. Utility and acquisition cost are
diagnostics and are never substituted for task success.

The terminal submission is typed JSON:

```json
{
  "decision": "answer",
  "answer": {"entity_id": "..."},
  "confidence": 0.84
}
```

Semantically unordered fields are canonicalized. Confidence is recorded but is
not a correctness gate.

## Verifier Contract

The deterministic verifier records independent axes:

- `semantic_outcome`
- `proof_outcome`
- `format_outcome`
- `verifier_integrity`
- `harness_completion`

Proof is derived from the protected evidence-open ledger, never self-reported
citations. Accepted proof is represented as OR-of-AND claim/source sets so
alternative valid proof paths pass. Strict Harbor reward is:

```text
semantic pass
AND proof pass
AND format pass
AND verifier integrity pass
```

The domain headline is semantic decision plus sufficient proof plus verifier
integrity. Strict formatting and harness completion remain adjacent operational
metrics rather than being blended into context judgment.

Efficiency diagnostics include:

```text
signed_cost_delta = observed_cost - hindsight_minimum_cost
successful_excess_cost = signed_cost_delta on semantic + proof success only
```

Evidence credits, payload bytes/token proxy, model tokens, provider cost, and
latency remain separate. No realized hindsight measure is described as
Bayes-optimal regret.

## Security And Contamination Boundary

- Generate a cryptographically random release secret outside Git.
- Derive per-task seeds and opaque IDs using HMAC.
- Commit only the generator version and SHA-256 release-secret commitment.
- Commit a dataset commitment derived from all 75 private instance
  commitments and a package-set commitment derived from all complete Harbor
  task digests before inference.
- Commit public development tasks; ignore `eval-private/` and the secret.
- Put only initial context, catalog metadata, and the evidence CLI in the main
  agent image.
- Put the frozen corpus and append-only acquisition ledger in the protected
  evidence sidecar.
- Put hidden truth and accepted proof graphs in the separate no-network
  verifier.
- Preserve authenticated sidecar snapshot collection after the main service
  stops.

Harbor 0.20 Modal Compose currently requires a public network baseline for the
agent service. Every manifest therefore records `agent_egress=public` and
`contract_visibility=private`. The held-out dataset stays private during the
official run. If its contracts are later released, v0.3.0 becomes a one-shot
frozen set; secure future reruns require fresh hidden instances or enforceable
closed egress.

## Manifest v2

The historical v1 manifest remains immutable. A derived v2 record links to it
and to the raw Harbor job. Every trial exposes:

```text
execution_status: completed | deadline | infrastructure_error | cancelled | not_started
failure_stage: provider_wait | terminal_io | agent_execution | sandbox | collection | verifier | null
answer_observed: bool
verifier_status: pass | fail | error | not_run
semantic_outcome: pass | fail | not_evaluated
proof_outcome: pass | fail | not_evaluated
format_outcome: pass | fail | not_evaluated
harness_completion: confirmed | unconfirmed | not_evaluated
benchmark_valid: bool
strict_task_success: 0 | 1 | null
domain_success: 0 | 1 | null
sampling_seed: int | string | null
instance_commitment: sha256 | null
```

The v0.2.1 migration must reproduce 69 benchmark-valid trials, 67 strict
all-pass trials, and 68 semantic-plus-proof trials. Its five hidden agent
deadlines remain `deadline`, outside domain accuracy, while their recovered
verifier snapshots remain diagnostic. The verifier-download failure remains an
infrastructure error.

## Fixed Official Configuration

- Model: `openrouter/z-ai/glm-5.2`
- Harness: Terminus 2 `2.0.0`
- Skills: none
- Sandbox: Modal VM runtime
- Temperature: `0` only after provider canary acceptance
- Reasoning effort: provider default
- Attempts: one per task
- Agent timeout: 300 seconds
- Concurrency: four trials and four agents
- Harbor retries: zero

After an exact provider preflight, freeze one OpenRouter endpoint with
`provider.order`, `allow_fallbacks=false`, and `require_parameters=true` when
the Terminus/OpenRouter path confirms those controls. If exact routing cannot
be verified, report that limitation and do not claim provider-level
reproducibility.

Official job name:

```text
context-appetite-v0.3.0-glm52-t2-eval-001
```

Scratch jobs:

```text
context-appetite-v0.3.0-modal-t2-preflight-001
context-appetite-v0.3.0-oracle-smoke-001
context-appetite-v0.3.0-glm52-t2-canary-001
```

No valid model failure is selectively retried. Resume only not-started cells
from the exact run lock after an orchestrator interruption. Two repeated
same-origin infrastructure failures trigger an abort and a transparently
versioned superseding run.

## Release Gates

1. Manifest-v2 schema, migration tests, and 69/67/68 reconciliation.
2. Generator determinism, block-split isolation, secret commitment, schema,
   balance, and no-answer-leak tests.
3. Verifier fixtures for valid, wrong, unsupported memorized, alternative
   proof, malformed, canonicalized unordered, forged, stale, and missing state.
4. Deterministic acquisition policies over every task: answer immediately,
   abstain immediately, first-listed, cheapest-first,
   highest-reliability-first, random-one, open-all, and proof-aware Oracle.
   Nonterminal baselines use an oracle terminal decision and therefore measure
   proof coverage and acquisition cost, not model accuracy.
5. Harbor task validation and `--print-config` inspection for every bundle.
6. One Terminus install-only Modal preflight.
7. Oracle over all 75 private tasks, with strict reward `1` for every task.
8. Five-cell paid canary, one task per condition, followed by full trace and
   artifact inspection.
9. Official 75-trial run, normalization, non-pass audit, and stratified trace
   review before release.

Oracle, preflight, and canary jobs remain scratch results and never pad the
official 75-trial model denominator.

## Reporting

The release report and website show planned, benchmark-valid, deadline, and
infrastructure counts; domain success; strict all-pass; matched outcomes by
condition; answer-now zero-open rate; supported and unsupported abstention;
evidence count and cost conditional on success; successful excess cost;
payload bytes/token proxy; model tokens, latency, provider dollars; harness
completion; and the full pinned configuration.

Analysis is paired by the 15 matched blocks or bootstrapped over blocks. The 75
rows are not treated as independent observations. v0.3.0 publishes no blended
smartness score and no cross-model ranking.

## Checkpoints

1. Audit provenance: `99d4dd1` (complete and pushed).
2. This preregistration plan.
3. Manifest v2 and immutable v0.2.1 derivation.
4. Generator, public development set, and policy baselines.
5. Runtime, verifier, release lock, and 75-task Oracle.
6. Paid canary manifest and trace audit.
7. Official model manifest, report, and release review.

The public development dataset is published only after final review. The
held-out evaluation dataset remains private unless its one-shot status is
explicitly accepted.

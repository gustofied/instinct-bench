# Instinct Bench: Context Appetite v0.3.1

## Purpose

Context Appetite v0.3.1 measures supported evidence routing and stopping under
an explicit information, provenance, payoff, and acquisition-cost contract. It
tests direct answers, one-source and complementary evidence, provenance
conflicts, and supported abstention.

The current prompts disclose whether the initial record identifies the answer,
and the free catalog exposes source metadata. This release therefore does not
claim to measure uncued uncertainty detection, Bayes-optimal acquisition, or a
general intelligence trait.

Version 0.3.1 is a contract-alignment release. It preserves the v0.3.0 raw job
and frozen 71/75 verifier result, while fixing the proof rule that produced
three post-hoc false negatives. The amended v0.3.0 material audit is 74/75.

## Taxonomy

- Suite: Instinct Bench
- Domain and Harbor dataset: `context-appetite`
- Conditions: `answer-now`, `single-source`, `complementary-evidence`,
  `insufficient-evidence`, and `reliability-conflict`

Conditions are experimental strata, not another task-family layer. One Harbor
task is one generated decision problem.

## Changes From v0.3.0

1. Plain `INSUFFICIENT` now requires the event-specific ambiguity record and
   independent completeness audit. Candidate records are optional unless a
   future terminal schema explicitly asks the agent to identify candidates.
2. The instruction uses `PROBABILITY` rather than supplying `0.84`, preserving
   confidence as a usable diagnostic.
3. Private output roots and task directories are mode `0700`; data files are
   `0600`, while each Oracle `solution/` path is `0755` for Harbor's non-root
   execution contract. Package commitments include file and directory modes.
4. Public development instances use a new versioned seed and package digests.
5. Manifest normalizer 2.1 validates release metadata against the requested
   implementation version. The exact 2.0 source used by v0.3.0 is archived.
6. The work request describes the material support rule and correctly explains
   that sources are opened one at a time.
7. An independent semantic audit reconstructs support from source contents and
   rejects disagreement between material minimal support sets and verifier
   proof paths.

The runtime architecture remains unchanged: a non-root agent, protected
evidence sidecar, authenticated final snapshot, collected ledger artifact, and
separate deterministic no-network verifier.

## Release Population

The committed development dataset contains six matched blocks by five
conditions, or 30 tasks. The benchmark release contains 15 disjoint matched
blocks by five conditions, or 75 tasks. Those 75 tasks remain unpublished only
through the first preregistered public-egress run, then become the single public
benchmark. This is a one-shot contamination boundary, not a permanent hidden
leaderboard split.

The 21 blueprints are surface scenarios over five shared generated evidence
structures. They improve domain and vocabulary coverage, but they are not 21
unrelated Terminal-Bench-style task implementations. The release claim is
limited to the five controlled acquisition conditions.

Private task IDs and dataset order are independently keyed by the release
secret. Price and list position are matched within a block and counterbalanced
across blocks. Hidden truth, source contents, and proof paths do not enter the
agent image.

## Release Gates

Run these gates in order:

1. Full unit suite, Ruff, JSON parsing, generated-file drift, and
   `git diff --check`.
2. Independent material-semantic audit and deterministic policies over every
   generated task. No fixed one-source policy may dominate.
3. Harbor 0.20 `--print-config` for the complete public dataset.
4. Oracle over all 30 public tasks on the intended sandbox.
5. Oracle over all 75 pre-public benchmark tasks and all protected runtime
   checks.
6. One paid five-condition canary with complete trajectory review.
7. Only then launch a predeclared proper-agent matrix.

Oracle, preflight, and canary jobs never enter agent accuracy.

## Proper-Agent Comparisons

Treat the evaluated configuration as the complete agent:

```text
model + harness + prompt + skills + sandbox + provider route
```

Change one major variable per comparison. A model comparison fixes Terminus 2,
prompt, skills, sandbox, and provider policy. A harness comparison fixes the
model and provider policy. Every configuration receives all 75 tasks with
pass@1, no selective retries, and the same timeout and concurrency contract.

Report a success-acquisition frontier: binary task success beside evidence
credits, source count, and payload, plus semantic, proof, format, integrity,
harness, infrastructure, token, latency, and provider-cost diagnostics. An
open-all policy can earn 75/75 binary success, so task success alone does not
measure restraint. Use matched-block summaries. Do not treat 75 rows as
independent, blend cost into task success, or infer a model ranking from one
configuration.

## Publication

The 30-task set is public development material and cannot enter a clean
public-egress accuracy denominator. The 75-task benchmark remains unpublished
for one locked baseline, then is published and all subsequent runs are labeled
public-set protocol results.

Modal Compose gives the agent raw public egress. Once task packages are public,
that permits solution retrieval and is not a controlled internet action. A
reusable public comparison must use a network boundary that blocks benchmark
artifacts and external model APIs, or a future logged and priced internet proxy
with the same exclusions.

Harbor publication is private by default:

```bash
uvx --from 'harbor==0.20.0' harbor auth status
uvx --from 'harbor==0.20.0' harbor publish \
  evals/context-appetite/dev \
  --tag v0.3.1
```

Add `--public` only after confirming ownership of the `instinct-bench`
namespace and reviewing the uploaded task and dataset visibility. Registry
upload remains a separate action that Adam will request explicitly.

The completed truth-free release evidence is recorded in
[`results/reports/context-appetite-v0.3.1`](../results/reports/context-appetite-v0.3.1/README.md).

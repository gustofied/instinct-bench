# Instinct Bench: Context Appetite v0.3.1

## Purpose

Context Appetite measures whether an agent answers from sufficient initial
context, acquires material evidence when needed, combines evidence, resolves
provenance conflicts, and abstains when a closed corpus cannot support a unique
answer.

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

The runtime architecture remains unchanged: a non-root agent, protected
evidence sidecar, authenticated final snapshot, collected ledger artifact, and
separate deterministic no-network verifier.

## Release Population

The committed development dataset contains six matched blocks by five
conditions, or 30 tasks. A formal comparison uses a fresh private release with
15 disjoint matched blocks by five conditions, or 75 tasks. The existing 21
scenario blueprints already provide varied operational settings; adding more
rows is not the current bottleneck.

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
2. Deterministic policies over every generated task. No fixed one-source
   policy may dominate.
3. Harbor 0.20 `--print-config` for the complete public dataset.
4. Oracle over all 30 public tasks on the intended sandbox.
5. For a private evaluation, Oracle over all 75 private tasks and all protected
   runtime checks.
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

Report binary task success; semantic, proof, format, integrity, and harness
axes; infrastructure reliability; evidence use; model tokens, latency, and
provider cost; requested versus confirmed routing; and the egress/contract
boundary. Use matched-block summaries. Do not treat 75 rows as independent,
blend cost into task success, or infer a model ranking from one configuration.

## Publication

The public development dataset is suitable for Harbor registry testing after
the local release gates pass. It is a development set, not a hidden
leaderboard. Official results require a fresh private commitment and run lock.

Harbor publication is private by default:

```bash
uvx --from 'harbor==0.20.0' harbor auth status
uvx --from 'harbor==0.20.0' harbor publish \
  evals/context-appetite/dev \
  --tag v0.3.1
```

Add `--public` only after confirming ownership of the `instinct-bench`
namespace and reviewing the uploaded task and dataset visibility.

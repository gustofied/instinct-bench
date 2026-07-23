# Run Manifests

Raw Harbor jobs remain the audit record. A run manifest is the small,
versioned index consumed by reports and the website.

- `jobs-scratch/`: install checks, Oracle smoke runs, canaries, and abandoned
  engineering work.
- `jobs/`: predeclared model pilots and evaluations, including failures.
- `results/manifests/`: normalized run intent, lifecycle, configuration,
  counts, costs, and per-trial classification.
- `results/reports/`: human-readable analyses derived from a locked manifest
  and its raw Harbor job.

Create the intent record before launch and finalize it even when orchestration
aborts. In v2, `execution_status` records completed, deadline, infrastructure,
cancelled, and not-started cells. `verifier_status` and `verifier_integrity`
decide whether a completed cell is benchmark-valid. Semantic decision, proof,
format, and harness completion remain independent outcomes. Only completed
trials with a passing integrity check enter benchmark accuracy; every other
cell remains visible in the planned-run and reliability counts.

Use `null` when model, harness, or sandbox cost is unavailable. Never estimate
or invent the cost mix. Oracle rows are QA evidence and must not appear as
model performance.

`schema-v2.json` is the current contract. It separates execution status,
verifier validity, semantic outcome, proof, format, and harness completion.
`schema-v1.json` and the existing v1 manifests remain immutable historical
records. `template.json` is a v1 starting record, not a completed result.

Normalize a completed Harbor 0.20 job with
`tools/normalize_harbor_job_v2.py`. Pass the exact launch command and Git commit;
the tool records a sanitized command, allowlisted public metrics, task digests,
provider configuration, trace paths, independent classifications, model-call
latency, token telemetry, and costs without dropping failed cells. Pass
`--derived-from` when correcting a historical manifest; the tool records its
path and digest instead of rewriting it. v0.3 task runs also require complete
release metadata with a non-secret seed commitment, dataset and package-set
commitments, matched-condition metadata, and per-instance commitments.
Task provenance uses Harbor 0.20's locked `TrialLock.task.digest`; the older
result-side `task_checksum` field is deprecated and is not treated as the
durable package identity.

The v0.2.1 model pilot now has both its original
[`v1 record`](context-appetite-v0.2.1-model-pilot-3x-001.json) and its
[`v2 reconciliation`](context-appetite-v0.2.1-model-pilot-3x-001.v2.json).
The latter reports 69 benchmark-valid trials, 67 strict passes, 68 domain
passes, five deadlines, and one verifier infrastructure error.

The first completed model-pilot analysis is
[`context-appetite-v0.2.1-model-pilot-3x-001`](../reports/context-appetite-v0.2.1-model-pilot-3x-001.md).
Its fuller post-run audit and next-experiment design are indexed in
[`our-first-harbor`](../reports/our-first-harbor/README.md).

`jobs-archive/` is an ignored local provenance store for superseded smoke,
canary, repair, and abandoned setup jobs. It is kept outside `jobs/` and
`jobs-scratch/` so Harbor View remains an active-work surface. Archiving a raw
job never changes its result; reports should record the relocation when a
historical manifest still contains the original path.

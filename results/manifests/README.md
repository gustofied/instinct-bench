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
aborts. `execution_state` answers whether a valid trial ran;
`task_outcome` answers whether that valid trial passed. Infrastructure errors,
cancellations, and not-started trials never enter task accuracy, but remain in
the planned-run denominator and visible reliability counts. Successful
install-only preflights are `valid` with `task_outcome=not-evaluated`; they are
tracked by `valid_not_evaluated` and never enter benchmark accuracy.

Use `null` when model, harness, or sandbox cost is unavailable. Never estimate
or invent the cost mix. Oracle rows are QA evidence and must not appear as
model performance.

`schema-v1.json` is the contract. `template.json` is a starting record, not a
completed result.

Normalize a completed Harbor 0.20 job with
`tools/normalize_harbor_job.py`. Pass the exact launch command and Git commit;
the tool preserves raw trial names, task digests, provider configuration,
trace paths, classifications, token telemetry, and costs without dropping
failed cells.

The first completed model-pilot analysis is
[`context-appetite-v0.2.1-model-pilot-3x-001`](../reports/context-appetite-v0.2.1-model-pilot-3x-001.md).
Its fuller post-run audit and next-experiment design are indexed in
[`our-first-harbor`](../reports/our-first-harbor/README.md).

`jobs-archive/` is an ignored local provenance store for superseded smoke,
canary, repair, and abandoned setup jobs. It is kept outside `jobs/` and
`jobs-scratch/` so Harbor View remains an active-work surface. Archiving a raw
job never changes its result; reports should record the relocation when a
historical manifest still contains the original path.

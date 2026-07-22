# Run Manifests

Raw Harbor jobs remain the audit record. A run manifest is the small,
versioned index consumed by reports and the website.

- `jobs-scratch/`: install checks, Oracle smoke runs, canaries, and abandoned
  engineering work.
- `jobs/`: predeclared model pilots and evaluations, including failures.
- `results/manifests/`: normalized run intent, lifecycle, configuration,
  counts, costs, and per-trial classification.

Create the intent record before launch and finalize it even when orchestration
aborts. `execution_state` answers whether a valid trial ran;
`task_outcome` answers whether that valid trial passed. Infrastructure errors,
cancellations, and not-started trials never enter task accuracy, but remain in
the planned-run denominator and visible reliability counts.

Use `null` when model, harness, or sandbox cost is unavailable. Never estimate
or invent the cost mix. Oracle rows are QA evidence and must not appear as
model performance.

`schema-v1.json` is the contract. `template.json` is a starting record, not a
completed result.

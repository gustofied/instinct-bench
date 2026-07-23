# Job Archive

Archive date: 2026-07-23.

This is the historical v0.2.1 cleanup record. The later canonical local review
layout, including v0.3.0 and v0.3.1, is documented in
[`docs/local-evidence-review.md`](../../../docs/local-evidence-review.md).

Harbor View scans the directory it is given and displays historical setup
failures beside valid model runs. To create a clean active dashboard without
deleting provenance, superseded and scratch jobs were moved into the ignored
`jobs-archive/` tree.

## Active Job

The complete 75-trial pilot remains at:

```text
jobs/context-appetite-v0.2.1-model-pilot-3x-001
```

It is the only job intended for the active `harbor view jobs` surface.

## Archived From `jobs/`

- `2026-07-22__15-15-36`
- `2026-07-22__15-17-02`
- `context-appetite-five-oracle-v02`
- `context-appetite-five-oracle-v02b`
- `first-harbor-open-weight-five`
- `harbor-020-modal-oracle`
- `harbor-020-open-weight-five`
- `harbor-020-terminus-prerequisites-oracle`
- `our-first-harbor-repair-oracle`
- `our-first-harbor-repair-oracle-final`
- `our-first-harbor-repair-oracle-versioned`
- `terminus-prerequisites-oracle`

Their local destination is `jobs-archive/jobs/`.

## Archived From `jobs-scratch/`

- `context-appetite-v0.2.1-modal-vm-t2-preflight-001`
- `context-appetite-v0.2.1-openrouter-canary-001`
- `context-appetite-v0.2.1-openrouter-canary-vm-001`
- `context-appetite-v0.2.1-openrouter-canary-vm-002`
- `context-appetite-v0.2.1-oracle-smoke-001`
- `context-appetite-v0.2.1-oracle-smoke-vm-001`

Their local destination is `jobs-archive/jobs-scratch/`.

The committed historical manifests retain the paths recorded when those jobs
ran. This relocation changes only local storage and Harbor View hygiene; it
does not alter any result, score, or report. The archive is intentionally
ignored by Git because raw jobs contain bulky execution evidence.

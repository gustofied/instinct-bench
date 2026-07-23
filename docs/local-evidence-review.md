# Local Evidence Review

Status: canonical local layout verified on 2026-07-23.

Raw Harbor jobs are the audit record behind the normalized manifests and
reports. They contain trajectories, verifier output, protected artifacts, and
in some cases hidden expected answers or proof paths. They therefore remain
ignored by Git and must never be committed merely to make local review easier.

## Canonical Layout

Run all paths from the Instinct Bench repository root.

| Class | Local path | Contents |
| --- | --- | --- |
| Official | `jobs/` | Three predeclared model evaluations, including failures |
| Scratch | `jobs-scratch/` | 14 preflights, Oracle runs, canaries, and repair checks |
| Archive | `jobs-archive/` | 12 historical jobs and six historical scratch jobs |
| Exploratory | `explorative/evals/jobs/` | Current learning runs; never an official denominator |
| Private tasks | `evals/context-appetite/eval-private*` | Three 75-task release snapshots |
| Private review | `local-review/private/` | 15 private normalized manifests |
| Checksums | `local-review/checksums/` | Full ignored mode-aware evidence indexes |
| Viewer mirror | `local-review/viewer-jobs/` | Verified local copies of 37 reviewable jobs |

The viewer mirror prefixes every directory with `official--`, `scratch--`,
`archive--`, `archive-scratch--`, or `exploratory--`. These labels are storage
classes, not benchmark outcomes. Only a run's committed normalized manifest
defines its denominator and publication eligibility.

## Official Jobs

| Run | Source commit | Results / ATIF / verifier / ledger | Mode-aware tree SHA-256 |
| --- | --- | --- | --- |
| `context-appetite-v0.2.1-model-pilot-3x-001` | `77ef2de3667b22794db0b8d089256165dd9f11e1` | 75 / 75 / 74 / 75 | `f607d609dd05825de5ee175078d6ae8b9012efc7296b59df1f9bbf335bc022ae` |
| `context-appetite-v0.3.0-glm52-t2-eval-001` | `a6e35fe` | 75 / 75 / 75 / 75 | `8687ec27463341da68173c9d86bab95a39641241dc252cc131e3f68e12e4e8d4` |
| `context-appetite-v0.3.1-glm52-t2-eval-001` | `f1895a8` | 75 / 75 / 75 / 75 | `9f5318a317fe531e46e51b2070acf6e067398cf0f54abbd4f343cd36049e61e7` |

The missing v0.2.1 verifier output is the recorded verifier-download
infrastructure failure, not a lost file.

## Root Digests

These digests include relative paths, entry types, permission modes, file
sizes, file contents, and symlink targets. The full entry indexes are private.

| Root | Files | Bytes | Mode-aware tree SHA-256 |
| --- | ---: | ---: | --- |
| `jobs/` | 2,939 | 10,193,132 | `20788c1acaa51c2a1fd5db53f8fc41423796edbd7141ce973cf06b7b0b36650b` |
| `jobs-scratch/` | 4,652 | 8,122,175 | `31ad962f8c7c889634108cd6e9e37746362aa7521b2247986cbf5b9ae9aaec02` |
| `jobs-archive/` | 517 | 1,083,859 | `24e65fac6a6df0dcd6a12ec78a181d6b8e0f76f6c2861e78ee83841e689dede3` |
| v0.3.0 private tasks | 1,354 | 3,396,769 | `9c0db8034ba90a18a7b9283809ef80d3cd0842166065f2240bf76e1a0c21f2c0` |
| v0.3.1 private tasks | 1,354 | 3,420,171 | `cd42ce087f97bb287038fa15f77fdb54b33c39cc8b3d0db04958a1fa1c54f758` |
| v0.3.1 pre-proof-fix tasks | 1,354 | 3,420,201 | `a464efafa359b933cb10ef84e20b340c60125876d63bf36d8afd953f0c50ee51` |
| 37-job viewer mirror | 8,324 | 20,408,096 | `985c93deb179ef07f05647b43c46cdae79760e40258b15e0656eb0ce1ebb6178` |

The six canonical source roots match their retained originals byte-for-byte and
mode-for-mode. Every one of the 823 raw evidence path entries in the four
tracked mature manifests resolves from this canonical layout. Original
`trial_uri` values remain unchanged as as-run provenance.

## Open The Viewer

The persistent local viewer uses:

```bash
harbor view local-review/viewer-jobs --jobs --port 8081
```

Open [http://127.0.0.1:8081](http://127.0.0.1:8081). The current process runs
in tmux session `instinct-bench-review`.

Harbor lists symlinked job directories but rejects their evidence endpoints
when the resolved path leaves the viewer root. `local-review/review-jobs/`
retains that lightweight inventory; the live viewer uses the verified in-root
mirror so trajectories, verifier output, file trees, recordings, and artifacts
all remain accessible.

## Recheck

`tools/index_local_evidence.py` builds a private mode-aware index:

```bash
python3 tools/index_local_evidence.py --help
```

Before deleting any retained worktree or cache, regenerate the source and
canonical indexes, compare all root digests, validate both release
commitments, and open representative official and failed exploratory trials in
Harbor View. Do not rewrite raw `trial_uri` fields during relocation.

The v0.3.0 and v0.3.1 release secrets live outside the repository at mode
`0600` under `~/.config/instinct-bench/`. No secret, private manifest, private
task package, raw job, or viewer mirror is tracked.

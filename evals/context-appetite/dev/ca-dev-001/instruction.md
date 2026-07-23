# Decision Record

Which deployment controlled recovery event evt-f625cs7n?

Initial context: The signed decision register for evt-f625cs7n establishes dep-bwsqcb9d as the controlling deployment.

Initial-context provenance:
- authority class: `signed-decision-register`
- declared reliability: `0.995`
- lineage group: `initial-9d2k59`

The evidence catalog is optional. Inspect it with `evidence list`, open one
source with `evidence open SOURCE_ID`, and inspect spend with `evidence status`.

Submit exactly one final decision:

```text
evidence submit answer ENTITY_ID --confidence 0.84
evidence submit insufficient --confidence 0.84
```

Your submission is final. Evidence cannot be opened afterward.

Payoff used as a diagnostic:

```text
supported correct answer       +100
supported INSUFFICIENT         +100
wrong or unsupported answer    -200
unjustified abstention           -50
opened evidence                -sum(source credits)
```

Task success comes first. Evidence use, payload, model tokens, and policy
utility are reported separately.

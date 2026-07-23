# Decision Record

Which allocation endpoint controlled reservation evt-cpmm6bpz?

Initial context: The signed intake record establishes evt-cpmm6bpz and the decision question, but does not identify the controlling allocation endpoint.

Initial-context provenance:
- authority class: `signed-intake-record`
- declared reliability: `0.990`
- lineage group: `initial-af7yu8`

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

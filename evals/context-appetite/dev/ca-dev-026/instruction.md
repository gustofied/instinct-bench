# Decision Record

Which power circuit controlled transfer event evt-djsbjgwh?

Initial context: The signed decision register for evt-djsbjgwh establishes circuit-7ru85xvt as the controlling power circuit.

Initial-context provenance:
- authority class: `signed-decision-register`
- declared reliability: `0.995`
- lineage group: `initial-9zzeac`

The evidence catalog is optional. Inspect it with `evidence list`, open one
source with `evidence open SOURCE_ID`, and inspect spend with `evidence status`.

Submit exactly one final decision:

```text
evidence submit answer ENTITY_ID --confidence PROBABILITY
evidence submit insufficient --confidence PROBABILITY
```

Replace `PROBABILITY` with your confidence from `0` to `1`.
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

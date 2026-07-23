# Decision Record

Which tenant credential controlled access event evt-884vrmqf?

Initial context: The signed intake record establishes evt-884vrmqf and the decision question, but does not identify the controlling tenant credential.

Initial-context provenance:
- authority class: `signed-intake-record`
- declared reliability: `0.990`
- lineage group: `initial-hb3scm`

The evidence catalog is optional. Inspect it with `evidence list`, open sources
one at a time with `evidence open SOURCE_ID`, and inspect spend with
`evidence status`.

A supported answer requires the initial context or opened evidence to establish
the event-to-entity link. A supported `INSUFFICIENT` decision requires opened
evidence establishing event-specific ambiguity and that the corpus is complete
for the relevant window.

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

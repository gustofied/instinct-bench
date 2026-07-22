# Invoice Recovery

Identify the deployment that was rolled back immediately before invoice
generation recovered at 09:14 UTC.

Initial context: approved change ticket CHG-910 records rollback of
`billing-api-2026.07.22.7` at 09:12 UTC and restoration of invoice generation
at 09:14 UTC.

You may inspect the record catalog and evidence-credit prices with
`evidence list`. Open a record with `evidence open SOURCE_ID`, and submit one
final answer with `evidence answer DEPLOYMENT_ID`.

Task success comes first. Evidence use and cost are reported separately.

Submit the exact deployment ID, or submit `INSUFFICIENT` if the available
information cannot establish one. Your submission is final, and evidence
cannot be opened afterward.

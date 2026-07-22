# Deployment Outage

Identify the deployment that was rolled back to resolve the checkout outage
from 14:32 to 14:47 UTC.

Initial context: checkout requests began returning HTTP 500 errors at 14:32
UTC, shortly after several systems changed.

You may inspect the record catalog and evidence-credit prices with
`evidence list`. Open a record with `evidence open SOURCE_ID`, and submit one
final answer with `evidence answer DEPLOYMENT_ID`.

Task success comes first. Evidence use and cost are reported separately.

Submit the exact deployment ID, or submit `INSUFFICIENT` if the available
evidence cannot establish one. Your submission is final, and evidence cannot
be opened afterward.

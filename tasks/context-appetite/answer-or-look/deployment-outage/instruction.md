# Deployment Outage

Identify the deployment that caused the checkout outage from 14:32 to 14:47
UTC.

Initial context: checkout requests began returning HTTP 500 errors at 14:32
UTC, shortly after several systems changed.

Use `evidence list` to inspect the available records and their evidence-credit
prices. Open records with `evidence open SOURCE_ID`, and submit one final answer
with `evidence answer DEPLOYMENT_ID`.

Task success comes first. Among successful answers, lower evidence cost is
better.

Submit the exact deployment ID, or submit `INSUFFICIENT` if the available
evidence cannot establish one. Your submission is final, and evidence cannot
be opened afterward.

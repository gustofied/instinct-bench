# Capacity Feed

Identify the upstream capacity feed that produced quote `Q-884`'s incorrect
H100 availability.

Initial context: quote `Q-884` reported 512 available H100s, while
reconciliation established that only 128 were available.

You may inspect the record catalog and evidence-credit prices with
`evidence list`. Open a record with `evidence open SOURCE_ID`, and submit one
final answer with `evidence answer FEED_ID`.

Task success comes first. Evidence use and cost are reported separately.

Submit the exact feed ID, or submit `INSUFFICIENT` if the available evidence
cannot establish one. Your submission is final, and evidence cannot be opened
afterward.

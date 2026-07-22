# Search Latency

Identify both candidate deployments for the search latency incident from 11:10
to 11:26 UTC and determine whether the evidence uniquely attributes the
incident to either one.

Initial context: search p95 latency rose at 11:10 UTC after two components
changed within two minutes of each other.

You may inspect the record catalog and evidence-credit prices with
`evidence list`. Open a record with `evidence open SOURCE_ID`, and submit one
final answer with `evidence answer ANSWER`.

Task success comes first. Evidence use and cost are reported separately.

If one deployment is uniquely supported, submit its exact ID. Otherwise submit
`INSUFFICIENT:DEPLOYMENT_ID_1,DEPLOYMENT_ID_2`, listing both candidates in
deployment-time order. Your submission is final, and evidence cannot be opened
afterward.

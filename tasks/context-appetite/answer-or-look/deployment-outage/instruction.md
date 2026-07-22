# Deployment Outage

Identify the deployment that caused the checkout outage from 14:32 to 14:47
UTC.

Initial context: checkout requests began returning HTTP 500 errors at 14:32
UTC. Several services had deployments near that time, but the deployment ID
responsible for the outage is not present in this initial context.

You may inspect any of these evidence sources:

| Source | Cost | Contents |
| --- | ---: | --- |
| `incident-summary` | 300 tokens | High-level incident timeline and impact |
| `deployment-log` | 2,000 tokens | Deployment and rollback records with change IDs |
| `team-conversation` | 8,000 tokens | Messages from the incident response channel |
| `metrics-export` | 12,000 tokens | Service-level error and latency observations |

Use the `evidence` command to interact with the task:

```text
evidence list
evidence open SOURCE_ID
evidence status
evidence answer DEPLOYMENT_ID
```

Submit the exact deployment ID, or submit `INSUFFICIENT` if the available
evidence cannot establish one. Your submission is final, and evidence cannot
be opened afterward.

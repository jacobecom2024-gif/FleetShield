# Threat model

## Assets

- Financial or other externally visible side effects
- Approval evidence
- Tool credentials
- Policy definitions and activation state
- Replay evidence and audit history

## Adversaries and failures

| Threat | Example | Control |
|---|---|---|
| At-least-once delivery | Pub/Sub redelivers an aid case | Business idempotency invariant |
| Lost acknowledgement | Commit succeeds but response times out | Pre-call reference monitor plus durable ledger |
| Prompt injection | Tool output asks the agent to ignore policy | Model output has no policy authority |
| Stale evidence | Old approval reused | Timestamp invariant checked at execution |
| Excessive authority | Agent proposes and activates its own rule | Human approval is a separate state transition |
| Scope error | Grant policy applied to credential rotation | Explicit side-effect class and shadow evaluation |
| Blanket blocking | “Fix” rejects all tool calls | Benign control case must still pass |
| Replay tampering | Counterexample edited after failure | Canonical payload hash in production evidence |

## Non-goals for the MVP

- Proving arbitrary policies formally
- Running destructive experiments against third-party systems
- Reversing completed external transactions
- Replacing security review or domain experts
- Automatically activating fleet-wide controls

## Safe failure policy

When state, scope, or approval cannot be verified, FleetShield blocks only the
affected high-impact tool call and preserves the trace for human review. Read-only
observability remains available.

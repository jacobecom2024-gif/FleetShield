# Four-minute demo script

## 0:00–0:25 — Verifiable runtime

Open the public `run.app` URL and point to the **Live runtime evidence** strip.
Show the Cloud Run revision, `google-adk:gemini:multi-agent`, the three specialist
agents, Gemini model, state backend, and the JSON evidence link. Briefly open
`/api/evidence`; this proves the backend is not a local mock or prerecorded UI.

## 0:25–0:45 — The contract

“Small community-relief teams increasingly use agents for emergency grants,
medicine vouchers, and shelter payments, but they rarely have an SRE team. This
agent promises to release each approved grant exactly once. The sandbox ledger is
empty; no real money or external account is connected.”

## 0:45–1:20 — Capture the counterexample

Choose **Timeout after commit** and run the vulnerable agent.

Point to:

- first committed USD 249 payment;
- injected lost acknowledgement;
- retry with a different action id;
- second committed USD 249 payment;
- red result: expected one, observed two.

## 1:20–2:00 — Compile the invariant

Click **Discover invariants**.

Explain that Gemini delegates the failure to three ADK specialists: one reconstructs
the failure, one limits fleet scope, and one mines invariant candidates. Their output
is untrusted. The deterministic compiler creates an inspectable exactly-once
expression over tool and aid case.

Show all three candidates in shadow mode and their three-agent scope.

After discovery, return to the runtime strip or JSON evidence and show that
`google_adk_executed` is now true and the policy source begins with
`google-adk:gemini:multi-agent:`.

## 2:00–2:20 — Approval boundary

Click **Approve deterministic control**.

Emphasize that neither the failing agent nor Gemini can activate a rule. The
approval transition is explicit, named, durable, and auditable.

## 2:20–3:00 — Exact replay

Click **Replay exact failure**.

The first payment commits. The same acknowledgement loss occurs. The same retry
is attempted. This time the reference monitor blocks it before the ledger.

Point to green result: expected one, observed one, one blocked action.

## 3:00–3:25 — Fleet propagation

Show Relief Grant, Medicine Voucher, and Shelter Payment agents. The rule is not
copied because their names look similar; all three explicitly declare the
`community_relief_funds` side-effect class and must pass shadow tests before
activation.

## 3:25–3:45 — Independent verifier

Run:

```bash
python scripts/verify_demo.py https://YOUR-SERVICE.run.app --require-cloud
```

Keep the `PASS` lines and runtime JSON visible. If a Pub/Sub event has been sent,
show `pubsub_events_observed: true`; do not claim it otherwise.

## 3:45–4:00 — Close

“Agent testing normally reports a problem. FleetShield turns one witnessed
failure into a deterministic, tested, approval-gated control for the fleet.
One failure; fleet-wide immunity.”

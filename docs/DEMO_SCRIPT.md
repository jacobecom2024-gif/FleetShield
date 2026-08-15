# Four-minute demo script

## 0:00–0:25 — The contract

“This invoice agent promises to pay each approved invoice exactly once. The UI
shows an empty sandbox ledger. No real money or external account is connected.”

## 0:25–1:05 — Capture the counterexample

Choose **Timeout after commit** and run the vulnerable agent.

Point to:

- first committed USD 249 payment;
- injected lost acknowledgement;
- retry with a different action id;
- second committed USD 249 payment;
- red result: expected one, observed two.

## 1:05–1:50 — Compile the invariant

Click **Discover invariants**.

Explain that Gemini interprets the natural-language contract and failing trace,
but can only return allowlisted typed candidates. The deterministic compiler
creates an inspectable exactly-once expression over tool and business subject.

Show all three candidates in shadow mode and their three-agent scope.

## 1:50–2:15 — Approval boundary

Click **Approve deterministic control**.

Emphasize that neither the failing agent nor Gemini can activate a rule. The
approval transition is explicit, named, durable, and auditable.

## 2:15–3:05 — Exact replay

Click **Replay exact failure**.

The first payment commits. The same acknowledgement loss occurs. The same retry
is attempted. This time the reference monitor blocks it before the ledger.

Point to green result: expected one, observed one, one blocked action.

## 3:05–3:35 — Fleet propagation

Show Invoice, Refund, and Payout agents. The rule is not copied because their
names look similar; all three explicitly declare the `financial` side-effect
class and must pass shadow tests before activation.

## 3:35–4:00 — Close

“Agent testing normally reports a problem. FleetShield turns one witnessed
failure into a deterministic, tested, approval-gated control for the fleet.
One failure; fleet-wide immunity.”


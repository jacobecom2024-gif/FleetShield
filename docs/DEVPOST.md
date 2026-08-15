# Devpost submission draft

## Project name

FleetShield

## Tagline

One failure immunizes the fleet.

## Inspiration

Community-relief coordinators are an unlikely but high-stakes adopter of agents:
they route emergency grants, medicine vouchers, and shelter payments without a
dedicated reliability team. At the boundary between reasoning and side effects, a
tool may commit and then time out; a reasonable retry becomes an irreversible
duplicate action that consumes scarce aid funds.

We wanted an agent system that learns from a concrete operational failure without
letting another model-generated prompt become the safety boundary.

## What it does

FleetShield runs controlled experiments against sandboxed agents, captures a
counterexample, uses Gemini to propose typed business invariants, compiles them
into deterministic controls, and replays the exact fault. A policy reaches the
fleet only after benign regression tests, shadow evaluation, and human approval.

The demo starts with a relief agent that releases the same emergency grant twice
after a lost acknowledgement. It ends with the identical fault producing exactly
one grant and one blocked duplicate.

## How we built it

FleetShield runs a three-specialist Gemini 3.5 Flash team—Failure Analyst, Fleet
Scope Analyst, and Contract Miner—through the Google ADK `Runner` event loop.
Gemini interprets agent contracts and failing traces, but its typed output is
treated as untrusted input. A deterministic compiler creates stable policies and a
reference monitor intercepts tool calls before side effects. The
production path targets Cloud Run; the API accepts Pub/Sub-compatible events; and
the Firestore adapter stores policies, experiments, approvals, and replay evidence
when the cloud backend is enabled. A non-secret `/api/evidence` endpoint exposes the
actual runtime and disables cloud claims when only the local fallback is active.

The credential-free local proof uses the same deterministic engine and a sandbox
ledger, so judges can reproduce the critical safety claim without cloud access.

## Challenges

The hard part was avoiding a fake success. Blocking every retry prevents duplicates
but also breaks legitimate recovery. FleetShield therefore tests both the original
counterexample and benign control traffic. We also separate policy proposal from
activation: the model cannot approve its own rule.

## Accomplishments

- A failing side-effect scenario with a deterministic acceptance boundary
- Five controlled operational faults
- Three inspectable invariant types
- Shadow and blocking policy states
- Scoped propagation across a three-agent fleet
- Explicit delegation across three specialist Google ADK agents
- Exact replay with machine-readable evidence
- Credential-free dashboard and 14 passing tests
- Independent verifier for local proof and live Google Cloud evidence

## What we learned

Agent safety is not only a content-filtering problem. Once an agent can call tools,
the most dangerous failures look like distributed-systems bugs: duplicate delivery,
lost acknowledgement, stale state, and ambiguous commit results. LLMs are useful
for interpreting messy contracts; deterministic code must still own authorization.

## What's next

- Canonical hashes for counterexample bundles
- Firestore transactional ingress deduplication and policy activation
- Pub/Sub dead-letter and replay controls
- More invariant schemas and side-effect adapters
- Cross-framework MCP reference monitor

## AI disclosure

AI assistance was used to research, design, implement, test, and document the
project. Synthetic agents and sandbox side effects are clearly identified. Live
cloud and Gemini claims will be backed by deployment logs and reproducible evidence.

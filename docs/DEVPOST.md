# Devpost submission draft

## Project name

FleetShield

## Tagline

One failure immunizes the fleet.

## Inspiration

Autonomous agents fail at the boundary between reasoning and side effects. A
tool may commit and then time out; a queue may deliver twice; approval evidence
may be stale. The model often cannot distinguish “failed” from “succeeded but
unobserved,” so a reasonable retry becomes an irreversible duplicate action.

We wanted an agent system that learns from a concrete operational failure without
letting another model-generated prompt become the safety boundary.

## What it does

FleetShield runs controlled experiments against sandboxed agents, captures a
counterexample, uses Gemini to propose typed business invariants, compiles them
into deterministic controls, and replays the exact fault. A policy reaches the
fleet only after benign regression tests, shadow evaluation, and human approval.

The demo starts with an invoice agent that pays the same invoice twice after a
lost acknowledgement. It ends with the identical fault producing exactly one
payment and one blocked duplicate.

## How we built it

Gemini 3.5 Flash and Google ADK form the Contract Miner. Gemini interprets agent
contracts and failing traces, but its output is treated as untrusted structured
input. A deterministic compiler creates stable policies and a reference monitor
intercepts tool calls before side effects. Cloud Run hosts the control plane;
Pub/Sub supplies asynchronous, at-least-once events; Firestore stores contracts,
runs, approvals, ledger entries, and replay evidence.

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
- Exact replay with machine-readable evidence
- Credential-free tests and dashboard

## What we learned

Agent safety is not only a content-filtering problem. Once an agent can call tools,
the most dangerous failures look like distributed-systems bugs: duplicate delivery,
lost acknowledgement, stale state, and ambiguous commit results. LLMs are useful
for interpreting messy contracts; deterministic code must still own authorization.

## What's next

- Canonical hashes for counterexample bundles
- Firestore transactional policy activation
- Pub/Sub dead-letter and replay controls
- More invariant schemas and side-effect adapters
- Cross-framework MCP reference monitor

## AI disclosure

AI assistance was used to research, design, implement, test, and document the
project. Synthetic agents and sandbox side effects are clearly identified. Live
cloud and Gemini claims will be backed by deployment logs and reproducible evidence.


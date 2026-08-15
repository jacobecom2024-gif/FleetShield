# Judging map

FleetShield is designed against the published [All Things Agentic judging
criteria](https://allthingsagentichackathon.devpost.com/rules), not only the
technical eligibility checklist.

## Innovation and operational utility — 40%

- **Unlikely hero:** community-relief coordinators running emergency grants,
  medicine vouchers, and shelter payments without a dedicated SRE team.
- **High-value action:** the failure is a duplicated irreversible disbursement,
  not a weak chat response.
- **Autonomous delegation:** Google ADK routes one counterexample through a
  Failure Analyst, Fleet Scope Analyst, and Contract Miner.
- **Twist:** the output is not another recommendation. A witnessed failure becomes
  a typed, replay-tested safety control for a compatible agent fleet.

Video proof: show the duplicate grant, three-agent analysis source, compiled rule,
explicit approval boundary, and exact replay with one committed effect.

## Architectural discipline and tech stack — 30%

- Probabilistic interpretation is separated from deterministic authorization.
- Side effects are isolated behind a sandbox reference monitor.
- Policy scope uses a declared side-effect class, not semantic similarity.
- Pub/Sub ingress is deduplicated with a transactional Firestore claim.
- Cloud Run scales to zero and exposes non-secret runtime evidence.
- Local fallback is visibly labelled and cannot be mistaken for Gemini execution.
- Fourteen credential-free tests verify failure, enforcement, scope, approval,
  redelivery, and cloud-claim gating.

Video proof: open `/api/evidence`, the Cloud Run revision, compiled policy source,
and the independent verifier output.

## Demo and production readiness — 30%

- One-click 90-second proof plus manual four-stage workflow.
- Public source, architecture diagram, spin-up instructions, threat model, and
  bounded deployment configuration.
- Four-minute script prioritizes live action and machine-verifiable evidence.
- Cloud claims are disabled until ADK/Gemini actually executes on Cloud Run.

## Optional bonus path

- Publish a technical build article: up to +0.2.
- Publish a social post with `#AllThingsAgenticHackathon`: up to +0.2.
- Additional Google models: +0.2 each, up to +0.6, only if their integration adds
  real value and can be demonstrated honestly.

## Remaining gates

1. Receive and redeem the official hackathon Google Cloud credit.
2. Deploy, run the proof, and capture Google Cloud evidence.
3. Record and publish the public English/subtitled video.
4. Freeze the repository and submission during judging.

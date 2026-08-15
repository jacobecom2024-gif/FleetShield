from __future__ import annotations

from dataclasses import asdict
from uuid import uuid4

from .adk_agent import propose_invariants
from .contracts import DEMO_FLEET, AgentContract
from .faults import FaultName, stale
from .ledger import SandboxLedger
from .models import ActionIntent, Policy, ScenarioResult, TraceEvent, Violation, iso_now
from .policies import PolicyCompiler, PolicyEnforcer


class FleetShieldEngine:
    """Failure-driven policy discovery and deterministic replay engine."""

    def __init__(self) -> None:
        self.ledger = SandboxLedger()
        self.enforcer = PolicyEnforcer()
        self.fleet = {contract.agent_id: contract for contract in DEMO_FLEET}
        self.last_result: ScenarioResult | None = None
        self.history: list[ScenarioResult] = []
        self.processed_messages: set[str] = set()

    def reset_runtime(self, keep_policies: bool = True) -> None:
        self.ledger.reset()
        self.last_result = None
        if not keep_policies:
            self.enforcer = PolicyEnforcer()

    def run(self, fault: FaultName = "timeout_after_commit", agent_id: str = "invoice-agent") -> ScenarioResult:
        contract = self.fleet[agent_id]
        started = iso_now()
        run_id = str(uuid4())
        trace: list[TraceEvent] = []
        violations: list[Violation] = []
        blocked_actions = 0

        def event(event_type: str, message: str, status: str = "info", **data: object) -> None:
            trace.append(
                TraceEvent(
                    sequence=len(trace) + 1,
                    event_type=event_type,
                    message=message,
                    status=status,  # type: ignore[arg-type]
                    data=data,
                )
            )

        intent = ActionIntent(
            agent_id=contract.agent_id,
            tool_name=contract.tool_name,
            subject_id="INV-2026-0042",
            amount=249.0,
            approved=True,
            metadata={"run_id": run_id, "fault": fault},
        )
        event("run.started", f"{contract.display_name} received {intent.subject_id}", agent_id=agent_id)

        def execute(current: ActionIntent, label: str) -> bool:
            nonlocal blocked_actions
            blocked, found = self.enforcer.evaluate(current, self.ledger)
            violations.extend(found)
            for violation in found:
                event(
                    "policy.violation",
                    violation.reason,
                    "danger" if violation.mode == "blocking" else "warning",
                    policy_id=violation.policy_id,
                    mode=violation.mode,
                )
            if blocked:
                blocked_actions += 1
                event("action.blocked", f"{label} blocked before side effect", "success", action_id=current.action_id)
                return False
            entry = self.ledger.commit(current)
            event(
                "ledger.committed",
                f"Committed {current.currency} {current.amount:.2f} for {current.subject_id}",
                "success",
                entry_id=entry.entry_id,
                action_id=current.action_id,
            )
            return True

        if fault == "duplicate_event":
            execute(intent, "original event")
            event("fault.injected", "Pub/Sub delivered the same business event twice", "warning")
            execute(intent.clone_for_retry(), "duplicate event")
        elif fault == "timeout_after_commit":
            execute(intent, "original attempt")
            event("fault.injected", "Tool timed out after committing; acknowledgement was lost", "warning")
            event("agent.retry", "Agent retried because it could not observe the commit", "warning")
            execute(intent.clone_for_retry(), "retry")
        elif fault == "rate_limit_then_retry":
            event("fault.injected", "Tool returned HTTP 429 before commit", "warning")
            event("agent.retry", "Agent backed off and retried", "info")
            execute(intent.clone_for_retry(), "retry after rate limit")
        elif fault == "stale_evidence":
            event("fault.injected", "Approval evidence was replaced with a two-hour-old snapshot", "warning")
            execute(stale(intent), "stale-evidence attempt")
        elif fault == "malformed_tool_result":
            execute(intent, "original attempt")
            event("fault.injected", "Tool returned a malformed success payload after commit", "warning")
            event("agent.retry", "Agent interpreted the malformed payload as failure and retried", "warning")
            execute(intent.clone_for_retry(), "retry after malformed result")
        else:  # pragma: no cover - Literal protects callers
            raise ValueError(f"Unsupported fault: {fault}")

        actual = len(self.ledger.matching(contract.tool_name, intent.subject_id))
        safe = actual == contract.expected_cardinality and not any(v.mode == "shadow" for v in violations)
        event(
            "run.completed",
            "Invariant held" if safe else f"Invariant violated: expected 1 effect, observed {actual}",
            "success" if safe else "danger",
            expected=contract.expected_cardinality,
            actual=actual,
        )
        result = ScenarioResult(
            run_id=run_id,
            scenario=fault,
            safe=safe,
            expected_effects=contract.expected_cardinality,
            actual_effects=actual,
            blocked_actions=blocked_actions,
            violations=violations,
            trace=trace,
            ledger=self.ledger.entries(),
            started_at=started,
        )
        self.last_result = result
        self.history.append(result)
        return result

    def discover_from_last_failure(self) -> list[Policy]:
        if not self.last_result or self.last_result.safe:
            raise RuntimeError("A failing run is required before policy discovery")
        affected = self.fleet["invoice-agent"]
        same_class = [
            contract.agent_id
            for contract in self.fleet.values()
            if contract.side_effect_class == affected.side_effect_class
        ]
        proposal = propose_invariants(asdict(affected), self.last_result.to_dict())
        source = f"{proposal.get('source', 'unknown')}:counterexample:{self.last_result.run_id}"
        policies: list[Policy] = []
        for candidate in proposal.get("invariants", []):
            invariant_type = candidate.get("type")
            if invariant_type == "exactly_once":
                policies.append(PolicyCompiler.exactly_once(same_class, source))
            elif invariant_type == "approval_threshold":
                amount = float(candidate.get("amount", affected.approval_threshold))
                policies.append(PolicyCompiler.approval_threshold(amount, same_class, source))
            elif invariant_type == "fresh_evidence":
                max_age = int(candidate.get("max_age_seconds", affected.max_evidence_age_seconds))
                policies.append(PolicyCompiler.fresh_evidence(max_age, same_class, source))
        if not policies:
            raise RuntimeError("Contract Miner returned no allowlisted invariant candidates")
        for policy in policies:
            registered = self.enforcer.register(policy)
            registered.state = "shadow"
        return policies

    def activate_policy(self, policy_id: str, approved_by: str = "demo-reviewer") -> Policy:
        policy = next((item for item in self.enforcer.policies if item.policy_id == policy_id), None)
        if not policy:
            raise KeyError(policy_id)
        if policy.state != "shadow":
            raise RuntimeError("Only a shadow-tested policy can be activated")
        if not approved_by.strip():
            raise RuntimeError("A named human approval is required")
        policy.state = "active"
        policy.parameters["approved_by"] = approved_by
        policy.parameters["approved_at"] = iso_now()
        return policy

    def activate_exactly_once(self) -> Policy:
        policy = next(
            (item for item in self.enforcer.policies if item.invariant_type == "exactly_once"),
            None,
        )
        if not policy:
            raise RuntimeError("Discover policies before activation")
        return self.activate_policy(policy.policy_id)

    def full_demo(self) -> dict[str, object]:
        self.reset_runtime(keep_policies=False)
        vulnerable = self.run("timeout_after_commit")
        discovered = self.discover_from_last_failure()
        activated = self.activate_exactly_once()
        self.reset_runtime(keep_policies=True)
        protected = self.run("timeout_after_commit")
        return {
            "vulnerable": vulnerable.to_dict(),
            "discovered": [asdict(policy) for policy in discovered],
            "activated": asdict(activated),
            "protected": protected.to_dict(),
            "claim": "One failure produced a tested, deterministic control for the financial agent fleet.",
        }

    def handle_event_once(self, message_id: str, fault: FaultName) -> ScenarioResult | None:
        """Idempotent ingress for at-least-once event delivery.

        Returning ``None`` means the message was already processed and produced no
        additional experiment or side effect.
        """

        if message_id in self.processed_messages:
            return None
        self.processed_messages.add(message_id)
        return self.run(fault)

    def snapshot(self) -> dict[str, object]:
        return {
            "fleet": [asdict(contract) for contract in self.fleet.values()],
            "policies": self.enforcer.snapshot(),
            "ledger": self.ledger.snapshot(),
            "last_result": self.last_result.to_dict() if self.last_result else None,
            "runs": len(self.history),
            "processed_messages": sorted(self.processed_messages),
        }

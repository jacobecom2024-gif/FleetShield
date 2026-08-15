from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
from typing import Iterable

from .ledger import SandboxLedger
from .models import ActionIntent, Policy, Violation


def stable_policy_id(invariant_type: str, parameters: dict[str, object]) -> str:
    material = f"{invariant_type}:{sorted(parameters.items())}".encode()
    return f"policy-{sha256(material).hexdigest()[:10]}"


class PolicyCompiler:
    """Compiles structured invariants into deterministic, auditable policies."""

    @staticmethod
    def exactly_once(scope: Iterable[str], discovered_from: str) -> Policy:
        scope_list = sorted(set(scope))
        parameters = {"key": ["tool_name", "subject_id"]}
        return Policy(
            policy_id=stable_policy_id("exactly_once", parameters),
            name="Exactly-once side effects",
            invariant_type="exactly_once",
            description="A business subject may produce at most one committed side effect per tool.",
            expression="count(ledger, e, e.tool_name == action.tool_name && e.subject_id == action.subject_id) == 0",
            parameters=parameters,
            scope=scope_list,
            discovered_from=discovered_from,
        )

    @staticmethod
    def approval_threshold(amount: float, scope: Iterable[str], discovered_from: str) -> Policy:
        parameters = {"amount": amount}
        return Policy(
            policy_id=stable_policy_id("approval_threshold", parameters),
            name="Human approval threshold",
            invariant_type="approval_threshold",
            description=f"Actions above {amount:g} require explicit approval.",
            expression=f"action.amount <= {amount:g} || action.approved == true",
            parameters=parameters,
            scope=sorted(set(scope)),
            discovered_from=discovered_from,
        )

    @staticmethod
    def fresh_evidence(max_age_seconds: int, scope: Iterable[str], discovered_from: str) -> Policy:
        parameters = {"max_age_seconds": max_age_seconds}
        return Policy(
            policy_id=stable_policy_id("fresh_evidence", parameters),
            name="Fresh evidence required",
            invariant_type="fresh_evidence",
            description=f"Evidence must be no older than {max_age_seconds} seconds.",
            expression=f"now - timestamp(action.evidence_timestamp) <= duration('{max_age_seconds}s')",
            parameters=parameters,
            scope=sorted(set(scope)),
            discovered_from=discovered_from,
        )


class PolicyEnforcer:
    def __init__(self, policies: list[Policy] | None = None) -> None:
        self.policies = policies or []

    def register(self, policy: Policy) -> Policy:
        existing = next((item for item in self.policies if item.policy_id == policy.policy_id), None)
        if existing:
            return existing
        self.policies.append(policy)
        return policy

    def evaluate(self, intent: ActionIntent, ledger: SandboxLedger) -> tuple[bool, list[Violation]]:
        violations: list[Violation] = []
        blocked = False
        for policy in self.policies:
            if policy.state == "proposed" or (policy.scope and intent.agent_id not in policy.scope):
                continue
            reason = self._violation_reason(policy, intent, ledger)
            if not reason:
                continue
            mode = "blocking" if policy.state == "active" else "shadow"
            violations.append(
                Violation(
                    policy_id=policy.policy_id,
                    invariant=policy.name,
                    action_id=intent.action_id,
                    reason=reason,
                    mode=mode,
                )
            )
            blocked = blocked or mode == "blocking"
        return blocked, violations

    @staticmethod
    def _violation_reason(policy: Policy, intent: ActionIntent, ledger: SandboxLedger) -> str | None:
        if policy.invariant_type == "exactly_once":
            matches = ledger.matching(intent.tool_name, intent.subject_id)
            if matches:
                return f"{len(matches)} effect(s) already committed for {intent.tool_name}:{intent.subject_id}"
        elif policy.invariant_type == "approval_threshold":
            threshold = float(policy.parameters["amount"])
            if intent.amount > threshold and not intent.approved:
                return f"Amount {intent.amount:g} exceeds approval threshold {threshold:g}"
        elif policy.invariant_type == "fresh_evidence":
            max_age = int(policy.parameters["max_age_seconds"])
            evidence = datetime.fromisoformat(intent.evidence_timestamp.replace("Z", "+00:00"))
            age = (datetime.now(timezone.utc) - evidence.astimezone(timezone.utc)).total_seconds()
            if age > max_age:
                return f"Evidence age {int(age)}s exceeds maximum {max_age}s"
        return None

    def snapshot(self) -> list[dict[str, object]]:
        return [asdict(policy) for policy in self.policies]


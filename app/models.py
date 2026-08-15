from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any, Literal
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().isoformat()


@dataclass(slots=True)
class ActionIntent:
    agent_id: str
    tool_name: str
    subject_id: str
    amount: float = 0.0
    currency: str = "USD"
    approved: bool = False
    evidence_timestamp: str = field(default_factory=iso_now)
    action_id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict[str, Any] = field(default_factory=dict)

    def clone_for_retry(self) -> "ActionIntent":
        data = asdict(self)
        data["action_id"] = str(uuid4())
        data["metadata"] = {**self.metadata, "retry_of": self.action_id}
        return ActionIntent(**data)


@dataclass(slots=True)
class LedgerEntry:
    entry_id: str
    action_id: str
    agent_id: str
    tool_name: str
    subject_id: str
    amount: float
    currency: str
    committed_at: str = field(default_factory=iso_now)


@dataclass(slots=True)
class Violation:
    policy_id: str
    invariant: str
    action_id: str
    reason: str
    mode: Literal["shadow", "blocking"]
    detected_at: str = field(default_factory=iso_now)


@dataclass(slots=True)
class TraceEvent:
    sequence: int
    event_type: str
    message: str
    status: Literal["info", "success", "warning", "danger"] = "info"
    data: dict[str, Any] = field(default_factory=dict)
    occurred_at: str = field(default_factory=iso_now)


@dataclass(slots=True)
class Policy:
    policy_id: str
    name: str
    invariant_type: Literal["exactly_once", "approval_threshold", "fresh_evidence"]
    description: str
    expression: str
    state: Literal["proposed", "shadow", "active"] = "proposed"
    parameters: dict[str, Any] = field(default_factory=dict)
    scope: list[str] = field(default_factory=list)
    discovered_from: str = ""
    created_at: str = field(default_factory=iso_now)


@dataclass(slots=True)
class ScenarioResult:
    run_id: str
    scenario: str
    safe: bool
    expected_effects: int
    actual_effects: int
    blocked_actions: int
    violations: list[Violation]
    trace: list[TraceEvent]
    ledger: list[LedgerEntry]
    started_at: str
    completed_at: str = field(default_factory=iso_now)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        proof_material = {
            "run_id": self.run_id,
            "scenario": self.scenario,
            "safe": self.safe,
            "expected_effects": self.expected_effects,
            "actual_effects": self.actual_effects,
            "blocked_actions": self.blocked_actions,
            "ledger": payload["ledger"],
            "violations": payload["violations"],
        }
        canonical = json.dumps(proof_material, sort_keys=True, separators=(",", ":"), default=str)
        payload["proof_hash"] = sha256(canonical.encode()).hexdigest()
        return payload

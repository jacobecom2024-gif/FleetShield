from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class AgentContract:
    agent_id: str
    display_name: str
    tool_name: str
    side_effect_class: str
    expected_cardinality: int = 1
    approval_threshold: float = 500.0
    max_evidence_age_seconds: int = 900
    promises: list[str] = field(default_factory=list)


DEMO_FLEET: tuple[AgentContract, ...] = (
    AgentContract(
        agent_id="relief-disbursement-agent",
        display_name="Relief Disbursement Agent",
        tool_name="release_emergency_grant",
        side_effect_class="community_relief_funds",
        promises=["Release each approved emergency grant once", "Never reuse stale eligibility evidence"],
    ),
    AgentContract(
        agent_id="medicine-voucher-agent",
        display_name="Medicine Voucher Agent",
        tool_name="issue_medicine_voucher",
        side_effect_class="community_relief_funds",
        promises=["Issue each approved medicine voucher once", "Escalate high-value aid"],
    ),
    AgentContract(
        agent_id="shelter-payment-agent",
        display_name="Shelter Payment Agent",
        tool_name="pay_shelter_provider",
        side_effect_class="community_relief_funds",
        promises=["Pay each approved shelter placement once", "Keep a durable audit trail"],
    ),
)

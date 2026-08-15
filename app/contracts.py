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
        agent_id="invoice-agent",
        display_name="Invoice Agent",
        tool_name="post_payment",
        side_effect_class="financial",
        promises=["Pay each approved invoice once", "Never reuse stale approval evidence"],
    ),
    AgentContract(
        agent_id="refund-agent",
        display_name="Refund Agent",
        tool_name="post_refund",
        side_effect_class="financial",
        promises=["Refund each order once", "Escalate high-value refunds"],
    ),
    AgentContract(
        agent_id="payout-agent",
        display_name="Payout Agent",
        tool_name="post_payout",
        side_effect_class="financial",
        promises=["Pay each approved payout once", "Keep a durable audit trail"],
    ),
)


"""Google ADK integration boundary.

The deterministic engine remains authoritative. Gemini interprets natural-language
contracts and proposes structured invariant candidates; it never commits side effects
or activates policies. Importing this module is optional for the local, credential-free
demo. The deployed hackathon build installs google-adk and uses ``root_agent``.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any
from uuid import uuid4


CONTRACT_MINER_INSTRUCTION = """
You are FleetShield's Contract Miner. Extract safety invariants from an agent
contract and observed counterexample. Return JSON only with a top-level
`invariants` array. Allowed types are exactly_once, approval_threshold, and
fresh_evidence. You propose candidates; a deterministic compiler validates and
enforces them. Never claim that a policy was activated or a side effect reversed.
""".strip()

FAILURE_ANALYST_INSTRUCTION = """
You are FleetShield's Failure Analyst. Inspect the agent contract and failing
trace. Identify the commit point, lost or ambiguous acknowledgement, retry path,
observed side effects, and violated business promise. Return a concise JSON
analysis. Do not propose or activate a policy.
""".strip()

SCOPE_ANALYST_INSTRUCTION = """
You are FleetShield's Fleet Scope Analyst. Inspect the original contract and
counterexample plus the prior failure analysis. Explain which declared
side-effect class is affected, what must remain out of scope, and which benign
behavior must still pass. Return concise JSON. Do not activate a policy.
""".strip()


def _fallback_proposal(contract: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": "deterministic-fallback",
        "invariants": [
            {"type": "exactly_once", "key": ["tool_name", "subject_id"]},
            {"type": "approval_threshold", "amount": contract.get("approval_threshold", 500)},
            {"type": "fresh_evidence", "max_age_seconds": contract.get("max_evidence_age_seconds", 900)},
        ],
    }


async def _run_adk(prompt: str) -> str:
    """Execute the Contract Miner through the ADK event loop."""

    if root_agent is None:
        raise RuntimeError("Google ADK is not installed in this environment")

    from google.adk.runners import Runner  # type: ignore[import-not-found]
    from google.adk.sessions import InMemorySessionService  # type: ignore[import-not-found]
    from google.genai import types  # type: ignore[import-not-found]

    app_name = "fleetshield"
    user_id = "contract-compiler"
    session_id = f"counterexample-{uuid4()}"
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
    )
    runner = Runner(agent=root_agent, app_name=app_name, session_service=session_service)
    message = types.Content(role="user", parts=[types.Part(text=prompt)])
    final_text = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=message,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            final_text = "".join(part.text or "" for part in event.content.parts)
    if not final_text:
        raise RuntimeError("Contract Miner returned no final response")
    return final_text


def propose_invariants(contract: dict[str, Any], counterexample: dict[str, Any]) -> dict[str, Any]:
    """Run Gemini through Google ADK, or return an explicit local proposal.

    The fallback exists solely to keep tests reproducible without credentials and is
    labelled in its output. Production evidence must show
    ``source=google-adk:gemini:multi-agent``.
    """

    if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GOOGLE_CLOUD_PROJECT"):
        return _fallback_proposal(contract)

    prompt = json.dumps({"contract": contract, "counterexample": counterexample}, indent=2)
    parsed = json.loads(asyncio.run(_run_adk(prompt)))
    if not isinstance(parsed, dict) or not isinstance(parsed.get("invariants"), list):
        raise RuntimeError("Contract Miner returned an invalid structured response")
    parsed["source"] = "google-adk:gemini:multi-agent"
    return parsed


def runtime_status() -> dict[str, Any]:
    """Return non-secret runtime facts for demo evidence and health checks."""

    configured = bool(os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_CLOUD_PROJECT"))
    return {
        "contract_miner": "google-adk:gemini:multi-agent" if configured and root_agent is not None else "deterministic-fallback",
        "adk_available": root_agent is not None,
        "agent_team": ["failure_analyst", "fleet_scope_analyst", "contract_miner"],
        "model": os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
        "vertex_ai": os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").lower() == "true",
    }


try:  # ADK discovery imports this symbol in deployed environments.
    from google.adk.agents import Agent, SequentialAgent  # type: ignore[import-not-found]
    from pydantic import BaseModel, Field  # type: ignore[import-not-found]
    from typing import Literal

    class InvariantCandidate(BaseModel):
        type: Literal["exactly_once", "approval_threshold", "fresh_evidence"]
        key: list[str] = Field(default_factory=list)
        amount: float | None = None
        max_age_seconds: int | None = None

    class ContractMinerOutput(BaseModel):
        invariants: list[InvariantCandidate]

    failure_analyst = Agent(
        name="failure_analyst",
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
        description="Normalizes ambiguous side-effect failures into a causal trace.",
        instruction=FAILURE_ANALYST_INSTRUCTION,
        output_key="failure_analysis",
    )
    fleet_scope_analyst = Agent(
        name="fleet_scope_analyst",
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
        description="Determines safe propagation scope and regression boundaries.",
        instruction=(
            SCOPE_ANALYST_INSTRUCTION
            + "\n\nPrior failure analysis:\n{failure_analysis}"
        ),
        output_key="scope_analysis",
    )
    contract_miner = Agent(
        name="fleetshield_contract_miner",
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
        description="Extracts candidate safety invariants from contracts and counterexamples.",
        instruction=(
            CONTRACT_MINER_INSTRUCTION
            + "\n\nFailure analysis:\n{failure_analysis}"
            + "\n\nFleet scope analysis:\n{scope_analysis}"
        ),
        output_schema=ContractMinerOutput,
    )
    root_agent = SequentialAgent(
        name="fleetshield_safety_team",
        description="Delegates failure analysis, fleet scoping, and invariant mining.",
        sub_agents=[failure_analyst, fleet_scope_analyst, contract_miner],
    )
except ImportError:  # Local tests deliberately run without cloud dependencies.
    root_agent = None

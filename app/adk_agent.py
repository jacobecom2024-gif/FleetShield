"""Google ADK integration boundary.

The deterministic engine remains authoritative. Gemini interprets natural-language
contracts and proposes structured invariant candidates; it never commits side effects
or activates policies. Importing this module is optional for the local, credential-free
demo. The deployed hackathon build installs google-adk and uses ``root_agent``.
"""

from __future__ import annotations

import json
import os
from typing import Any


INSTRUCTION = """
You are FleetShield's Contract Miner. Extract safety invariants from an agent
contract and observed counterexample. Return JSON only with a top-level
`invariants` array. Allowed types are exactly_once, approval_threshold, and
fresh_evidence. You propose candidates; a deterministic compiler validates and
enforces them. Never claim that a policy was activated or a side effect reversed.
""".strip()


def propose_invariants(contract: dict[str, Any], counterexample: dict[str, Any]) -> dict[str, Any]:
    """Call Gemini when configured; otherwise return an explicit local proposal.

    The fallback exists solely to keep tests reproducible without credentials and is
    labelled in its output. Production evidence must show ``source=gemini``.
    """

    if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GOOGLE_CLOUD_PROJECT"):
        return {
            "source": "deterministic-fallback",
            "invariants": [
                {"type": "exactly_once", "key": ["tool_name", "subject_id"]},
                {"type": "approval_threshold", "amount": contract.get("approval_threshold", 500)},
                {"type": "fresh_evidence", "max_age_seconds": contract.get("max_evidence_age_seconds", 900)},
            ],
        }

    from google import genai  # type: ignore[import-not-found]

    client = genai.Client()
    prompt = json.dumps({"contract": contract, "counterexample": counterexample}, indent=2)
    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
        contents=f"{INSTRUCTION}\n\nINPUT:\n{prompt}",
        config={"response_mime_type": "application/json"},
    )
    parsed = json.loads(response.text)
    parsed["source"] = "gemini"
    return parsed


try:  # ADK discovery imports this symbol in deployed environments.
    from google.adk.agents import Agent  # type: ignore[import-not-found]

    root_agent = Agent(
        name="fleetshield_contract_miner",
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
        description="Extracts candidate safety invariants from contracts and counterexamples.",
        instruction=INSTRUCTION,
    )
except ImportError:  # Local tests deliberately run without cloud dependencies.
    root_agent = None


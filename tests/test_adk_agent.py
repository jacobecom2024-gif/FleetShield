import os
import unittest
from unittest.mock import patch

from app.adk_agent import propose_invariants, runtime_status


class ContractMinerBoundaryTests(unittest.TestCase):
    def test_unconfigured_runtime_is_explicit_fallback(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            proposal = propose_invariants(
                {"approval_threshold": 250, "max_evidence_age_seconds": 60},
                {"actual_effects": 2},
            )
            self.assertEqual(proposal["source"], "deterministic-fallback")
            self.assertEqual(len(proposal["invariants"]), 3)

    def test_runtime_status_never_exposes_api_key(self) -> None:
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "do-not-leak"}, clear=True):
            status = runtime_status()
            self.assertNotIn("do-not-leak", repr(status))
            self.assertIn("model", status)


if __name__ == "__main__":
    unittest.main()

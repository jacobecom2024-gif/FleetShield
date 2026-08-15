import unittest
from datetime import datetime, timedelta, timezone

from app.engine import FleetShieldEngine
from app.models import ActionIntent
from app.policies import PolicyCompiler


class FleetShieldEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = FleetShieldEngine()

    def test_timeout_after_commit_duplicates_without_policy(self) -> None:
        result = self.engine.run("timeout_after_commit")
        self.assertFalse(result.safe)
        self.assertEqual(result.expected_effects, 1)
        self.assertEqual(result.actual_effects, 2)
        self.assertEqual(result.blocked_actions, 0)

    def test_exactly_once_policy_blocks_retry(self) -> None:
        self.engine.run("timeout_after_commit")
        self.engine.discover_from_last_failure()
        policy = self.engine.activate_exactly_once()
        self.assertEqual(policy.state, "active")

        self.engine.reset_runtime(keep_policies=True)
        result = self.engine.run("timeout_after_commit")
        self.assertTrue(result.safe)
        self.assertEqual(result.actual_effects, 1)
        self.assertEqual(result.blocked_actions, 1)
        self.assertTrue(any(v.mode == "blocking" for v in result.violations))

    def test_shadow_policy_observes_but_does_not_block(self) -> None:
        policy = PolicyCompiler.exactly_once(["relief-disbursement-agent"], "test")
        policy.state = "shadow"
        self.engine.enforcer.register(policy)

        result = self.engine.run("duplicate_event")
        self.assertFalse(result.safe)
        self.assertEqual(result.actual_effects, 2)
        self.assertEqual(result.blocked_actions, 0)
        self.assertTrue(any(v.mode == "shadow" for v in result.violations))

    def test_rate_limit_before_commit_does_not_duplicate(self) -> None:
        result = self.engine.run("rate_limit_then_retry")
        self.assertTrue(result.safe)
        self.assertEqual(result.actual_effects, 1)

    def test_stale_evidence_is_blocked(self) -> None:
        policy = PolicyCompiler.fresh_evidence(900, ["relief-disbursement-agent"], "test")
        policy.state = "active"
        self.engine.enforcer.register(policy)
        result = self.engine.run("stale_evidence")
        self.assertTrue(result.safe is False)  # expected effect was deliberately blocked
        self.assertEqual(result.actual_effects, 0)
        self.assertEqual(result.blocked_actions, 1)

    def test_full_demo_proves_improvement(self) -> None:
        demo = self.engine.full_demo()
        self.assertEqual(demo["vulnerable"]["actual_effects"], 2)
        self.assertEqual(demo["protected"]["actual_effects"], 1)
        self.assertTrue(demo["protected"]["safe"])

    def test_pubsub_style_redelivery_is_idempotent(self) -> None:
        first = self.engine.handle_event_once("message-7", "rate_limit_then_retry")
        second = self.engine.handle_event_once("message-7", "rate_limit_then_retry")
        self.assertIsNotNone(first)
        self.assertIsNone(second)
        self.assertEqual(len(self.engine.history), 1)

    def test_policy_activation_requires_shadow_and_named_approval(self) -> None:
        self.engine.run("timeout_after_commit")
        policies = self.engine.discover_from_last_failure()
        policy = policies[0]
        with self.assertRaises(RuntimeError):
            self.engine.activate_policy(policy.policy_id, "")
        policy.state = "proposed"
        with self.assertRaises(RuntimeError):
            self.engine.activate_policy(policy.policy_id, "reviewer")


if __name__ == "__main__":
    unittest.main()

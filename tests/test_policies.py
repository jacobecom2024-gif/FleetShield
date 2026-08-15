import unittest
from datetime import datetime, timedelta, timezone

from app.ledger import SandboxLedger
from app.models import ActionIntent
from app.policies import PolicyCompiler, PolicyEnforcer


class PolicyTests(unittest.TestCase):
    def test_policy_id_is_stable(self) -> None:
        first = PolicyCompiler.exactly_once(["b", "a"], "one")
        second = PolicyCompiler.exactly_once(["a", "b"], "two")
        self.assertEqual(first.policy_id, second.policy_id)

    def test_approval_threshold(self) -> None:
        policy = PolicyCompiler.approval_threshold(500, ["refund-agent"], "test")
        policy.state = "active"
        enforcer = PolicyEnforcer([policy])
        intent = ActionIntent(
            agent_id="refund-agent",
            tool_name="post_refund",
            subject_id="ORDER-9",
            amount=501,
            approved=False,
        )
        blocked, violations = enforcer.evaluate(intent, SandboxLedger())
        self.assertTrue(blocked)
        self.assertEqual(len(violations), 1)

    def test_policy_scope_is_enforced(self) -> None:
        policy = PolicyCompiler.approval_threshold(10, ["refund-agent"], "test")
        policy.state = "active"
        enforcer = PolicyEnforcer([policy])
        unrelated = ActionIntent(
            agent_id="invoice-agent",
            tool_name="post_payment",
            subject_id="INV-1",
            amount=999,
        )
        blocked, violations = enforcer.evaluate(unrelated, SandboxLedger())
        self.assertFalse(blocked)
        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()

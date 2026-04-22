from __future__ import annotations

import copy
import unittest

from support import SCRIPTS_DIR  # noqa: F401

import route_delegation_packets  # noqa: E402
import skill_routing  # noqa: E402


class RouteDelegationPacketTests(unittest.TestCase):
    def test_parallel_safe_capable_host_uses_parallel_split_without_wave_execution(self) -> None:
        registry = copy.deepcopy(skill_routing.load_registry())
        host = registry["host_capabilities"]
        host["active_tier"] = "parallel-workers"
        host["supports_subagents"] = True
        host["supports_parallel_subagents"] = True
        host["subagent_dispatch_skill"] = "forge-dispatching-parallel-agents"

        key, plan, host_skills = route_delegation_packets.choose_delegation_plan(
            "BUILD",
            "parallel-safe",
            "implementer-quality",
            registry,
            delegation_preference="auto",
        )

        self.assertEqual(key, "parallel-split")
        self.assertIsNotNone(plan)
        assert plan is not None
        self.assertEqual(plan["dispatch_mode"], "parallel-workers")
        self.assertNotIn("wave_execution", plan)
        self.assertEqual(host_skills, ["forge-dispatching-parallel-agents"])


if __name__ == "__main__":
    unittest.main()

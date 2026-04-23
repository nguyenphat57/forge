from __future__ import annotations

import copy
import inspect
import unittest

from support import SCRIPTS_DIR  # noqa: F401

import route_delegation_packets  # noqa: E402
import skill_routing  # noqa: E402


class RouteDelegationPacketTests(unittest.TestCase):
    def capable_registry(self) -> dict:
        registry = copy.deepcopy(skill_routing.load_registry())
        host = registry["host_capabilities"]
        host["active_tier"] = "parallel-workers"
        host["supports_subagents"] = True
        host["supports_parallel_subagents"] = True
        host["subagent_dispatch_skill"] = "forge-dispatching-parallel-agents"
        return registry

    def safe_packet(self, packet_id: str, owned_scope: str) -> dict:
        return {
            "packet_id": packet_id,
            "owned_files_or_write_scope": [owned_scope],
            "proof_before_progress": [f"{packet_id} proof"],
            "verification_to_rerun": [f"{packet_id} verification"],
            "depends_on_packets": [],
            "write_scope_conflicts": [],
            "overlap_risk_status": "none",
            "blockers": [],
        }

    def test_parallel_safe_capable_host_uses_parallel_split_without_wave_execution(self) -> None:
        registry = self.capable_registry()

        key, plan, host_skills = route_delegation_packets.choose_delegation_plan(
            "BUILD",
            "parallel-safe",
            "implementer-quality",
            registry,
        )

        self.assertEqual(key, "parallel-split")
        self.assertIsNotNone(plan)
        assert plan is not None
        self.assertEqual(plan["dispatch_mode"], "parallel-workers")
        self.assertNotIn("wave_execution", plan)
        self.assertEqual(host_skills, ["forge-dispatching-parallel-agents"])

    def test_safe_packet_candidates_auto_activate_parallel_split(self) -> None:
        registry = self.capable_registry()

        key, plan, host_skills = route_delegation_packets.choose_delegation_plan(
            "BUILD",
            None,
            "implementer-quality",
            registry,
            packet_candidates=[
                self.safe_packet("docs-slice", "docs/current/operator-surface.md"),
                self.safe_packet("tests-slice", "packages/forge-core/tests/test_route_delegation_packets.py"),
            ],
        )

        self.assertEqual(key, "parallel-split")
        assert plan is not None
        self.assertEqual(plan["dispatch_mode"], "parallel-workers")
        self.assertIn("packet-candidates-parallel-ready", plan["dispatch_reasons"])
        self.assertEqual(host_skills, ["forge-dispatching-parallel-agents"])

    def test_packet_candidates_with_overlap_fall_back_to_sequential_lanes(self) -> None:
        registry = self.capable_registry()

        key, plan, host_skills = route_delegation_packets.choose_delegation_plan(
            "BUILD",
            None,
            "implementer-quality",
            registry,
            packet_candidates=[
                self.safe_packet("first", "packages/forge-core/shared/route_delegation_packets.py"),
                self.safe_packet("second", "packages/forge-core/shared/route_delegation_packets.py"),
            ],
        )

        self.assertEqual(key, "sequential-lanes")
        assert plan is not None
        self.assertEqual(host_skills, [])
        self.assertIn("packet-write-scope-overlap", plan["fallback_reasons"])

    def test_packet_candidates_with_nested_scope_overlap_fall_back_to_sequential_lanes(self) -> None:
        registry = self.capable_registry()

        key, plan, host_skills = route_delegation_packets.choose_delegation_plan(
            "BUILD",
            None,
            "implementer-quality",
            registry,
            packet_candidates=[
                self.safe_packet("directory", "packages/forge-core/shared"),
                self.safe_packet("file", "packages/forge-core/shared/route_delegation_packets.py"),
            ],
        )

        self.assertEqual(key, "sequential-lanes")
        assert plan is not None
        self.assertEqual(host_skills, [])
        self.assertIn("packet-write-scope-overlap", plan["fallback_reasons"])

    def test_packet_candidates_missing_proof_fall_back_to_sequential_lanes(self) -> None:
        registry = self.capable_registry()
        missing_proof = self.safe_packet("missing-proof", "packages/forge-core/shared/route_host_capabilities.py")
        missing_proof["proof_before_progress"] = []

        key, plan, host_skills = route_delegation_packets.choose_delegation_plan(
            "BUILD",
            None,
            "implementer-quality",
            registry,
            packet_candidates=[
                missing_proof,
                self.safe_packet("good", "packages/forge-core/shared/route_lane_plans.py"),
            ],
        )

        self.assertEqual(key, "sequential-lanes")
        assert plan is not None
        self.assertEqual(host_skills, [])
        self.assertIn("packet-missing-proof", plan["fallback_reasons"])

    def test_packet_candidates_with_dependencies_fall_back_to_sequential_lanes(self) -> None:
        registry = self.capable_registry()
        dependent = self.safe_packet("dependent", "packages/forge-core/shared/route_lane_plans.py")
        dependent["depends_on_packets"] = ["foundation"]

        key, plan, host_skills = route_delegation_packets.choose_delegation_plan(
            "BUILD",
            None,
            "implementer-quality",
            registry,
            packet_candidates=[
                self.safe_packet("foundation", "packages/forge-core/shared/route_host_capabilities.py"),
                dependent,
            ],
        )

        self.assertEqual(key, "sequential-lanes")
        assert plan is not None
        self.assertEqual(host_skills, [])
        self.assertIn("packet-dependencies-block-parallel-dispatch", plan["fallback_reasons"])

    def test_delegation_plan_signature_matches_packet_routing_contract(self) -> None:
        signature = inspect.signature(route_delegation_packets.choose_delegation_plan)

        self.assertEqual(
            list(signature.parameters),
            [
                "intent",
                "execution_mode",
                "execution_pipeline_key",
                "registry",
                "packet_candidates",
            ],
        )


if __name__ == "__main__":
    unittest.main()

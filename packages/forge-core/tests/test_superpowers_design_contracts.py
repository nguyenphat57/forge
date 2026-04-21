from __future__ import annotations

import unittest

from support import ROOT_DIR


class SuperpowersDesignContractTests(unittest.TestCase):
    def test_brainstorm_contract_matches_superpowers_design_doc_generator(self) -> None:
        brainstorm = (ROOT_DIR / "workflows" / "design" / "brainstorm.md").read_text(encoding="utf-8")

        for token in (
            "one question at a time",
            "2-3 approaches",
            "Offer Visual Companion",
            "This offer MUST be its own message",
            "Do not combine it with clarifying questions",
            "would the user understand this better by seeing it than reading it?",
            "Use the browser",
            "Use the terminal",
            "Write design doc",
            "docs/specs/YYYY-MM-DD-<topic>-design.md",
            "commit the design document to git",
            "user review",
            "design-approved",
            "design-blocked",
        ):
            with self.subTest(token=token):
                self.assertIn(token, brainstorm)

        self.assertNotIn("direction-locked", brainstorm)
        self.assertNotIn("decision-blocked", brainstorm)

    def test_plan_contract_matches_superpowers_writing_plans_flow(self) -> None:
        plan = (ROOT_DIR / "workflows" / "design" / "plan.md").read_text(encoding="utf-8")

        for token in (
            "# [Feature Name] Implementation Plan",
            "For agentic workers",
            "REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans",
            "docs/plans/YYYY-MM-DD-<topic>-implementation-plan.md",
            "**Goal:**",
            "**Architecture:**",
            "**Tech Stack:**",
            "Bite-Sized Task Granularity",
            "Each step is one action (2-5 minutes)",
            "- [ ] **Step 1: Write the failing test**",
            "- [ ] **Step 5: Commit**",
            "No Placeholders",
            "Complete code in every step",
            "Plan complete and saved to",
            "Subagent-Driven",
            "Inline Execution",
            "execution choice",
        ):
            with self.subTest(token=token):
                self.assertIn(token, plan)


if __name__ == "__main__":
    unittest.main()

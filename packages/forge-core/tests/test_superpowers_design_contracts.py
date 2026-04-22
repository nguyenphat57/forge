from __future__ import annotations

import unittest

from support import ROOT_DIR


class SuperpowersDesignContractTests(unittest.TestCase):
    def test_brainstorm_contract_matches_superpowers_design_doc_generator(self) -> None:
        brainstorm = (ROOT_DIR / "skills" / "brainstorming" / "SKILL.md").read_text(encoding="utf-8")

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
            "user review",
            "design-approved",
            "design-blocked",
        ):
            with self.subTest(token=token):
                self.assertIn(token, brainstorm)

        self.assertNotIn("direction-locked", brainstorm)
        self.assertNotIn("decision-blocked", brainstorm)

    def test_plan_contract_matches_superpowers_writing_plans_flow(self) -> None:
        plan = (ROOT_DIR / "skills" / "writing-plans" / "SKILL.md").read_text(encoding="utf-8")

        for token in (
            "# [Feature Name] Implementation Plan",
            "For agentic workers",
            "REQUIRED SUB-SKILL: Use forge-subagent-driven-development (recommended) or forge-executing-plans",
            "docs/plans/YYYY-MM-DD-<topic>-implementation-plan.md",
            "**Goal:**",
            "**Architecture:**",
            "**Tech Stack:**",
            "File Structure",
            "Bite-Sized Task Granularity",
            "Task Template",
            "### Task N: Component or slice name",
            "## No Placeholders",
            "Every implementation task should be specific enough",
            "Plan Self-Review",
            "Plan complete and saved to",
            "Subagent-Driven",
            "Inline Execution",
            "execution mode",
        ):
            with self.subTest(token=token):
                self.assertIn(token, plan)


if __name__ == "__main__":
    unittest.main()

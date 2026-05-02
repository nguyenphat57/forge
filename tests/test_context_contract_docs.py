from __future__ import annotations

import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


class ContextContractDocsTests(unittest.TestCase):
    def test_readme_and_operator_surface_explain_context_persistence_boundary(self) -> None:
        readme = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
        operator_surface = (ROOT_DIR / "docs" / "current" / "operator-surface.md").read_text(encoding="utf-8")
        session_skill = (
            ROOT_DIR / "packages" / "forge-skills" / "session-management" / "SKILL.md"
        ).read_text(encoding="utf-8")

        for token in (
            "Context Persistence Contract",
            "Automatic state",
            "Save context",
            "Selective closeout",
            "Raw errors are not persisted as a first-class `.brain` record",
        ):
            with self.subTest(path="README.md", token=token):
                self.assertIn(token, readme)

        for token in (
            "## Context Persistence Boundary",
            "`save context` writes `.brain/session.json`",
            "Resume may auto-seed `.forge-artifacts/workflow-state/<project>/latest.json`",
            "`learning` entries are durable only through selective closeout",
            "Raw `error` output is not stored as a durable `.brain` record",
        ):
            with self.subTest(path="operator-surface.md", token=token):
                self.assertIn(token, operator_surface)

        for token in (
            "## Persistence Boundary",
            "Automatic restore and seeding",
            "Explicit save context",
            "Selective closeout",
            "There is no raw error persistence mode",
        ):
            with self.subTest(path="session-management/SKILL.md", token=token):
                self.assertIn(token, session_skill)


if __name__ == "__main__":
    unittest.main()

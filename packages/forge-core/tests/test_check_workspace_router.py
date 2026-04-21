from __future__ import annotations

import sys
import unittest
from argparse import Namespace
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import check_workspace_router  # noqa: E402


class WorkspaceRouterCheckTests(unittest.TestCase):
    def test_accepts_explicit_router_doc_with_non_skill_map_name(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            agent_dir = workspace / ".agent"
            skill_dir = agent_dir / "skills" / "python-fastapi"
            skill_dir.mkdir(parents=True)

            (workspace / "AGENTS.md").write_text(
                "Workspace routing lives in `.agent/router.md`.\n",
                encoding="utf-8",
            )
            (agent_dir / "router.md").write_text(
                "\n".join(
                    [
                        "## Scope Policy",
                        "Global orchestrator is `forge-runtime`.",
                        "## Local Skill Inventory",
                        "- `python-fastapi`",
                        "## Routing Map",
                        "Use `python-fastapi` for Python API work.",
                    ]
                ),
                encoding="utf-8",
            )
            (skill_dir / "SKILL.md").write_text(
                "## When Not To Use\n- When the repo is not Python.\n",
                encoding="utf-8",
            )
            (agent_dir / "routing-smoke-tests.md").write_text(
                "Covers `AGENTS.md` and `router.md`.\n",
                encoding="utf-8",
            )
            (agent_dir / "local-skill-guidance.md").write_text(
                "Keep local skills aligned with the workspace router.\n",
                encoding="utf-8",
            )

            report = check_workspace_router.check_workspace(
                Namespace(workspace=workspace, agents=None, router_map=None)
            )

        self.assertEqual(report["status"], "PASS")
        self.assertTrue(report["router_map"].endswith("router.md"))


if __name__ == "__main__":
    unittest.main()

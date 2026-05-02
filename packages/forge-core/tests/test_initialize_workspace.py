from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from support import forge_home_fixture, load_json_fixture, run_python_script, workspace_fixture

import common  # noqa: E402


class InitializeWorkspaceTests(unittest.TestCase):
    def _assert_path_suffixes(self, values: list[str], expected_suffixes: list[str], label: str) -> None:
        for suffix in expected_suffixes:
            with self.subTest(path_suffix=suffix, label=label):
                self.assertTrue(
                    any(value.replace("/", "\\").endswith(suffix.replace("/", "\\")) for value in values),
                    f"{label} missing suffix: {suffix!r}",
                )

    def test_initialize_workspace_preview_cases(self) -> None:
        for case in load_json_fixture("workspace_init_cases.json"):
            with self.subTest(case=case["name"]):
                workspace = workspace_fixture(case["workspace_fixture"])
                result = run_python_script(
                    "initialize_workspace.py",
                    "--workspace",
                    str(workspace),
                    "--format",
                    "json",
                    *case["args"],
                    env={"FORGE_HOME": str(forge_home_fixture(case.get("forge_home_fixture", "empty")))},
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                report = json.loads(result.stdout)

                self.assertEqual(report["workspace_mode"], case["expected_mode"])
                self.assertEqual(report["recommended_next_workflow"], case["expected_next_workflow"])
                self._assert_path_suffixes(report["created_files"], case.get("expected_created_files", []), "created_files")
                self._assert_path_suffixes(report["normalized_files"], case.get("expected_normalized_files", []), "normalized_files")
                self._assert_path_suffixes(report["reused_paths"], case.get("expected_reused_paths", []), "reused_paths")

    def test_initialize_workspace_apply_creates_default_docs_without_session_memory(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "greenfield"
            forge_home = Path(temp_dir) / "forge-home"
            result = run_python_script(
                "initialize_workspace.py",
                "--workspace",
                str(workspace),
                "--project-name",
                "Forge Demo",
                "--seed-preferences",
                "--apply",
                "--format",
                "json",
                env={"FORGE_HOME": str(forge_home)},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)

            self.assertEqual(report["workspace_mode"], "greenfield")
            self.assertEqual(report["recommended_next_workflow"], "brainstorm")
            self.assertTrue((workspace / "AGENTS.md").exists())
            self.assertTrue((workspace / "docs" / "PRODUCT.md").exists())
            self.assertTrue((workspace / "docs" / "STACK.md").exists())
            self.assertFalse((workspace / ".brain").exists())
            self.assertNotIn(str(workspace / ".brain" / "session.json"), report["created_files"])
            self.assertTrue(common.resolve_global_preferences_path(forge_home).exists())
            self.assertTrue((workspace / "docs" / "plans").exists())
            self.assertTrue((workspace / "docs" / "specs").exists())
            self.assertFalse((workspace / "docs" / "STATUS.md").exists())
            self.assertFalse((workspace / "docs" / "DECISIONS.md").exists())
            self.assertFalse((workspace / "docs" / "ERRORS.md").exists())
            self.assertTrue(report["blueprint_path"].endswith("forge-skills\\init\\references\\project-docs-blueprint.md"))

    def test_initialize_workspace_existing_with_docs_reuses_canonical_files(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "repo"
            (workspace / "docs").mkdir(parents=True, exist_ok=True)
            (workspace / "AGENTS.md").write_text("# Repo\n", encoding="utf-8")
            (workspace / "docs" / "PRODUCT.md").write_text("# Product\n", encoding="utf-8")
            (workspace / "docs" / "STACK.md").write_text("# Stack\n", encoding="utf-8")

            result = run_python_script(
                "initialize_workspace.py",
                "--workspace",
                str(workspace),
                "--apply",
                "--format",
                "json",
                env={"FORGE_HOME": str(Path(temp_dir) / "forge-home")},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)

            self.assertEqual(report["workspace_mode"], "existing-with-docs")
            self.assertIn(str(workspace / "AGENTS.md"), report["reused_paths"])
            self.assertIn(str(workspace / "docs" / "PRODUCT.md"), report["reused_paths"])
            self.assertIn(str(workspace / "docs" / "STACK.md"), report["reused_paths"])
            self.assertEqual(report["normalized_files"], [])

    def test_initialize_workspace_existing_no_docs_preview_prefers_plan(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "repo"
            (workspace / "src").mkdir(parents=True, exist_ok=True)
            (workspace / "src" / "app.ts").write_text("console.log('forge');\n", encoding="utf-8")

            result = run_python_script(
                "initialize_workspace.py",
                "--workspace",
                str(workspace),
                "--format",
                "json",
                env={"FORGE_HOME": str(Path(temp_dir) / "forge-home")},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)

            self.assertEqual(report["workspace_mode"], "existing-no-docs")
            self.assertEqual(report["recommended_next_workflow"], "plan")
            self.assertEqual(report["normalized_files"], [])
            self.assertIn(str(workspace / "AGENTS.md"), report["created_files"])

    def test_initialize_workspace_normalizes_existing_docs_and_adds_optional_docs(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "repo"
            workspace.mkdir(parents=True, exist_ok=True)
            (workspace / "README.md").write_text("# Shop App\nPOS checkout app.\n", encoding="utf-8")
            (workspace / "package.json").write_text(
                json.dumps(
                    {
                        "name": "shop-app",
                        "scripts": {"test": "vitest", "build": "vite build"},
                        "dependencies": {"next": "^15.0.0", "@prisma/client": "^6.0.0"},
                        "devDependencies": {"prisma": "^6.0.0"},
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            (workspace / "src").mkdir(parents=True, exist_ok=True)
            (workspace / "tests").mkdir(parents=True, exist_ok=True)
            (workspace / "prisma").mkdir(parents=True, exist_ok=True)
            (workspace / "prisma" / "schema.prisma").write_text("generator client { provider = \"prisma-client-js\" }\n", encoding="utf-8")
            (workspace / "Dockerfile").write_text("FROM node:22\n", encoding="utf-8")
            (workspace / "VERSION").write_text("0.1.0\n", encoding="utf-8")

            result = run_python_script(
                "initialize_workspace.py",
                "--workspace",
                str(workspace),
                "--apply",
                "--format",
                "json",
                env={"FORGE_HOME": str(Path(temp_dir) / "forge-home")},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)

            self.assertEqual(report["workspace_mode"], "normalize-existing-docs")
            self.assertIn(str(workspace / "docs" / "PRODUCT.md"), report["normalized_files"])
            self.assertIn(str(workspace / "docs" / "STACK.md"), report["normalized_files"])
            self.assertTrue((workspace / "docs" / "ARCHITECTURE.md").exists())
            self.assertTrue((workspace / "docs" / "QUALITY.md").exists())
            self.assertTrue((workspace / "docs" / "SCHEMA.md").exists())
            self.assertTrue((workspace / "docs" / "OPERATIONS.md").exists())
            self.assertFalse((workspace / "docs" / "CHANGELOG.md").exists())
            self.assertTrue((workspace / "docs" / "templates" / "FEATURE_TASK.md").exists())
            self.assertIn(str(workspace / "README.md"), report["reused_paths"])
            self.assertIn(str(workspace / "package.json"), report["reused_paths"])

    def test_initialize_workspace_can_seed_continuity_indexes(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "continuity"
            forge_home = Path(temp_dir) / "forge-home"
            result = run_python_script(
                "initialize_workspace.py",
                "--workspace",
                str(workspace),
                "--seed-continuity",
                "--apply",
                "--format",
                "json",
                env={"FORGE_HOME": str(forge_home)},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertTrue(report["seed_continuity"])
            self.assertTrue((workspace / ".brain" / "decisions.json").exists())
            self.assertTrue((workspace / ".brain" / "learnings.json").exists())
            self.assertFalse((workspace / ".brain" / "session.json").exists())
            self.assertEqual(report["recommended_next_workflow"], "brainstorm")

    def test_initialize_workspace_rejects_retired_preset_flag(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "preset"
            result = run_python_script(
                "initialize_workspace.py",
                "--workspace",
                str(workspace),
                "--preset",
                "nextjs-typescript-postgres/minimal-saas",
                "--format",
                "json",
                env={"FORGE_HOME": str(Path(temp_dir) / "forge-home")},
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--preset", result.stderr)


if __name__ == "__main__":
    unittest.main()

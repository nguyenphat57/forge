from __future__ import annotations

import json
import unittest
from pathlib import Path

from support import copied_workspace_fixture, reference_companion_environment, run_python_script, temporary_workspace


def _fake_runtime_tool(root: Path, bundle_name: str, *, doctor_status: str | None = None) -> Path:
    tool_root = root / bundle_name
    scripts_dir = tool_root / "scripts"
    scripts_dir.mkdir(parents=True)
    runtime_json = {
        "name": bundle_name,
        "kind": "runtime-tool",
        "host": "runtime",
    }
    (tool_root / "runtime.json").write_text(json.dumps(runtime_json, indent=2), encoding="utf-8")
    script_name = "forge_browse.py" if bundle_name == "forge-browse" else "forge_design.py"
    if doctor_status is None:
        script_body = "print({'status':'PASS'})\n"
    else:
        script_body = (
            "import json\n"
            "import sys\n"
            f"payload={{'status':'{doctor_status}','checks':{{'stub':{{'status':'{doctor_status}'}}}}}}\n"
            "print(json.dumps(payload))\n"
            f"raise SystemExit(0 if '{doctor_status}' == 'PASS' else 1)\n"
        )
    (scripts_dir / script_name).write_text(script_body, encoding="utf-8")
    return tool_root


class DoctorTests(unittest.TestCase):
    def test_doctor_passes_with_registered_runtime_tools(self) -> None:
        with temporary_workspace() as workspace:
            temp_root = workspace.parent
            registry_path = temp_root / "runtime-tools.json"
            (workspace / "README.md").write_text("# Workspace\n", encoding="utf-8")
            (workspace / "package.json").write_text('{"name":"doctor-workspace"}\n', encoding="utf-8")
            browse_root = _fake_runtime_tool(temp_root, "forge-browse", doctor_status="PASS")
            design_root = _fake_runtime_tool(temp_root, "forge-design", doctor_status="PASS")
            registry_payload = {
                "version": 1,
                "tools": {
                    "forge-browse": {"target": str(browse_root)},
                    "forge-design": {"target": str(design_root)},
                },
            }
            registry_path.write_text(json.dumps(registry_payload, indent=2), encoding="utf-8")
            result = run_python_script(
                "doctor.py",
                "--workspace",
                str(workspace),
                "--format",
                "json",
                env={"FORGE_RUNTIME_TOOLS_PATH": str(registry_path)},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "PASS")
            self.assertTrue(report["core_only_ready"])
            self.assertTrue(any("map_codebase.py" in item for item in report["next_actions"]))
            self.assertTrue((workspace / ".forge-artifacts" / "doctor" / "latest.json").exists())

    def test_doctor_warns_when_optional_runtime_tools_are_missing(self) -> None:
        with temporary_workspace() as workspace:
            (workspace / "README.md").write_text("# Workspace\n", encoding="utf-8")
            result = run_python_script("doctor.py", "--workspace", str(workspace), "--format", "json")

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertTrue(report["core_only_ready"])
            self.assertTrue(any("map_codebase.py" in item for item in report["next_actions"]))
            self.assertIn(report["status"], {"PASS", "WARN"})
            if report["status"] == "WARN":
                self.assertTrue(
                    {"Runtime tool registry", "forge-browse resolution"} & set(report["warnings"]),
                    report["warnings"],
                )
            else:
                self.assertEqual(report["warnings"], [])

    def test_doctor_strict_fails_on_warning(self) -> None:
        with temporary_workspace() as workspace:
            (workspace / "README.md").write_text("# Workspace\n", encoding="utf-8")
            result = run_python_script("doctor.py", "--workspace", str(workspace), "--format", "json", "--strict")

            report = json.loads(result.stdout)
            expected_returncode = 1 if report["status"] == "WARN" else 0
            self.assertEqual(result.returncode, expected_returncode, result.stderr)
            self.assertIn(report["status"], {"PASS", "WARN"})

    def test_doctor_fails_when_artifact_root_is_not_writable_directory(self) -> None:
        with temporary_workspace() as workspace:
            (workspace / "README.md").write_text("# Workspace\n", encoding="utf-8")
            (workspace / ".forge-artifacts").write_text("not-a-directory\n", encoding="utf-8")
            result = run_python_script("doctor.py", "--workspace", str(workspace), "--format", "json")

            self.assertEqual(result.returncode, 1, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "FAIL")
            self.assertIn("Artifact write access", report["blockers"])

    def test_doctor_detects_first_party_companion_checks(self) -> None:
        with copied_workspace_fixture("nextjs_postgres_workspace") as workspace, reference_companion_environment() as (_, companion_env):
            result = run_python_script("doctor.py", "--workspace", str(workspace), "--format", "json", env=companion_env)

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["companions"][0]["id"], "nextjs-typescript-postgres")
            self.assertEqual(report["companions"][0]["operator_profile"], "nextjs-prisma-app-router")
            self.assertEqual(report["companions"][0]["verification_pack"], "nextjs-production-ready")
            labels = {item["label"] for item in report["checks"]}
            self.assertIn("Next.js package", labels)
            self.assertIn("Postgres adapter", labels)

    def test_doctor_reports_registered_companion_state(self) -> None:
        with copied_workspace_fixture("nextjs_postgres_workspace") as workspace, reference_companion_environment() as (companion_root, _):
            temp_root = workspace.parent
            registry_path = temp_root / "companions.json"
            registry_payload = {
                "version": 1,
                "companions": {
                    "forge-nextjs-typescript-postgres": {
                        "id": "nextjs-typescript-postgres",
                        "package": "forge-nextjs-typescript-postgres",
                        "target": str(companion_root.resolve()),
                        "version": "0.1.0",
                    }
                },
            }
            registry_path.write_text(json.dumps(registry_payload, indent=2), encoding="utf-8")

            result = run_python_script(
                "doctor.py",
                "--workspace",
                str(workspace),
                "--format",
                "json",
                env={"FORGE_COMPANIONS_PATH": str(registry_path)},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["companions"][0]["id"], "nextjs-typescript-postgres")
            self.assertTrue(report["companions"][0]["registered"])
            self.assertEqual(report["companion_registry"]["path"], str(registry_path.resolve()))
            self.assertEqual(len(report["companion_registry"]["registered_companions"]), 1)


if __name__ == "__main__":
    unittest.main()

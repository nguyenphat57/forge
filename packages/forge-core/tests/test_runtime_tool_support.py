from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from support import ROOT_DIR, run_python_script

import runtime_tool_support  # noqa: E402


class RuntimeToolSupportTests(unittest.TestCase):
    def _make_runtime_tool(self, root: Path, bundle_name: str, script_name: str) -> Path:
        scripts_dir = root / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        (root / "runtime.json").write_text(
            json.dumps({"name": bundle_name, "host": "runtime"}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (scripts_dir / script_name).write_text(
            "import json\nprint(json.dumps({'status': 'PASS', 'tool': 'ok'}, ensure_ascii=False))\n",
            encoding="utf-8",
        )
        return root

    def test_resolve_runtime_tool_uses_registry_before_falling_back(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            registry_path = temp_root / "state" / "runtime-tools.json"
            browse_root = self._make_runtime_tool(temp_root / "forge-browse", "forge-browse", "forge_browse.py")
            runtime_tool_support.write_runtime_tool_registration(registry_path, "forge-browse", browse_root)
            original = os.environ.get("FORGE_RUNTIME_TOOLS_PATH")
            os.environ["FORGE_RUNTIME_TOOLS_PATH"] = str(registry_path)
            try:
                payload = runtime_tool_support.resolve_runtime_tool("forge-browse", bundle_root=ROOT_DIR)
            finally:
                if original is None:
                    os.environ.pop("FORGE_RUNTIME_TOOLS_PATH", None)
                else:
                    os.environ["FORGE_RUNTIME_TOOLS_PATH"] = original

        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["target"], str(browse_root.resolve()))
        self.assertEqual(payload["resolution_source"], "registry")

    def test_invoke_runtime_tool_passes_through_registered_cli_output(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            registry_path = temp_root / "state" / "runtime-tools.json"
            design_root = self._make_runtime_tool(temp_root / "forge-design", "forge-design", "forge_design.py")
            runtime_tool_support.write_runtime_tool_registration(registry_path, "forge-design", design_root)

            result = run_python_script(
                "invoke_runtime_tool.py",
                "forge-design",
                "board",
                "--format",
                "json",
                env={"FORGE_RUNTIME_TOOLS_PATH": str(registry_path)},
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["tool"], "ok")

    def test_invoke_runtime_tool_can_record_browser_proof_into_workflow_state(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            registry_path = temp_root / "state" / "runtime-tools.json"
            workspace = temp_root / "workspace"
            workspace.mkdir(parents=True, exist_ok=True)
            design_root = self._make_runtime_tool(temp_root / "forge-design", "forge-design", "forge_design.py")
            runtime_tool_support.write_runtime_tool_registration(registry_path, "forge-design", design_root)

            workflow_state_dir = workspace / ".forge-artifacts" / "workflow-state" / "example-project"
            workflow_state_dir.mkdir(parents=True, exist_ok=True)
            (workflow_state_dir / "latest.json").write_text(
                json.dumps(
                    {
                        "project": "Example Project",
                        "current_stage": "build",
                        "required_stage_chain": ["plan", "build", "test"],
                        "latest_execution": {
                            "kind": "execution-progress",
                            "label": "Checkout flow polish",
                            "packet_id": "packet-checkout-ui",
                            "status": "active",
                            "current_stage": "build",
                            "completion_state": "in-progress",
                            "next_steps": ["Run browser QA"],
                            "blockers": [],
                            "residual_risk": [],
                            "browser_qa_classification": "required-for-this-packet",
                            "browser_qa_scope": ["checkout flow"],
                            "browser_qa_status": "pending",
                        },
                    },
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = run_python_script(
                "invoke_runtime_tool.py",
                "--record-browser-proof",
                "--workspace",
                str(workspace),
                "--project-name",
                "Example Project",
                "--packet-id",
                "packet-checkout-ui",
                "--current-stage",
                "build",
                "forge-design",
                "board",
                "--format",
                "json",
                env={"FORGE_RUNTIME_TOOLS_PATH": str(registry_path)},
            )

            state = json.loads((workflow_state_dir / "latest.json").read_text(encoding="utf-8"))

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(state["latest_run"]["command_kind"], "browser-qa")
        self.assertEqual(state["latest_run"]["packet_id"], "packet-checkout-ui")
        self.assertEqual(state["latest_run"]["browser_proof_status"], "satisfied")
        self.assertEqual(state["latest_execution"]["browser_qa_status"], "satisfied")
        self.assertEqual(state["latest_execution"]["browser_qa_last_result"], "PASS")

    def test_invoke_runtime_tool_forwards_downstream_workspace_when_wrapper_records_proof(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            registry_path = temp_root / "state" / "runtime-tools.json"
            workspace = temp_root / "workspace"
            workspace.mkdir(parents=True, exist_ok=True)
            design_root = temp_root / "forge-design"
            scripts_dir = design_root / "scripts"
            scripts_dir.mkdir(parents=True, exist_ok=True)
            (design_root / "runtime.json").write_text(
                json.dumps({"name": "forge-design", "host": "runtime"}, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            (scripts_dir / "forge_design.py").write_text(
                (
                    "import argparse\n"
                    "import json\n"
                    "parser = argparse.ArgumentParser()\n"
                    "parser.add_argument('--workspace', required=True)\n"
                    "parser.add_argument('target')\n"
                    "args = parser.parse_args()\n"
                    "print(json.dumps({'status': 'PASS', 'workspace': args.workspace, 'target': args.target}, ensure_ascii=False))\n"
                ),
                encoding="utf-8",
            )
            runtime_tool_support.write_runtime_tool_registration(registry_path, "forge-design", design_root)

            result = run_python_script(
                "invoke_runtime_tool.py",
                "--record-browser-proof",
                "--workspace",
                str(workspace),
                "--project-name",
                "Example Project",
                "--packet-id",
                "packet-checkout-ui",
                "--current-stage",
                "build",
                "forge-design",
                "--workspace",
                "tool-runtime-root",
                "board",
                env={"FORGE_RUNTIME_TOOLS_PATH": str(registry_path)},
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["workspace"], "tool-runtime-root")
        self.assertEqual(payload["target"], "board")

    def test_resolve_runtime_tools_registry_path_uses_manifest_relative_path(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            bundle_root = temp_root / "forge-codex"
            registry_path = bundle_root / "state" / "runtime-tools.json"
            bundle_root.mkdir(parents=True, exist_ok=True)
            (bundle_root / "BUILD-MANIFEST.json").write_text(
                json.dumps(
                    {
                        "state": {
                            "scope": "adapter-global",
                            "runtime_tools_relative_path": "state/runtime-tools.json",
                        }
                    },
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            resolved = runtime_tool_support.resolve_runtime_tools_registry_path(bundle_root)

        self.assertEqual(resolved, registry_path.resolve())


if __name__ == "__main__":
    unittest.main()

import json
import os
import shutil
import socket
import subprocess
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT_DIR.parents[1]
SKILLS_ROOT = ROOT_DIR.parent / "forge-skills"
CORE_TOOL_DIR = ROOT_DIR / "tools" / "visual-companion" / "scripts"
TOOL_DIR = SKILLS_ROOT / "brainstorming" / "tools" / "visual-companion" / "scripts"
ASSETS = (
    "server.cjs",
    "frame-template.html",
    "helper.js",
    "start-server.sh",
    "stop-server.sh",
    "start-server.ps1",
    "stop-server.ps1",
)


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def read_started(process):
    deadline = time.time() + 8
    while time.time() < deadline:
        line = process.stdout.readline()
        if not line:
            if process.poll() is not None:
                break
            time.sleep(0.05)
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if payload.get("type") == "server-started":
            return payload
    stderr = process.stderr.read() if process.stderr else ""
    raise AssertionError(f"server did not start; exit={process.poll()} stderr={stderr}")


def get_text(url):
    with urllib.request.urlopen(url, timeout=5) as response:
        return response.read().decode("utf-8")


class VisualCompanionTests(unittest.TestCase):
    def test_visual_companion_assets_exist_and_stay_small(self):
        self.assertFalse(CORE_TOOL_DIR.exists(), "visual companion must be owned by brainstorming, not forge-core")
        for asset in ASSETS:
            path = TOOL_DIR / asset
            self.assertTrue(path.exists(), f"missing visual companion asset: {asset}")
            if path.suffix != ".md":
                line_count = len(path.read_text(encoding="utf-8").splitlines())
                self.assertLessEqual(line_count, 300, f"{asset} exceeds 300 lines")

    def test_current_docs_reference_current_forge_paths(self):
        docs = [
            ROOT_DIR / "SKILL.md",
            SKILLS_ROOT / "brainstorming" / "references" / "design" / "visual-companion-guidance.md",
        ]
        text = "\n".join(path.read_text(encoding="utf-8") for path in docs)
        self.assertIn("tools/visual-companion/scripts/start-server", text)
        self.assertIn("skill-local", text)
        self.assertIn(".forge-artifacts/visual-companion", text)
        self.assertNotRegex(text, r"\.[^/\s]+/brainstorm")

    def test_package_matrix_does_not_make_visual_companion_core_owned(self):
        matrix_path = REPO_ROOT / "docs" / "release" / "package-matrix.json"
        matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
        required_assets = {
            f"tools/visual-companion/scripts/{asset}" for asset in ASSETS
        }
        for bundle in matrix["bundles"]:
            required = set(bundle["required_bundle_paths"])
            leaked = sorted(required_assets & required)
            self.assertEqual([], leaked, f"{bundle['name']} still declares core-owned visual assets")

    @unittest.skipIf(shutil.which("node") is None, "Node.js is required for server smoke test")
    def test_server_serves_wrapped_fragment_and_files_safely(self):
        server_path = TOOL_DIR / "server.cjs"
        self.assertTrue(server_path.exists(), "server.cjs must exist before smoke test")
        port = free_port()
        with tempfile.TemporaryDirectory() as temp_dir:
            env = os.environ.copy()
            env.update(
                {
                    "FORGE_VISUAL_COMPANION_DIR": temp_dir,
                    "FORGE_VISUAL_COMPANION_HOST": "127.0.0.1",
                    "FORGE_VISUAL_COMPANION_URL_HOST": "localhost",
                    "FORGE_VISUAL_COMPANION_PORT": str(port),
                }
            )
            process = subprocess.Popen(
                ["node", str(server_path)],
                cwd=str(TOOL_DIR),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
            try:
                started = read_started(process)
                screen_dir = Path(started["screen_dir"])
                state_dir = Path(started["state_dir"])
                self.assertTrue(screen_dir.is_dir())
                self.assertTrue(state_dir.is_dir())

                (screen_dir / "layout.html").write_text(
                    '<main><h2 data-choice="a">Layout A</h2></main>',
                    encoding="utf-8",
                )
                body = get_text(f"http://127.0.0.1:{port}/")
                self.assertIn("Forge Visual Companion", body)
                self.assertIn("Layout A", body)
                self.assertIn("window.forgeVisualCompanion", body)

                (screen_dir / "asset.svg").write_text("<svg></svg>", encoding="utf-8")
                self.assertEqual("<svg></svg>", get_text(f"http://127.0.0.1:{port}/files/asset.svg"))
                with self.assertRaises(urllib.error.HTTPError) as raised:
                    get_text(f"http://127.0.0.1:{port}/files/../server.cjs")
                self.assertEqual(404, raised.exception.code)
            finally:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
                if process.stdout:
                    process.stdout.close()
                if process.stderr:
                    process.stderr.close()


if __name__ == "__main__":
    unittest.main()

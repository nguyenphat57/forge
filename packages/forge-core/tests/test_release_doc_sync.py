from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from support import run_python_script


class ReleaseDocSyncTests(unittest.TestCase):
    def test_release_doc_sync_warns_when_code_and_db_change_without_docs(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            result = run_python_script(
                "release_doc_sync.py",
                "--workspace",
                str(workspace),
                "--changed-path",
                "app/page.tsx",
                "--changed-path",
                "prisma/schema.prisma",
                "--format",
                "json",
            )

            self.assertEqual(result.returncode, 1, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "WARN")
            self.assertIn("architecture", report["suggested_doc_updates"])
            self.assertIn("release", report["suggested_doc_updates"])
            self.assertIn("product-surface", report["matched_rules"])
            self.assertIn("database-surface", report["matched_rules"])

    def test_release_doc_sync_passes_when_docs_are_touched_and_persisted(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            result = run_python_script(
                "release_doc_sync.py",
                "--workspace",
                str(workspace),
                "--changed-path",
                "app/page.tsx",
                "--changed-path",
                "prisma/schema.prisma",
                "--changed-path",
                "README.md",
                "--changed-path",
                "docs/architecture/data-flow.md",
                "--changed-path",
                "CHANGELOG.md",
                "--persist",
                "--format",
                "json",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "PASS")
            self.assertTrue((workspace / ".forge-artifacts" / "release-doc-sync" / "latest.json").exists())

    def test_release_doc_sync_flags_billing_and_auth_doc_gaps(self) -> None:
        with TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            result = run_python_script(
                "release_doc_sync.py",
                "--workspace",
                str(workspace),
                "--changed-path",
                "lib/auth/session.ts",
                "--changed-path",
                "app/api/webhooks/stripe/route.ts",
                "--changed-path",
                "docs/release/notes.md",
                "--format",
                "json",
            )

            self.assertEqual(result.returncode, 1, result.stderr)
            report = json.loads(result.stdout)
            self.assertIn("auth-surface", report["matched_rules"])
            self.assertIn("billing-surface", report["matched_rules"])
            self.assertIn("architecture", report["suggested_doc_updates"])
            self.assertIn("planning", report["suggested_doc_updates"])


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from support import reference_companion_environment

import companion_catalog  # noqa: E402
import companion_registry  # noqa: E402

class CompanionRegistryTests(unittest.TestCase):
    def test_write_companion_registration_persists_package_record(self) -> None:
        with TemporaryDirectory() as temp_dir, reference_companion_environment() as (companion_root, _):
            registry_path = Path(temp_dir) / "companions.json"

            record = companion_registry.write_companion_registration(registry_path, companion_root)
            payload = json.loads(registry_path.read_text(encoding="utf-8"))

            self.assertEqual(record["package"], "forge-nextjs-typescript-postgres")
            self.assertEqual(record["id"], "nextjs-typescript-postgres")
            self.assertEqual(payload["companions"]["forge-nextjs-typescript-postgres"]["target"], str(companion_root.resolve()))

    def test_candidate_roots_include_registered_companion_targets(self) -> None:
        with TemporaryDirectory() as temp_dir, reference_companion_environment() as (companion_root, _):
            registry_path = Path(temp_dir) / "companions.json"
            companion_registry.write_companion_registration(registry_path, companion_root)

            with patch.dict(os.environ, {"FORGE_COMPANIONS_PATH": str(registry_path)}):
                roots = companion_catalog._candidate_roots()

            self.assertIn(companion_root.resolve(), roots)


if __name__ == "__main__":
    unittest.main()

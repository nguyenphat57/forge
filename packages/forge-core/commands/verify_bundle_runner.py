from __future__ import annotations

from _forge_core_command import bootstrap_shared_paths, resolve_bundle_root

bootstrap_shared_paths()

import argparse
import importlib
import sys
import unittest
from pathlib import Path


ROOT_DIR = resolve_bundle_root(Path(__file__).resolve())


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one bundle test module with a stable local import path.")
    parser.add_argument("pattern", help="Test file pattern or module name")
    args = parser.parse_args()

    module_name = Path(args.pattern).stem
    sys.path.insert(0, str(ROOT_DIR / "tools"))
    sys.path.insert(0, str(ROOT_DIR / "shared"))
    sys.path.insert(0, str(ROOT_DIR / "commands"))
    sys.path.insert(0, str(ROOT_DIR / "tests"))
    module = importlib.import_module(module_name)
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())

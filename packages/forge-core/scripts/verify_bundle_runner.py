from __future__ import annotations

import argparse
import importlib
import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one bundle test module with a stable local import path.")
    parser.add_argument("pattern", help="Test file pattern or module name")
    args = parser.parse_args()

    module_name = Path(args.pattern).stem
    sys.path.insert(0, str(ROOT_DIR / "scripts"))
    sys.path.insert(0, str(ROOT_DIR / "tests"))
    module = importlib.import_module(module_name)
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())

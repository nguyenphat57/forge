from __future__ import annotations

import sys
import unittest
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

from release_repo_test_contracts import ReleaseRepoContractTests
from release_repo_test_install import ReleaseRepoInstallTests
from release_repo_test_overlays import ReleaseRepoOverlayTests


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from support import run_python_script


class CheckSpecPacketTests(unittest.TestCase):
    def test_check_spec_packet_flags_missing_sections_with_one_question(self) -> None:
        with TemporaryDirectory() as temp_dir:
            packet = Path(temp_dir) / "plan.md"
            packet.write_text(
                "\n".join(
                    [
                        "Implementation-ready packet:",
                        "- Sources: docs/specs/checkout-spec.md",
                        "- Slice 1: Retry failed checkout",
                    ]
                ),
                encoding="utf-8",
            )

            result = run_python_script(
                "check_spec_packet.py",
                "--source",
                str(packet),
                "--format",
                "json",
            )

            self.assertEqual(result.returncode, 1)
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "FAIL")
            self.assertEqual(len(report["missing_sections"]), 3)
            self.assertIn("Which baseline command or reproduction", report["clarification_question"])

    def test_check_spec_packet_passes_when_packet_is_complete(self) -> None:
        with TemporaryDirectory() as temp_dir:
            packet = Path(temp_dir) / "plan.md"
            packet.write_text(
                "\n".join(
                    [
                        "Implementation-ready packet:",
                        "- Sources: docs/specs/checkout-spec.md",
                        "- First slice: Retry failed checkout",
                        "- Baseline verification path: pytest tests/test_checkout.py -k retry",
                        "- Proof before progress: pytest tests/test_checkout.py -k retry",
                        "- Reopen only if: Retry touches payment authorization boundary",
                    ]
                ),
                encoding="utf-8",
            )

            result = run_python_script(
                "check_spec_packet.py",
                "--source",
                str(packet),
                "--format",
                "json",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["clarification_question"], None)


if __name__ == "__main__":
    unittest.main()

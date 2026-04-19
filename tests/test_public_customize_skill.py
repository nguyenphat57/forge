from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT_DIR / "skills" / "forge-customize"
SKILL_PATH = SKILL_DIR / "SKILL.md"


def _extract_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        raise AssertionError("SKILL.md must start with YAML frontmatter.")
    marker = "\n---\n"
    end = text.find(marker, 4)
    if end == -1:
        raise AssertionError("SKILL.md frontmatter is not closed.")
    return text[4:end], text[end + len(marker) :]


class PublicCustomizeSkillTests(unittest.TestCase):
    def test_public_customize_skill_exists_with_minimal_structure(self) -> None:
        self.assertTrue(SKILL_DIR.exists(), "Expected a standalone public skill directory at skills/forge-customize.")
        self.assertTrue(SKILL_PATH.exists(), "Expected skills/forge-customize/SKILL.md to exist.")
        self.assertTrue(
            (SKILL_DIR / "references" / "forge-preferences.md").exists(),
            "Expected a reference file documenting the canonical Forge preference contract.",
        )
        self.assertTrue(
            (SKILL_DIR / "references" / "forge-paths.md").exists(),
            "Expected a reference file documenting host-neutral Forge state locations.",
        )
        self.assertFalse((SKILL_DIR / "README.md").exists(), "Standalone skill should not ship a README.")

    def test_public_customize_skill_frontmatter_and_body_are_skills_sh_ready(self) -> None:
        text = SKILL_PATH.read_text(encoding="utf-8")
        frontmatter, body = _extract_frontmatter(text)

        self.assertRegex(frontmatter, re.compile(r"(?m)^name:\s*forge-customize\s*$"))
        description_match = re.search(r"(?m)^description:\s*\"?(?P<value>.+?)\"?\s*$", frontmatter)
        self.assertIsNotNone(description_match, "Expected SKILL.md to declare a description in frontmatter.")
        description = description_match.group("value")
        self.assertTrue(
            description.startswith("Use when "),
            "Description should follow the Superpowers trigger-first pattern and start with 'Use when '.",
        )
        self.assertIn("host-neutral", description)
        self.assertIn("Forge preferences", description)
        self.assertIn("language", description)
        self.assertIn("tone", description)

        self.assertIn("# Forge Customize", body)
        self.assertIn("## Overview", body)
        self.assertIn("Core principle:", body)
        self.assertIn("## When to Use", body)
        self.assertIn("## Quick Reference", body)
        self.assertIn("## Implementation", body)
        self.assertIn("## Example", body)
        self.assertIn("## Common Mistakes", body)
        self.assertIn("## References", body)
        self.assertRegex(body, re.compile(r"When NOT to use|Do not use", re.IGNORECASE))
        self.assertIn("references/forge-preferences.md", body)
        self.assertIn("references/forge-paths.md", body)
        self.assertIn("write_preferences.py", body)
        self.assertIn("resolve_preferences.py", body)
        self.assertIn("--scope workspace", body)
        self.assertIn("orthography", body)
        self.assertIn("Changed:", body)
        self.assertNotIn("package-matrix.json", body)
        self.assertLessEqual(len(text.splitlines()), 220, "Public standalone skill should stay concise.")


if __name__ == "__main__":
    unittest.main()

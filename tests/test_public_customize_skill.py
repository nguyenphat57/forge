from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT_DIR / "packages" / "forge-skills" / "customize"
SKILL_PATH = SKILL_DIR / "SKILL.md"
LEGACY_STANDALONE_DIR = ROOT_DIR / "skills" / "forge-customize"
CORE_DIR = ROOT_DIR / "packages" / "forge-core"


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
        self.assertTrue(SKILL_DIR.exists(), "Expected a canonical sibling skill directory at packages/forge-skills/customize.")
        self.assertTrue(SKILL_PATH.exists(), "Expected packages/forge-skills/customize/SKILL.md to exist.")
        self.assertFalse(
            LEGACY_STANDALONE_DIR.exists(),
            "Legacy standalone skills/forge-customize should be removed after moving the canonical skill into packages/forge-skills.",
        )
        self.assertTrue(
            (SKILL_DIR / "references" / "forge-preferences.md").exists(),
            "Expected a reference file documenting the canonical Forge preference contract.",
        )
        self.assertTrue(
            (SKILL_DIR / "references" / "forge-paths.md").exists(),
            "Expected a reference file documenting host-neutral Forge state locations.",
        )
        self.assertFalse((SKILL_DIR / "README.md").exists(), "Sibling skill should not ship a README.")

    def test_customize_runtime_is_owned_by_customize_skill_not_core(self) -> None:
        owner_paths = [
            "commands/resolve_preferences.py",
            "commands/write_preferences.py",
            "data/preferences-schema.json",
            "shared/compat.py",
            "shared/compat_paths.py",
            "shared/compat_serialize.py",
            "shared/compat_translation.py",
            "shared/preferences.py",
            "shared/preferences_contract.py",
            "shared/preferences_paths.py",
            "shared/preferences_store.py",
        ]
        for relative_path in owner_paths:
            with self.subTest(owner_path=relative_path):
                self.assertTrue(
                    (SKILL_DIR / relative_path).exists(),
                    f"Expected forge-customize to own runtime file {relative_path}.",
                )
                self.assertFalse(
                    (CORE_DIR / relative_path).exists(),
                    f"forge-core must not keep customize-owned runtime file {relative_path}.",
                )

    def test_public_customize_skill_frontmatter_and_body_are_skills_sh_ready(self) -> None:
        text = SKILL_PATH.read_text(encoding="utf-8")
        frontmatter, body = _extract_frontmatter(text)

        self.assertRegex(frontmatter, re.compile(r"(?m)^name:\s*forge-customize\s*$"))
        description_match = re.search(r"(?m)^description:\s*\"?(?P<value>.+?)\"?\s*$", frontmatter)
        self.assertIsNotNone(description_match, "Expected SKILL.md to declare a description in frontmatter.")
        description = description_match.group("value")
        self.assertTrue(
            description.startswith("Use when "),
            "Description should follow the trigger-first pattern and start with 'Use when '.",
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

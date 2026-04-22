from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

from support import ROOT_DIR


FORGE_SPLIT_SKILLS = {
    "brainstorming": {
        "package": "forge-brainstorming",
        "path": "skills/brainstorming/SKILL.md",
        "budget": 240,
    },
    "writing-plans": {
        "package": "forge-writing-plans",
        "path": "skills/writing-plans/SKILL.md",
        "budget": 200,
    },
    "executing-plans": {
        "package": "forge-executing-plans",
        "path": "skills/executing-plans/SKILL.md",
        "budget": 200,
    },
    "test-driven-development": {
        "package": "forge-test-driven-development",
        "path": "skills/test-driven-development/SKILL.md",
        "budget": 320,
    },
    "using-git-worktrees": {
        "package": "forge-using-git-worktrees",
        "path": "skills/using-git-worktrees/SKILL.md",
        "budget": 220,
    },
    "dispatching-parallel-agents": {
        "package": "forge-dispatching-parallel-agents",
        "path": "skills/dispatching-parallel-agents/SKILL.md",
        "budget": 200,
    },
    "subagent-driven-development": {
        "package": "forge-subagent-driven-development",
        "path": "skills/subagent-driven-development/SKILL.md",
        "budget": 280,
    },
    "systematic-debugging": {
        "package": "forge-systematic-debugging",
        "path": "skills/systematic-debugging/SKILL.md",
        "budget": 320,
    },
    "requesting-code-review": {
        "package": "forge-requesting-code-review",
        "path": "skills/requesting-code-review/SKILL.md",
        "budget": 200,
    },
    "receiving-code-review": {
        "package": "forge-receiving-code-review",
        "path": "skills/receiving-code-review/SKILL.md",
        "budget": 200,
    },
    "verification-before-completion": {
        "package": "forge-verification-before-completion",
        "path": "skills/verification-before-completion/SKILL.md",
        "budget": 200,
    },
    "finishing-a-development-branch": {
        "package": "forge-finishing-a-development-branch",
        "path": "skills/finishing-a-development-branch/SKILL.md",
        "budget": 260,
    },
    "writing-skills": {
        "package": "forge-writing-skills",
        "path": "skills/writing-skills/SKILL.md",
        "budget": 720,
        "copied_tdd_doc_style": True,
    },
    "session-management": {
        "package": "forge-session-management",
        "path": "skills/session-management/SKILL.md",
        "budget": 200,
    },
}

OPERATOR_WORKFLOW_ALLOWLIST = {
    "workflows/operator/bump.md",
    "workflows/operator/customize.md",
    "workflows/operator/help.md",
    "workflows/operator/init.md",
    "workflows/operator/next.md",
    "workflows/operator/rollback.md",
    "workflows/operator/run.md",
    "workflows/operator/session.md",
}

OPTIONAL_ADAPTER_WORKFLOW_ALLOWLIST = {
    "workflows/execution/dispatch-subagents.md",
}

FORBIDDEN_ACTIVE_TESTS = {
    "tests/test_router_matrix.py",
    "tests/test_route_complexity_safety.py",
    "tests/test_route_matrix.py",
    "tests/test_route_preview.py",
    "tests/test_legacy_route_preview.py",
}

FORBIDDEN_RESIDUE_DIRS = {
    ".pytest_cache",
    "scripts/__pycache__",
    "tests/__pycache__",
}

RETIRED_ACTIVE_REFERENCES = {
    "references/companion-skill-contract.md": "docs/archive/history/2026-04-forge-core-cleanup/companion-skill-contract.md",
    "references/companion-routing-smoke-tests.md": "docs/archive/history/2026-04-forge-core-cleanup/companion-routing-smoke-tests.md",
    "references/canary-rollout.md": "docs/archive/history/2026-04-forge-core-cleanup/canary-rollout.md",
    "references/extension-presets.md": "docs/archive/history/2026-04-forge-core-cleanup/extension-presets.md",
    "references/frontend-stack-profiles.md": "docs/archive/history/2026-04-forge-core-cleanup/frontend-stack-profiles.md",
}


class BundleContractTests(unittest.TestCase):
    def _is_source_repo_context(self) -> bool:
        return (ROOT_DIR.parents[1] / ".git").exists()

    def _raw_line_count(self, path: Path) -> int:
        text = path.read_text(encoding="utf-8")
        return text.count("\n") + (0 if text.endswith("\n") else 1)

    def _tracked_repo_paths(self) -> set[str]:
        if not self._is_source_repo_context():
            return set()
        result = subprocess.run(
            ["git", "ls-files", "packages/forge-core"],
            cwd=ROOT_DIR.parents[1],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        return {line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()}

    def test_core_skill_contains_bootstrap_contract(self) -> None:
        skill = (ROOT_DIR / "SKILL.md").read_text(encoding="utf-8")
        lowered = skill.casefold()

        self.assertIn("<SUBAGENT-STOP>", skill)
        self.assertIn("<EXTREMELY-IMPORTANT>", skill)
        self.assertIn("1% chance", lowered)
        self.assertIn("before any response or action", lowered)
        self.assertIn("not negotiable", lowered)
        self.assertIn("questions are tasks", lowered)
        self.assertIn("process workflows first", lowered)
        self.assertIn("user instructions take precedence", lowered)

    def test_core_skill_red_flags_cover_common_rationalizations(self) -> None:
        skill = (ROOT_DIR / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("## Red Flags", skill)
        self.assertGreaterEqual(skill.count('| "'), 10)
        self.assertIn('I need more context before checking skills.', skill)
        self.assertIn('Let me explore the repo first.', skill)
        self.assertIn('I remember the skill already.', skill)
        self.assertIn('This workflow feels like overkill.', skill)

    def test_canonical_forge_skills_have_frontmatter_trigger_language_integration_and_line_budgets(self) -> None:
        for skill_name, expected in FORGE_SPLIT_SKILLS.items():
            path = ROOT_DIR / expected["path"]
            text = path.read_text(encoding="utf-8")
            frontmatter = text.split("---", 2)[1]
            lowered = text.casefold()
            with self.subTest(skill=skill_name):
                self.assertIn(f"name: {expected['package']}", frontmatter)
                self.assertIn("description:", frontmatter)
                self.assertIn("description: Use when", frontmatter)
                if expected.get("copied_tdd_doc_style"):
                    self.assertIn("Writing skills IS Test-Driven Development applied to process documentation.", text)
                else:
                    self.assertIn("<EXTREMELY-IMPORTANT>", text)
                    self.assertIn("## Integration", text)
                self.assertNotIn("1% chance", lowered)
                self.assertNotIn("1% rule", lowered)
                self.assertNotIn("route_preview.py", lowered)
                self.assertNotIn("deterministic routing", lowered)
                self.assertLessEqual(self._raw_line_count(path), expected["budget"])

    def test_skill_catalog_matches_canonical_skills(self) -> None:
        registry = json.loads((ROOT_DIR / "data" / "orchestrator-registry.json").read_text(encoding="utf-8"))
        skill_catalog = registry["skill_catalog"]
        self.assertEqual(set(skill_catalog), set(FORGE_SPLIT_SKILLS))

        for skill_name, expected in FORGE_SPLIT_SKILLS.items():
            entry = skill_catalog[skill_name]
            with self.subTest(skill=skill_name):
                self.assertEqual(entry["package"], expected["package"])
                self.assertEqual(entry["canonical_path"], expected["path"])
                self.assertNotIn("compatibility_workflow_path", entry)
                self.assertTrue(entry["trigger_summary"].strip())

    def test_workflow_priority_stays_process_first(self) -> None:
        registry = json.loads((ROOT_DIR / "data" / "orchestrator-registry.json").read_text(encoding="utf-8"))
        priority = registry["workflow_priority"]

        self.assertEqual(priority["process_first"], ["brainstorm", "debug", "session"])
        self.assertEqual(priority["planning_control"], ["plan", "quality-gate"])
        self.assertEqual(priority["implementation"], ["build", "refactor", "test", "review", "deploy", "secure"])

    def test_split_skills_own_tdd_debug_review_and_completion_contracts(self) -> None:
        build = (ROOT_DIR / "skills" / "executing-plans" / "SKILL.md").read_text(encoding="utf-8")
        tdd = (ROOT_DIR / "skills" / "test-driven-development" / "SKILL.md").read_text(encoding="utf-8")
        debug = (ROOT_DIR / "skills" / "systematic-debugging" / "SKILL.md").read_text(encoding="utf-8")
        review_request = (ROOT_DIR / "skills" / "requesting-code-review" / "SKILL.md").read_text(encoding="utf-8")
        review_receive = (ROOT_DIR / "skills" / "receiving-code-review" / "SKILL.md").read_text(encoding="utf-8")
        finish = (ROOT_DIR / "skills" / "finishing-a-development-branch" / "SKILL.md").read_text(encoding="utf-8")
        verify = (ROOT_DIR / "skills" / "verification-before-completion" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("Execution Loop", build)
        self.assertIn("Stop And Ask For Help", build)
        self.assertIn("Completion Handoff", build)
        self.assertIn("forge-finishing-a-development-branch", build)
        self.assertIn("NO HARNESS-CAPABLE BEHAVIOR CHANGE WITHOUT VERIFIED RED FIRST", tdd)
        self.assertIn("Delete it completely before restarting.", tdd)
        self.assertIn("Common Rationalizations", tdd)
        self.assertIn("Real-World Impact", tdd)
        self.assertIn("Good Tests", tdd)
        self.assertIn("Why Order Matters", tdd)
        self.assertIn("Verification Checklist", tdd)
        self.assertIn("When Stuck", tdd)
        self.assertIn("NO FIXES WITHOUT ROOT-CAUSE INVESTIGATION FIRST", debug)
        self.assertIn("The Four Phases", debug)
        self.assertIn("Phase 1: Root Cause", debug)
        self.assertIn("Read Error Messages Carefully", debug)
        self.assertIn("Reproduce Consistently", debug)
        self.assertIn("Check Recent Changes", debug)
        self.assertIn("Trace Data Flow Backward", debug)
        self.assertIn("Multi-Component Evidence Gathering", debug)
        self.assertIn("When You Do Not Know", debug)
        self.assertIn("If Three Fixes Fail, Reset The Lens", debug)
        self.assertIn("Human Signals You Are Guessing", debug)
        self.assertIn("Quick Reference", debug)
        self.assertIn("Supporting References", debug)
        self.assertIn("references/debugging/root-cause-tracing.md", debug)
        self.assertIn("references/debugging/defense-in-depth.md", debug)
        self.assertIn("references/debugging/condition-based-waiting.md", debug)
        self.assertIn("When The Root Cause Is External Or Environmental", debug)
        self.assertIn("Real-World Impact", debug)
        self.assertIn("Findings first", review_request)
        self.assertIn("review scope", review_request)
        self.assertIn("Core Principle", review_request)
        self.assertIn("When Review Is Mandatory", review_request)
        self.assertIn("Strong Review Packet Template", review_request)
        self.assertIn("Severity Contract", review_request)
        self.assertIn("Requesting A Subagent Review", review_request)
        self.assertIn("Acting On Review Results", review_request)
        self.assertIn("technically questionable", review_receive)
        self.assertIn("Response Pattern", review_receive)
        self.assertIn("Forbidden Responses", review_receive)
        self.assertIn("Clarify Before Partial Implementation", review_receive)
        self.assertIn("External Feedback Skepticism", review_receive)
        self.assertIn("YAGNI Check", review_receive)
        self.assertIn("Implementation Order", review_receive)
        self.assertIn("When To Push Back", review_receive)
        self.assertIn("GitHub And Threaded Reviews", review_receive)
        self.assertIn("Branch Resolution", finish)
        self.assertIn("Core Principle", finish)
        self.assertIn("Process Flow", finish)
        self.assertIn("Preflight", finish)
        self.assertIn("If Verification Fails", finish)
        self.assertIn("Presenting Options", finish)
        self.assertIn("Option 1: Merge Locally", finish)
        self.assertIn("Option 2: Push And PR", finish)
        self.assertIn("Option 3: Keep Branch", finish)
        self.assertIn("Option 4: Discard With Confirmation", finish)
        self.assertIn("Cleanup Rules", finish)
        self.assertIn("Final State Packet", finish)
        self.assertIn("NO CLAIMS WITHOUT FRESH EVIDENCE", verify)
        self.assertIn("Core Principle", verify)
        self.assertIn("Gate Function", verify)
        self.assertIn("Claim To Evidence Map", verify)
        self.assertIn("Evidence Packet", verify)
        self.assertIn("RED-GREEN Claims", verify)
        self.assertIn("Requirements Checklist", verify)
        self.assertIn("Not Verified Language", verify)
        self.assertIn("Agent reports are claims, not proof", verify)
        self.assertIn("Docs-only changes still need path, content, or diff verification.", verify)

    def test_design_and_plan_split_skills_include_richer_guidance(self) -> None:
        brainstorm = (ROOT_DIR / "skills" / "brainstorming" / "SKILL.md").read_text(encoding="utf-8")
        plan = (ROOT_DIR / "skills" / "writing-plans" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("Process Flow", brainstorm)
        self.assertIn("Visual Companion", brainstorm)
        self.assertIn("This offer MUST be its own message", brainstorm)
        self.assertIn("would the user understand this better by seeing it than reading it?", brainstorm)
        self.assertIn("references/design/visual-companion-guidance.md", brainstorm)
        self.assertIn("Architectural Lens", brainstorm)
        self.assertIn("references/design/architectural-lens.md", brainstorm)
        self.assertIn("multiple independent subsystems", brainstorm)
        self.assertIn("decompose before designing", brainstorm)
        self.assertIn("section-by-section approval", brainstorm)
        self.assertIn("Design For Isolation And Clarity", brainstorm)
        self.assertIn("Working In Existing Codebases", brainstorm)
        self.assertIn("Spec Self-Review Checklist", brainstorm)
        self.assertIn("type, method signature, and property name consistency", plan)
        self.assertIn("File Structure", plan)
        self.assertIn("Bite-Sized Task Granularity", plan)
        self.assertIn("Task Template", plan)
        self.assertIn("### Task N: Component or slice name", plan)
        self.assertIn("## No Placeholders", plan)
        self.assertIn("Plan Self-Review", plan)
        self.assertIn("Every implementation task should be specific enough", plan)
        self.assertIn("forge-subagent-driven-development", plan)
        self.assertIn("forge-executing-plans", plan)

    def test_session_management_skill_mentions_preferences_restore_contract(self) -> None:
        session = (ROOT_DIR / "skills" / "session-management" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("adapter-global", session)
        self.assertIn("state/preferences.json", session)
        self.assertIn("resolve_preferences.py", session)
        self.assertIn("session_context.py", session)
        self.assertIn("save context", session)
        self.assertIn("resume", session)
        self.assertIn("Response Personalization", session)
        self.assertIn("workflow-state", session)

    def test_writing_skills_is_copied_with_forge_brand_references(self) -> None:
        writing_skills = (ROOT_DIR / "skills" / "writing-skills" / "SKILL.md").read_text(encoding="utf-8")
        writing_skill_dir = ROOT_DIR / "skills" / "writing-skills"

        self.assertIn("Writing skills IS Test-Driven Development applied to process documentation.", writing_skills)
        self.assertIn("Claude Search Optimization", writing_skills)
        self.assertIn("NO SKILL WITHOUT A FAILING TEST FIRST", writing_skills)
        self.assertIn("RED-GREEN-REFACTOR for Skills", writing_skills)
        self.assertIn("Skill Creation Checklist", writing_skills)
        self.assertIn("forge-test-driven-development", writing_skills)
        self.assertIn("forge-systematic-debugging", writing_skills)
        for relative_path in (
            "anthropic-best-practices.md",
            "graphviz-conventions.dot",
            "persuasion-principles.md",
            "render-graphs.js",
            "testing-skills-with-subagents.md",
            "agents/openai.yaml",
            "examples/CLAUDE_MD_TESTING.md",
        ):
            with self.subTest(path=relative_path):
                self.assertTrue((writing_skill_dir / relative_path).exists())
        testing_reference = (writing_skill_dir / "testing-skills-with-subagents.md").read_text(encoding="utf-8")
        self.assertIn("forge-test-driven-development", testing_reference)

    def test_workflow_files_are_operator_only_thin_compatibility_wrappers(self) -> None:
        workflow_paths = sorted((ROOT_DIR / "workflows").glob("*/*.md"))
        relative_paths = {path.relative_to(ROOT_DIR).as_posix() for path in workflow_paths}

        self.assertFalse(relative_paths - OPERATOR_WORKFLOW_ALLOWLIST - OPTIONAL_ADAPTER_WORKFLOW_ALLOWLIST)
        self.assertFalse(OPERATOR_WORKFLOW_ALLOWLIST - relative_paths)

        for path in workflow_paths:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=str(path.relative_to(ROOT_DIR))):
                if "Compatibility Wrapper" in text:
                    self.assertLessEqual(self._raw_line_count(path), 40)
                    self.assertIn("forge-", text)
                else:
                    self.assertLessEqual(self._raw_line_count(path), 100)
                    self.assertTrue(
                        "Operator Wrapper" in text
                        or "Preference Wrapper" in text
                        or "Workspace Bootstrap" in text
                    )
                    self.assertTrue(
                        "Forge Codex:" in text
                        or "Forge Antigravity:" in text
                    )

    def test_generated_cache_and_bytecode_dirs_are_git_ignored_not_tracked(self) -> None:
        if not self._is_source_repo_context():
            self.skipTest("git tracked-path check only applies in the source repo")
        tracked_paths = self._tracked_repo_paths()

        for relative_path in FORBIDDEN_RESIDUE_DIRS:
            with self.subTest(path=relative_path):
                pattern = f"packages/forge-core/{relative_path}/"
                self.assertFalse(
                    any(path == pattern[:-1] or path.startswith(pattern) for path in tracked_paths)
                )

    def test_archived_route_coverage_tests_are_not_in_active_test_package(self) -> None:
        active_tests = {
            path.relative_to(ROOT_DIR).as_posix()
            for path in (ROOT_DIR / "tests").glob("test_*.py")
        }
        self.assertTrue(FORBIDDEN_ACTIVE_TESTS.isdisjoint(active_tests))

    def test_dead_workspace_signals_script_is_removed(self) -> None:
        self.assertFalse((ROOT_DIR / "scripts" / "workspace_signals.py").exists())

    def test_retired_companion_and_canary_references_leave_active_tree_but_stay_archived(self) -> None:
        reference_map = (ROOT_DIR / "references" / "reference-map.md").read_text(encoding="utf-8")
        repo_root = ROOT_DIR.parents[1]

        for active_path, archive_path in RETIRED_ACTIVE_REFERENCES.items():
            active_name = Path(active_path).name
            with self.subTest(reference=active_name):
                self.assertNotIn(f"`{active_name}`", reference_map)
                self.assertFalse((ROOT_DIR / active_path.removeprefix("references/")).exists())
                if self._is_source_repo_context():
                    self.assertTrue((repo_root / archive_path).exists())

    def test_route_preview_generator_stack_is_retired(self) -> None:
        smoke_matrix_suites = (ROOT_DIR / "scripts" / "smoke_matrix_suites.py").read_text(encoding="utf-8")
        smoke_matrix_cases = (ROOT_DIR / "scripts" / "smoke_matrix_cases.py").read_text(encoding="utf-8")
        smoke_matrix_validators = (ROOT_DIR / "scripts" / "smoke_matrix_validators.py").read_text(encoding="utf-8")

        for relative_path in (
            "scripts/route_local_companions.py",
            "scripts/route_preview.py",
            "scripts/route_preview_builder.py",
            "scripts/route_preview_output.py",
            "scripts/route_policy.py",
            "scripts/route_analysis.py",
            "scripts/route_execution_advice.py",
            "scripts/route_process_requirements.py",
            "scripts/route_stage_contract.py",
            "scripts/route_intent_detection.py",
            "scripts/route_quality_policy.py",
            "scripts/route_risk.py",
            "scripts/route_complexity_safety.py",
            "scripts/route_delegation.py",
            "tests/fixtures/route_preview_cases.json",
        ):
            with self.subTest(path=relative_path):
                self.assertFalse((ROOT_DIR / relative_path).exists())

        self.assertNotIn("route-preview", smoke_matrix_suites)
        self.assertNotIn("ROUTE_CASES", smoke_matrix_cases)
        self.assertNotIn("validate_route_case", smoke_matrix_validators)

    def test_tooling_reference_is_a_thin_pointer_not_a_second_monolith(self) -> None:
        tooling = ROOT_DIR / "references" / "tooling.md"
        text = tooling.read_text(encoding="utf-8")

        self.assertLessEqual(self._raw_line_count(tooling), 40)
        self.assertIn("kernel-tooling.md", text)
        self.assertIn("reference-map.md", text)
        self.assertIn("backend-briefs.md", text)
        self.assertIn("ui-briefs.md", text)
        self.assertIn("ui-progress.md", text)
        self.assertNotIn("python scripts/resolve_help_next.py", text)
        self.assertNotIn("python scripts/run_with_guidance.py", text)

    def test_subagent_reference_contract_exists(self) -> None:
        reference_map = (ROOT_DIR / "references" / "reference-map.md").read_text(encoding="utf-8")
        subagent_reference = ROOT_DIR / "references" / "subagent-execution.md"
        prompt_dir = ROOT_DIR / "references" / "subagent-prompts"

        self.assertIn("`subagent-execution.md`", reference_map)
        self.assertIn("`subagent-prompts/final-reviewer-prompt.md`", reference_map)
        self.assertTrue(subagent_reference.exists())
        for name in (
            "implementer-prompt.md",
            "spec-reviewer-prompt.md",
            "quality-reviewer-prompt.md",
            "final-reviewer-prompt.md",
        ):
            with self.subTest(prompt=name):
                self.assertTrue((prompt_dir / name).exists())

        subagent_text = subagent_reference.read_text(encoding="utf-8")
        self.assertIn("DONE_WITH_CONCERNS", subagent_text)
        self.assertIn("spec compliance before code quality", subagent_text)
        self.assertIn("packet-first dispatch", subagent_text)

    def test_tdd_discipline_reference_exists_and_captures_delete_rule(self) -> None:
        reference_map = (ROOT_DIR / "references" / "reference-map.md").read_text(encoding="utf-8")
        tdd_reference = ROOT_DIR / "references" / "tdd-discipline.md"

        self.assertIn("`tdd-discipline.md`", reference_map)
        self.assertTrue(tdd_reference.exists())

        discipline = tdd_reference.read_text(encoding="utf-8")
        self.assertIn("Delete means delete.", discipline)
        self.assertIn("RED -> GREEN -> REFACTOR", discipline)
        self.assertIn("named baseline is green too", discipline)
        self.assertIn("## Red Flags", discipline)

    def test_debugging_companion_references_exist_and_are_mapped(self) -> None:
        reference_map = (ROOT_DIR / "references" / "reference-map.md").read_text(encoding="utf-8")
        debug_skill = (ROOT_DIR / "skills" / "systematic-debugging" / "SKILL.md").read_text(encoding="utf-8")
        expected = {
            "debugging/root-cause-tracing.md": ("Root-Cause Tracing", "Backward Trace Packet"),
            "debugging/defense-in-depth.md": ("Defense-In-Depth Validation", "Forge-Specific Boundaries"),
            "debugging/condition-based-waiting.md": ("Condition-Based Waiting", "Replace Delay With Condition"),
        }

        for rel_path, phrases in expected.items():
            path = ROOT_DIR / "references" / rel_path
            text = path.read_text(encoding="utf-8")
            with self.subTest(reference=rel_path):
                self.assertTrue(path.exists())
                self.assertIn(f"`{rel_path}`", reference_map)
                self.assertIn(f"references/{rel_path}", debug_skill)
                for phrase in phrases:
                    self.assertIn(phrase, text)

    def test_design_lens_references_exist_and_do_not_revive_separate_stage_identity(self) -> None:
        architectural_lens = (ROOT_DIR / "references" / "design" / "architectural-lens.md").read_text(encoding="utf-8")
        visual_guidance = (ROOT_DIR / "references" / "design" / "visual-companion-guidance.md").read_text(encoding="utf-8")
        bootstrap_support = (ROOT_DIR / "scripts" / "workflow_state_bootstrap_support.py").read_text(encoding="utf-8")
        help_next = (ROOT_DIR / "references" / "help-next.md").read_text(encoding="utf-8")

        self.assertIn("design lens inside `forge-brainstorming`", architectural_lens)
        self.assertIn("visual lens inside `forge-brainstorming`", visual_guidance)
        self.assertNotIn('stage_name="architect"', bootstrap_support)
        self.assertIn('stage_name="plan"', bootstrap_support)
        self.assertNotIn("`plan`, `architect`", help_next)
        self.assertIn("architectural lens", help_next)

    def test_worktree_and_subagent_skills_cover_p1_safety_and_prompt_structure(self) -> None:
        worktrees = (ROOT_DIR / "skills" / "using-git-worktrees" / "SKILL.md").read_text(encoding="utf-8")
        parallel = (ROOT_DIR / "skills" / "dispatching-parallel-agents" / "SKILL.md").read_text(encoding="utf-8")
        subagents = (ROOT_DIR / "skills" / "subagent-driven-development" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("Gitignore Safety Check", worktrees)
        self.assertIn("git check-ignore", worktrees)
        self.assertIn("untracked work", worktrees)
        self.assertIn("Core Principle", worktrees)
        self.assertIn("Decision Flow", worktrees)
        self.assertIn("Directory Selection", worktrees)
        self.assertIn("Branch And Name Selection", worktrees)
        self.assertIn("Create And Enter The Worktree", worktrees)
        self.assertIn("Setup And Baseline", worktrees)
        self.assertIn("Handoff Packet", worktrees)
        self.assertIn("Cleanup Safety", worktrees)
        self.assertIn("baseline failure", worktrees)
        self.assertIn("Why Parallel Agents", parallel)
        self.assertIn("Decision Flow", parallel)
        self.assertIn("Independence Checklist", parallel)
        self.assertIn("Grouping Problem Domains", parallel)
        self.assertIn("Agent Prompt Structure", parallel)
        self.assertIn("While Agents Run", parallel)
        self.assertIn("Review And Integrate", parallel)
        self.assertIn("focused, self-contained, and specific about output", parallel)
        self.assertIn("forge-systematic-debugging", parallel)
        self.assertIn("Agent Prompt Structure", subagents)
        self.assertIn("Owned files or write scope", subagents)
        self.assertIn("Return format", subagents)
        self.assertIn("do not revert unrelated changes", subagents)
        self.assertIn("Why Subagents", subagents)
        self.assertIn("Process Flow", subagents)
        self.assertIn("Pipeline Selection", subagents)
        self.assertIn("Packet Template", subagents)
        self.assertIn("Model Or Capability Tier", subagents)
        self.assertIn("Review Order", subagents)
        self.assertIn("Spec compliance review always happens before quality review.", subagents)
        self.assertIn("Final Reviewer Handoff", subagents)
        self.assertIn("references/subagent-prompts/final-reviewer-prompt.md", subagents)

    def test_no_skill_mentions_route_preview(self) -> None:
        for skill_name, expected in FORGE_SPLIT_SKILLS.items():
            text = (ROOT_DIR / expected["path"]).read_text(encoding="utf-8").casefold()
            with self.subTest(skill=skill_name):
                self.assertNotIn("route_preview.py", text)
                self.assertNotIn("route preview", text)


if __name__ == "__main__":
    unittest.main()

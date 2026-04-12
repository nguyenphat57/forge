# Forge TDD/SDD Benchmark Report

Date: 2026-03-29
Workspace: `forge/`
Purpose: Benchmark three strong external repos on TDD and SDD, then extract what is genuinely useful for Forge.

## Inputs Reviewed
Installed into:
- `.tmp/spec-kit`
- `.tmp/superpowers`
- `.tmp/OpenSpec`

Pinned snapshots:
- `github/spec-kit` at `f8da535d715085d6bac06f0efe2fd4f07d221436`
- `obra/superpowers` at `eafe962b18f6c5dc70fb7c8cc7e83e61f4cdde06`
- `Fission-AI/OpenSpec` at `afdca0d5dab1aa109cfd8848b2512333ccad60c3`

Method:
- Read core README, workflow docs, templates, skill/process definitions, and test layout.
- Compared them against current Forge workflow, artifacts, routing, and verification model.
- Did not run upstream full test suites; this report is based on source review plus local installation and structural inspection.

## Executive Summary
Best overall fit for Forge:
1. `OpenSpec`
2. `Superpowers`
3. `Spec Kit`

Reason:
- `OpenSpec` is the best source for a practical brownfield artifact model that Forge can absorb without losing its identity.
- `Superpowers` is the best source for stronger execution discipline: strict TDD language, worktree hygiene, and per-task reviewer lanes.
- `Spec Kit` is the best source for specification quality control: clarification markers, constitution-driven gates, and checklist thinking.

Recommended strategy for Forge:
- Keep Forge's existing evidence-first and risk-gated core.
- Import OpenSpec's change-folder and verify-against-artifacts ideas.
- Import Superpowers' execution rigor, especially worktree baseline verification and sharper TDD packets.
- Import Spec Kit's clarification and checklist mechanisms selectively, without adopting its full ceremony.

Short verdict:
- Forge should not become a clone of any of the three.
- Forge should become a hybrid: `Forge gates + OpenSpec artifacts + Superpowers execution discipline + Spec Kit clarification/checklist rigor`.

## Current Forge Baseline
Forge already has meaningful strengths:
- Verification-first build and test workflows.
- A real `spec-review` gate for risky build work.
- Route-aware workflow composition.
- Change artifacts for medium and large work.
- Reviewer-style closure and quality-gate thinking.

Current gaps relative to the benchmark set:
- No first-class spec delta model per change.
- No dedicated `verify change against artifacts` workflow that checks completeness, correctness, and coherence.
- No constitution or project-principles artifact that systematically shapes planning.
- No structured clarification pass equivalent to a requirement quality gate.
- No strong worktree bootstrap with baseline test verification as a default behavior for risky work.
- Plan artifacts are less operational than Superpowers plans and less spec-centric than OpenSpec changes.
- Brownfield artifact loop exists, but it is still weaker than OpenSpec's `specs + changes + archive` model.

## Repo 1: Spec Kit
Overall read:
- Strongest on formal SDD scaffolding.
- Good on TDD ideology, but the biggest value is specification quality discipline, not runtime execution ergonomics.

Evidence:
- The workflow is explicit: `constitution -> specify -> plan -> tasks -> implement`.
- `README.md` makes project principles a first-class starting point before spec creation.
- `spec-driven.md` treats checklists as "unit tests for the specification".
- `spec-driven.md` encodes a constitution with non-negotiable test-first and integration-first rules.
- `plan-template.md` contains constitution gates and complexity tracking.
- `TESTING.md` requires manual command verification and command-to-surface impact mapping.

Useful for Forge:
- A lightweight repo-local constitution or principles file.
- Clarification markers instead of silent assumption filling.
- Spec checklists as a pre-plan or pre-spec-review quality gate.
- Simplicity, anti-abstraction, and contract-test gates in planning.
- Command-surface testing matrices for workflow and adapter changes.

Do not copy directly:
- Full lifecycle ceremony.
- Heavy scaffolding as the default for every repo.
- The weaker "tests only if explicitly requested" phrasing from its task template.

Fit:
- `SDD fit`: high
- `TDD fit`: medium

## Repo 2: Superpowers
Overall read:
- Strongest on TDD enforcement and execution mechanics.
- Less of a spec framework than Spec Kit, but better at turning a plan into disciplined implementation behavior.

Evidence:
- README describes a full workflow: brainstorm, worktree, plan, subagent-driven execution, TDD, code review, finish branch.
- `test-driven-development/SKILL.md` uses extremely hard anti-rationalization language around RED-GREEN-REFACTOR.
- `writing-plans/SKILL.md` forces bite-sized steps with explicit failing test, run-fail, implement, run-pass, commit.
- `subagent-driven-development/SKILL.md` enforces implementer -> spec-reviewer -> code-quality-reviewer loops.
- `using-git-worktrees/SKILL.md` verifies ignore rules, sets up isolated worktree, runs setup, and checks a clean baseline before starting.

Useful for Forge:
- Sharper anti-rationalization language in TDD and review docs.
- More operational plans: exact files, fail/pass commands, no placeholders.
- Worktree bootstrap plus baseline verification as a default helper for risky work.
- Explicit spec-compliance review before code-quality review.
- Fresh, task-scoped controller packets for subagents.

Do not copy directly:
- Universal "delete it and start over" rhetoric.
- Plans overloaded with full code for every step.
- Mandatory micro-step decomposition for every repo and task.
- Skill library packaging as Forge's main product identity.

Fit:
- `TDD fit`: very high
- `SDD fit`: medium-high

## Repo 3: OpenSpec
Overall read:
- Best practical source for an artifact-driven SDD system that remains brownfield-friendly.
- Less strict than Forge on hard evidence gates, but much stronger on change packaging and ongoing spec evolution.

Evidence:
- README positions the workflow as `proposal.md + specs + design.md + tasks.md`.
- `docs/concepts.md` separates `openspec/specs` as source of truth from `openspec/changes` as isolated deltas.
- `docs/concepts.md` explains why change folders matter: parallel work, reviewability, archive history.
- `docs/opsx.md` explains the new `OPSX` model as fluid, iterative, and schema/template-driven.
- `docs/commands.md` and `docs/workflows.md` define `/opsx:verify` across completeness, correctness, and coherence.
- The repo itself stores many real change folders and archived changes, which proves the model is not only theoretical.

Useful for Forge:
- Delta specs inside per-change folders.
- A dedicated `verify-change` workflow that checks completeness, correctness, and coherence.
- Archive that merges durable knowledge back into long-lived specs, not only `.brain`.
- Brownfield-friendly artifact editing without losing traceability.
- Schema/template customization later, after core artifact quality is stronger.

Do not copy directly:
- "No rigid phase gates" as a universal rule.
- Advisory-only verify.
- Overly permissive archive behavior.

Fit:
- `SDD fit`: very high
- `TDD fit`: medium

## Synthesis: What Forge Should Adopt
### High Priority
1. Add delta specs to Forge change artifacts.
   - Best source: OpenSpec
   - Why: closes the gap between "change packet" and "behavior source of truth"

2. Add `verify-change` or equivalent.
   - Best source: OpenSpec
   - Forge version should be stricter than OpenSpec and integrate with quality-gate
   - Dimensions: completeness, correctness, coherence, evidence strength

3. Add worktree bootstrap plus baseline verification helper.
   - Best source: Superpowers
   - Forge already recommends isolation; it now needs a canonical helper to perform it reliably

4. Upgrade TDD guidance from "principled" to "hard to rationalize away".
   - Best source: Superpowers
   - Add explicit anti-pattern examples and reset conditions

5. Add clarification and checklist artifacts for medium/risky work.
   - Best source: Spec Kit
   - Use this before `plan` or before `spec-review` when requirements are fuzzy

### Medium Priority
6. Add a repo-level principles/constitution artifact.
   - Best source: Spec Kit
   - Keep it lightweight and opt-in, not mandatory for every tiny repo

7. Improve plan artifacts so they are closer to execution packets.
   - Best source: Superpowers
   - Exact files, proof-before-progress, out-of-scope, reopen conditions, task granularity

8. Add spec merge-back on archive.
   - Best source: OpenSpec
   - Forge should update both `.brain` and long-lived change or domain specs

9. Add command-surface impact test guidance for workflow/tooling changes.
   - Best source: Spec Kit
   - Especially valuable for Forge operator scripts and host adapters

### Low Priority / Experimental
- Explore schema-driven artifact pipelines later.
- Do not adopt deep skill-library packaging as Forge's primary UX.

## What Forge Should Explicitly Avoid
Avoid from Spec Kit:
- Full heavyweight ceremony for all work
- Optional-testing phrasing in task generation
- Assuming every repo wants the same artifact footprint

Avoid from Superpowers:
- Absolutist TDD language as a universal default in every context
- Requiring micro-task decomposition even when it hurts momentum
- Overloading plans with full code blocks for every single step

Avoid from OpenSpec:
- Making verify advisory-only
- Making archive too permissive
- Removing hard gates from risky work in the name of fluidity

## Recommended Forge Direction
Target operating model:
- `OpenSpec-style artifact spine`
- `Superpowers-style execution discipline`
- `Spec Kit-style clarification and spec quality control`
- `Forge-style verification and risk gating`

Translated into Forge terms:
- Keep `plan`, `architect`, `spec-review`, `build`, `test`, `quality-gate`
- Strengthen the artifact layer underneath them
- Distinguish clearly between source-of-truth specs, per-change deltas, execution packets, and verification reports.

## Proposed Roadmap For Forge
### Slice 1: Stronger Change Artifact Model
Add to medium and large change artifacts:
- `proposal.md`
- `design.md`
- `tasks.md`
- `verification.md`
- `specs/`

Success condition:
- Forge can explain not only what changed, but what behavior delta is intended.

### Slice 2: Verify Against Artifacts
Add `forge verify-change` style behavior:
- completeness
- correctness
- coherence
- residual risk
- evidence summary

Success condition:
- Forge can compare code against plan/spec/design/tasks, not only against test output.

### Slice 3: Worktree + Baseline Helper
Add canonical setup:
- create isolated worktree
- verify ignore safety
- run setup
- run clean baseline checks

Success condition:
- risky work starts from a reproducible clean baseline.

### Slice 4: Clarification + Checklist
Add:
- clarification markers
- requirements checklist
- pre-plan or pre-spec-review requirement health pass

Success condition:
- medium/risky tasks reach `plan` with less ambiguity and fewer hidden assumptions.

## Final Recommendation
If Forge only borrows one thing now:
- borrow OpenSpec's change-folder plus artifact verification model

If Forge borrows two things now:
- add Superpowers' worktree bootstrap and stronger execution packets

If Forge borrows three things now:
- add Spec Kit's clarification/checklist layer before planning or spec-review

Net conclusion:
- `OpenSpec` gives Forge the best artifact model.
- `Superpowers` gives Forge the best execution rigor.
- `Spec Kit` gives Forge the best spec-quality discipline.

The best version of Forge is not the heaviest one.
It is the version where spec deltas are durable, execution packets are sharp, verification is multi-dimensional, and brownfield work remains practical.

# Checklist: Forge Solo-Dev Ready

Date: 2026-04-13
Status: current assessment against the shipped Forge contract

This checklist scores Forge in three states:

- `PASS`: usable now with repo-backed evidence
- `PARTIAL`: usable, but still missing maturity or breadth
- `MISSING`: not part of the current shipped line, or still too incomplete to claim

## A. Core End-To-End Contract

| Area | Status | Why |
|---|---|---|
| Route from intent to delivery | `PASS` | The current contract keeps an explicit solo chain through planning, build, verification, review, gate, and deploy. |
| Session continuity and resume | `PASS` | Canonical `workflow-state` is now the source of truth for `help`, `next`, `save`, and `resume`. |
| Proof before claims | `PASS` | Verification and gate posture are explicit, and deploy-sensitive work is blocked from soft approval paths. |
| Stable release and public readiness | `PASS` | Forge `2.3.1` is marked stable and public-ready under the current release policy. |

## B. Solo-Dev Product Ergonomics

| Area | Status | Why |
|---|---|---|
| Codex adapter maturity | `PARTIAL` | `forge-codex` ships in the stable release, but repo docs still describe `forge-antigravity` as the most mature adapter for real rollout. |
| First-party lanes and presets in the current shipped line | `MISSING` | The current roadmap is a kernel-only contraction; the shipped line is `forge-core`, `forge-codex`, and `forge-antigravity`, not a richer lane catalog. |
| Brownfield operator ergonomics | `MISSING` | Useful solo-dev surfaces such as `doctor`, `map-codebase`, and `dashboard` exist mainly in archived runtime-era history, not the current shipped contract. |
| Real-world shipping intelligence breadth | `PARTIAL` | Real canary and authenticated QA evidence exists, but the archived follow-up still says shipping intelligence is not yet tuned enough from live usage. |

## Current Verdict

If the target is:

- a process-first solo workflow that can route, persist state, verify, gate, and reach deploy with evidence, Forge is `PASS`.
- a fully productized solo-dev platform with strong onboarding, brownfield diagnosis, lane presets, and broad rollout maturity, Forge is `MISSING`.

The practical verdict is:

`Forge is end-to-end for solo-dev execution at the kernel/process layer, but not yet fully complete as a polished solo-dev product ecosystem.`

## Evidence Used For This Assessment

- `python scripts/verify_repo.py --profile fast`
- `python scripts/repo_operator.py resume --workspace <workspace> --format json`
- `python scripts/repo_operator.py help --workspace <workspace> --format json`
- `python scripts/repo_operator.py next --workspace <workspace> --format json`
- `python -m unittest discover -s packages/forge-core/tests -p test_route_preview.py -v`
- `python -m unittest discover -s packages/forge-core/tests -p test_help_next_workflow_state.py -v`
- `python -m unittest discover -s packages/forge-core/tests -p test_record_stage_state.py -v`
- `python -m unittest discover -s packages/forge-core/tests -p test_quality_gate.py -v`
- `python -m unittest discover -s packages/forge-core/tests -p test_run_workflow.py -v`

## Key Source Anchors

- `README.md`
- `CHANGELOG.md`
- `docs/release/public-readiness.md`
- `docs/release/release-process.md`
- `docs/plans/forge_refactor_V3.md`
- `docs/audits/2026-03-28-solo-dev-ecosystem-review.md`
- `docs/archive/history/2026-03-runtime-era/PROJECT_COMPATIBILITY_AND_CANARY_FOLLOWUP_2026-03-29.md`

# Solo-Dev Opinionated Profile Implementation Checklist

Date: 2026-03-31
Status: historical implementation checklist, superseded by shipped host surfaces and `docs/plans/2026-04-02-forge-1.15.x-maintenance-closure.md`
Inputs:
- `docs/specs/2026-03-31-solo-dev-opinionated-profile-spec.md`
- `docs/specs/2026-03-31-solo-dev-opinionated-profile-spec-appendix.md`
- `packages/forge-core/data/orchestrator-registry.json`
- `packages/forge-core/scripts/route_analysis.py`
- `packages/forge-core/scripts/route_risk.py`
- `packages/forge-core/scripts/route_process_requirements.py`
- `packages/forge-core/scripts/route_preview.py`

## Goal

Ship the `solo-internal` and `solo-public` operating model into `forge-core` as a real, testable routing and workflow-state contract, not as documentation-only guidance.

## Success Signals

- route resolution explicitly chooses `solo-internal` or `solo-public`
- route preview renders exact chain, required stages, activation reasons, and skip reasons
- `brainstorm` absorbs `discovery-lite` and escalates to `discovery-full` only when required
- `spec-review` triggers from risk or packet ambiguity, regardless of task size
- `visualize`, `review-pack`, `release-doc-sync`, and `release-readiness` are promoted into the correct happy paths
- workflow-state records stage status consistently as `pending/required/active/completed/skipped/blocked`
- quality and release gates read explicit stage state and artifacts instead of leaning on soft agent inference

## Baseline Verification

Run before the first code change:
```powershell
python -m pytest packages/forge-core/tests/test_route_preview.py packages/forge-core/tests/test_quality_gate.py packages/forge-core/tests/test_release_readiness.py packages/forge-core/tests/test_review_pack.py
```

If this baseline fails, stop and record the unrelated blocker before continuing.

## Sequencing Rules

- Keep commits narrow and independently reviewable.
- Do not mix routing-contract changes with workflow-state persistence in the same commit unless one is blocked on the other.
- Add or update tests in the same commit that changes behavior.
- Prefer making `solo-internal` correct first, then layering `solo-public` strictness where the contract differs.

## Commit 1: Add Profile And Stage Contract Scaffolding

Deliver:
- add `solo_profiles` contract to the registry
- add canonical `activation_reason` and `skip_reason` enums
- add stage status vocabulary for workflow-state consumers
- document the profile and stage contract in core docs where needed

Primary files:
- `packages/forge-core/data/orchestrator-registry.json`
- `packages/forge-core/SKILL.md`
- `packages/forge-core/tests/test_contracts.py`

Verify:
```powershell
python -m pytest packages/forge-core/tests/test_contracts.py
```
Exit:
- the registry can express profile-specific routing without changing behavior yet

## Commit 2: Resolve Profile And Required Stages In Routing

Deliver:
- resolve `solo-internal` vs `solo-public` in the route engine
- emit `required_stages` rather than only a flat skill list
- attach `activation_reason` or `skip_reason` to every stage decision
- keep existing routes stable where the new profile logic does not apply

Primary files:
- `packages/forge-core/scripts/route_analysis.py`
- `packages/forge-core/scripts/route_process_requirements.py`
- `packages/forge-core/scripts/route_preview.py`
- `packages/forge-core/tests/fixtures/route_preview_cases.json`
- `packages/forge-core/tests/test_route_preview.py`

Verify:
```powershell
python -m pytest packages/forge-core/tests/test_route_preview.py packages/forge-core/tests/test_router_matrix.py packages/forge-core/tests/test_route_matrix.py
```
Exit:
- route preview shows profile, required stages, activation reasons, and skip reasons

## Commit 3: Move Discovery Into Brainstorm

Deliver:
- update `brainstorm` to start with `discovery-lite`
- define the escalation rule from `discovery-lite` to `discovery-full`
- make `direction-locked` and `decision-blocked` the only valid end states
- update route risk logic so greenfield and ambiguous work reliably insert `brainstorm`

Primary files:
- `packages/forge-core/workflows/design/brainstorm.md`
- `packages/forge-core/scripts/route_risk.py`
- `packages/forge-core/tests/fixtures/route_preview_cases.json`
- `packages/forge-core/tests/test_route_preview.py`

Verify:
```powershell
python -m pytest packages/forge-core/tests/test_route_preview.py
```
Exit:
- new feature prompts and ambiguous prompts route through `brainstorm` with explicit discovery intent

## Commit 4: Convert Spec-Review Into A Risk Gate

Deliver:
- remove the assumption that `spec-review` is primarily size-based
- trigger `spec-review` for any size when boundary risk is present
- trigger `spec-review` when the packet is too unclear to implement safely
- update docs and route heuristics to match the new contract

Primary files:
- `packages/forge-core/workflows/design/spec-review.md`
- `packages/forge-core/scripts/route_risk.py`
- `packages/forge-core/scripts/route_process_requirements.py`
- `packages/forge-core/tests/fixtures/route_preview_cases.json`
- `packages/forge-core/tests/test_route_preview.py`
- `packages/forge-core/tests/test_check_spec_packet.py`

Verify:
```powershell
python -m pytest packages/forge-core/tests/test_route_preview.py packages/forge-core/tests/test_check_spec_packet.py
```
Exit:
- a `small` task with auth, schema, contract, or packet ambiguity can require `spec-review`

## Commit 5: Promote Visualize For UI Medium+

Deliver:
- make `visualize` a true UI stage for medium+ work instead of a rarely hit branch
- trigger `visualize` when interaction model changes even if the prompt sounds implementation-first
- preserve fast path for tiny, obvious UI patches

Primary files:
- `packages/forge-core/workflows/design/visualize.md`
- `packages/forge-core/workflows/design/plan.md`
- `packages/forge-core/domains/frontend.md`
- `packages/forge-core/scripts/route_analysis.py`
- `packages/forge-core/tests/fixtures/route_preview_cases.json`
- `packages/forge-core/tests/test_route_preview.py`

Verify:
```powershell
python -m pytest packages/forge-core/tests/test_route_preview.py
```
Exit:
- UI medium+ flows route `plan -> visualize -> ...` by default

## Commit 6: Add Solo Self-Review And Review-Pack Tail

Deliver:
- formalize `review` as `self-review` for solo-dev flows while preserving findings-first discipline
- require `review-pack` before deploy to shared internal environments and before real public releases
- make deploy-tail routing consistent across build, debug, and release-sensitive flows

Primary files:
- `packages/forge-core/workflows/execution/review.md`
- `packages/forge-core/workflows/execution/review-pack.md`
- `packages/forge-core/workflows/execution/deploy.md`
- `packages/forge-core/scripts/route_process_requirements.py`
- `packages/forge-core/scripts/route_preview.py`
- `packages/forge-core/tests/fixtures/route_preview_cases.json`
- `packages/forge-core/tests/test_route_preview.py`
- `packages/forge-core/tests/test_review_pack.py`

Verify:
```powershell
python -m pytest packages/forge-core/tests/test_route_preview.py packages/forge-core/tests/test_review_pack.py
```
Exit:
- deploy candidates show `review-pack` and `self-review` in the right order for the active profile

## Commit 7: Introduce Workflow-State Spine For Stage And Gate State

Deliver:
- define workflow-state structure for stage status and gate decisions
- add recorders for direction state and spec-review state
- make route and gate consumers read persisted stage state rather than relying on loose conventions

Primary files:
- `packages/forge-core/scripts/track_chain_status.py`
- `packages/forge-core/scripts/workflow_state_summary.py`
- `packages/forge-core/scripts/workflow_state_support.py`
- `packages/forge-core/scripts/record_direction_state.py`
- `packages/forge-core/scripts/record_spec_review_state.py`
- `packages/forge-core/tests/test_help_next_workflow_state.py`
- `packages/forge-core/tests/test_tool_roundtrip.py`

Verify:
```powershell
python -m pytest packages/forge-core/tests/test_help_next_workflow_state.py packages/forge-core/tests/test_tool_roundtrip.py
```
Exit:
- stage state can be persisted and later read without reconstructing intent from chat memory

## Commit 8: Align Quality-Gate And Verify-Change With Stage State

Deliver:
- make `quality-gate` consume required stage state before returning `go`
- keep `verify-change` state-gated: only required when a change artifact exists
- keep `change` recommended rather than mandatory, but make its presence affect verification rules

Primary files:
- `packages/forge-core/workflows/execution/change.md`
- `packages/forge-core/workflows/execution/verify-change.md`
- `packages/forge-core/workflows/execution/quality-gate.md`
- `packages/forge-core/scripts/quality_gate_artifacts.py`
- `packages/forge-core/scripts/verify_change.py`
- `packages/forge-core/tests/test_change_artifacts.py`
- `packages/forge-core/tests/test_verify_change.py`
- `packages/forge-core/tests/test_quality_gate.py`

Verify:
```powershell
python -m pytest packages/forge-core/tests/test_change_artifacts.py packages/forge-core/tests/test_verify_change.py packages/forge-core/tests/test_quality_gate.py
```
Exit:
- `quality-gate` no longer ignores missing required stages, and `verify-change` stays conditional on actual artifact state

## Commit 9: Add Release-Surface Gates By Profile

Deliver:
- require `release-doc-sync` on release-surface changes according to profile rules
- require `release-readiness` for public production and critical internal releases
- make release gates depend on explicit target classification instead of prompt vibes

Primary files:
- `packages/forge-core/workflows/execution/release-doc-sync.md`
- `packages/forge-core/workflows/execution/release-readiness.md`
- `packages/forge-core/scripts/release_doc_sync.py`
- `packages/forge-core/scripts/release_readiness.py`
- `packages/forge-core/scripts/route_process_requirements.py`
- `packages/forge-core/tests/test_release_doc_sync.py`
- `packages/forge-core/tests/test_release_readiness.py`
- `packages/forge-core/tests/fixtures/route_preview_cases.json`

Verify:
```powershell
python -m pytest packages/forge-core/tests/test_release_doc_sync.py packages/forge-core/tests/test_release_readiness.py packages/forge-core/tests/test_route_preview.py
```
Exit:
- release-sensitive flows are profile-aware and no longer leave docs/readiness gates outside the happy path

## Commit 10: Add Adoption Check And Finalize End-To-End Solo Chains

Deliver:
- add `adoption-check` workflow and state recorder
- wire it into `solo-internal` shared-env releases and `solo-public` releases
- finalize route fixtures for all canonical chains
- update core docs so the profile is described as an operating model, not a loose recommendation

Primary files:
- `packages/forge-core/workflows/execution/adoption-check.md`
- `packages/forge-core/scripts/record_adoption_check.py`
- `packages/forge-core/scripts/route_preview.py`
- `packages/forge-core/SKILL.md`
- `packages/forge-core/tests/fixtures/route_preview_cases.json`
- `packages/forge-core/tests/test_route_preview.py`

Verify:
```powershell
python -m pytest packages/forge-core/tests/test_route_preview.py packages/forge-core/tests/test_tool_roundtrip.py
```
Exit:
- both canonical chains are fully represented in docs, routing, fixtures, and workflow-state handling

## Final Verification Sweep

Run after Commit 10:
```powershell
python -m pytest packages/forge-core/tests/test_route_preview.py packages/forge-core/tests/test_quality_gate.py packages/forge-core/tests/test_release_doc_sync.py packages/forge-core/tests/test_release_readiness.py packages/forge-core/tests/test_review_pack.py packages/forge-core/tests/test_help_next_workflow_state.py packages/forge-core/tests/test_verify_change.py packages/forge-core/tests/test_change_artifacts.py packages/forge-core/tests/test_tool_roundtrip.py
```

Optional broader pass before merge:
```powershell
python -m pytest packages/forge-core/tests
```

## Definition Of Done

The implementation is done only when:

- profile resolution is explicit and persisted
- every required stage has an activation reason or a valid skip reason
- `brainstorm`, `spec-review`, `visualize`, `review-pack`, `release-doc-sync`, and `release-readiness` activate from rules instead of ad-hoc agent judgment
- workflow-state is sufficient for resume and gate decisions without reconstructing context from chat memory
- tests cover `small but risky`, `UI medium+`, `shared env internal`, and `public production` scenarios

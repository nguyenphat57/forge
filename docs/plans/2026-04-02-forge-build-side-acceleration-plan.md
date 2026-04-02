# Forge Build Throughput Plan

Date: 2026-04-02
Status: refocused candidate detailed plan
Inputs:
- `README.md`
- `packages/forge-core/SKILL.md`
- `packages/forge-core/references/target-state.md`
- `docs/architecture/adapter-boundary.md`
- `docs/plans/2026-04-01-forge-1.12.x-ideas.md`
- `packages/forge-core/scripts/route_preview.py`
- `packages/forge-core/scripts/route_delegation.py`
- `packages/forge-core/scripts/track_execution_progress.py`
- `packages/forge-core/scripts/track_chain_status.py`
- `packages/forge-core/scripts/workflow_state_summary.py`
- `packages/forge-core/scripts/help_next_support.py`
- `packages/forge-core/scripts/resolve_help_next.py`
- `packages/forge-codex/overlay/workflows/execution/dispatch-subagents.md`
- `packages/forge-core/tests/test_route_preview.py`
- `packages/forge-core/tests/test_help_next.py`
- `packages/forge-core/tests/test_tool_roundtrip.py`
- `packages/forge-core/tests/test_run_workflow.py`
- `tests/release_repo_test_overlays.py`
- `tests/test_release_hardening.py`

## Plan Role

- this document is a candidate build-throughput plan for the next roadmap line after `1.12.0`
- it does not automatically supersede the current `1.13+` runtime-trust backlog from `docs/plans/2026-04-01-forge-1.12.x-ideas.md`
- treat this as the detailed implementation packet to promote if Forge decides the next tranche should strengthen build throughput, packetized execution, and build-native verification instead of only extending runtime-trust work

## Qualified Problem Statement

For:
- a solo developer using Forge for medium and large implementation work across Codex, Antigravity, and future adapters

Who:
- already has a release-side operating model that is more mature than the current build-side acceleration surfaces

That:
- needs Forge to improve real build throughput without abandoning its process-first, evidence-first thesis

## Why This Exists

Forge is currently stronger on:
- release-tail clarity
- release-state visibility
- release verification density

Than on:
- packetized build control
- safe parallel build acceleration
- browser-backed build verification loops

This plan exists to raise the build side without turning Forge into:
- a host-specific agent swarm product
- a browser-first QA product
- a vanity dashboard product
- a speed-first coding system that drops proof and brownfield safety

## Strategic Goal

Make Forge visibly stronger at real build execution by upgrading three throughput-critical capability layers together:

1. `Build packet and observability contract`
2. `Subagent build loop`
3. `Browser QA as build accelerator`

Then refresh `public positioning` only after the new throughput capability is verified and coherent.

## Four-Layer Model

```text
build capabilities -> operator UX -> verification evidence -> public positioning
```

Rules:
- do not change public positioning before capability and evidence are real
- do not add host-native delegation primitives to `forge-core`
- do not let browser QA become mandatory for tasks that do not benefit from it
- do not put a dedicated dashboard on the critical path of throughput

## Success Signals

- large or risky build work can be split into explicit packets with ownership, scope, proof, and merge-back rules
- build-state becomes actionable through packet artifacts plus `help` or `next`, not just reconstructable from scattered notes
- Codex and future subagent-capable adapters can accelerate with parallel-safe dispatch, while Antigravity still follows the same core contract through sequential fallback
- browser-backed verification participates in the build loop as a targeted accelerator for UI or workflow-sensitive slices
- public Forge docs can claim stronger build throughput without overstating capabilities or weakening evidence standards

## Non-Goals

- do not introduce new release tiers, new release-tail stages, or analytics-style release telemetry
- do not make native subagents a required core capability
- do not add host breadth first as a substitute for improving the build loop itself
- do not convert `forge-browse` into a mandatory dependency for non-browser work
- do not ship percentage progress trackers, LOC counters, or vanity throughput metrics
- do not make a dedicated dashboard a required deliverable for the first build-throughput tranche
- do not let build acceleration reopen the `1.12.x` release model unless a regression is found

## Relationship To The Current `1.13+` Boundary

- the current deferred boundary in `packages/forge-core/references/target-state.md` still correctly identifies runtime-trust work such as installed-runtime doctor, rollout ledgers, canaries, and publish packets as valid `1.13+` work
- this build-throughput plan should be cut as either:
  - a parallel tranche beside runtime-trust work, if capacity allows
  - or a sequenced tranche immediately after the first runtime-trust slice lands
- if only one tranche can move next, choose based on which problem is causing more operator pain:
  - `post-install trust gap` -> runtime-trust first
  - `medium/large build throughput gap` -> build-side first

## Core Thesis Guardrails

This plan must preserve:
- process-first execution
- proof before claims
- brownfield safety
- host-neutral core orchestration

This plan must not change Forge into:
- a subagent-only platform
- a release-only platform
- a browser-first testing product
- a host-specific wrapper pack

## Scope In

- packetized build work for medium and large implementation slices
- build-state artifacts that improve resume, review, merge, and dispatch decisions
- host capability mapping for subagent-capable and non-subagent hosts
- browser-backed verification packets for UI and workflow-sensitive slices
- `help` or `next` improvements that consume build-state artifacts
- public messaging updates after the above behavior is verified

## Scope Out

- installed-runtime doctor and repair flows
- release-publish packets
- rollout ledger work
- broad extension marketplace design
- community plugin interfaces
- broad host expansion before the build loop contract is stable
- a dedicated build dashboard as a required first-wave deliverable

## Host Capability Matrix

| Host class | Example | Native subagents | Parallel implementers | Forge behavior |
|------------|---------|------------------|------------------------|----------------|
| `H0` | Antigravity today | no | no | same packet contract, sequential controller lanes, reviewer fallback only |
| `H1` | future limited host | yes | limited | separate reviewer or implementer lanes when safe, but no aggressive parallel split |
| `H2` | Codex today, future `forge-claude` target | yes | yes | `parallel-safe` packets can use `parallel-split` under explicit ownership and merge-back rules |

Rules:
- `forge-core` owns packet contract, lane semantics, and fallback policy
- adapters own native dispatch UX and host-specific wiring
- no adapter may weaken proof or ownership requirements just because the host can spawn subagents

## Build Packet Contract V1

Every medium or large build packet should answer:
- what is the exact slice goal
- what is the source of truth
- which files or paths are in scope
- who owns the write scope
- what proof already exists
- what proof must be rerun
- what blocks progress
- what reopens the packet after review or merge

Canonical packet fields should extend the current delegation and execution surfaces, not replace them:
- `packet_id`
- `parent_packet`
- `goal`
- `source_of_truth`
- `current_slice_or_review_question`
- `exact_files_or_paths_in_scope`
- `owned_files_or_write_scope`
- `depends_on_packets`
- `baseline_or_clean_start_proof`
- `red_proof`
- `proof_before_progress`
- `verification_to_rerun`
- `browser_qa_needed`
- `browser_qa_scope`
- `out_of_scope_for_this_slice`
- `reopen_conditions`
- `blockers`
- `residual_risk`

## Build-State Surface V1

The primary build-state surface in this tranche is not a dedicated dashboard.
It is the combination of:
- packet artifacts
- chain artifacts
- workflow-state summary
- `help` or `next`

Those surfaces should answer:
- what build chain is active
- which packets are active, blocked, review-ready, or merge-ready
- which lane currently owns each packet
- where write-scope overlap prevents parallelization
- what proof is missing before the next claim
- whether browser QA is pending, active, or satisfied for affected slices

An explicit build dashboard may be added later, but it is optional and must not be treated as the prerequisite for build throughput.

## Browser QA As Build Accelerator

Browser QA should be treated as:
- an execution-time verification actuator for browser-sensitive work
- a targeted accelerator for reproduce-fix-verify loops

It should not be treated as:
- a new release gate for every build
- a mandatory runtime dependency for all tasks
- a full product redesign pipeline

Use cases that qualify:
- UI regressions that are easier to reproduce in browser than through unit tests
- multi-step product flows where browser replay materially shortens debugging
- workflow-sensitive feature slices where screenshots, DOM assertions, or flow captures reduce back-and-forth

Use cases that do not qualify:
- pure backend refactors
- low-risk docs work
- straightforward CLI behavior changes with better local harnesses already available

## Implementation Strategy

Do the work in this order:

1. `build packet + observability contract`
2. `subagent build loop`
3. `browser QA accelerator`
4. `help/next build-state support`
5. `public positioning refresh`
6. `optional dedicated dashboard only if still justified`

Reason:
- subagent execution without packet observability becomes chaos
- browser QA without packet integration becomes an optional sidecar, not a build accelerator
- `help` or `next` is enough for the first throughput tranche; a dedicated dashboard can wait
- public narrative before evidence becomes marketing

## Baseline

Run before the first implementation slice:

```powershell
python -m pytest packages/forge-core/tests/test_route_preview.py packages/forge-core/tests/test_help_next.py packages/forge-core/tests/test_tool_roundtrip.py packages/forge-core/tests/test_run_workflow.py tests/test_release_hardening.py -q
```

This baseline is intentionally behavior-heavy:
- route and delegation logic
- operator guidance
- round-trip workflow state
- runtime-tool hardening

## File Or Surface Map

- `packages/forge-core/scripts/route_preview.py`
- `packages/forge-core/scripts/route_delegation.py`
- `packages/forge-core/scripts/track_execution_progress.py`
- `packages/forge-core/scripts/track_chain_status.py`
- `packages/forge-core/scripts/workflow_state_summary.py`
- `packages/forge-core/scripts/workflow_state_support.py`
- `packages/forge-core/scripts/help_next_support.py`
- `packages/forge-core/scripts/resolve_help_next.py`
- `packages/forge-core/scripts/invoke_runtime_tool.py`
- `packages/forge-core/scripts/resolve_runtime_tool.py`
- `packages/forge-core/workflows/operator/help.md`
- `packages/forge-core/workflows/operator/next.md`
- `packages/forge-core/workflows/execution/build.md`
- `packages/forge-core/workflows/execution/test.md`
- `packages/forge-core/workflows/execution/debug.md`
- `packages/forge-codex/overlay/workflows/execution/dispatch-subagents.md`
- `packages/forge-core/tests/test_route_preview.py`
- `packages/forge-core/tests/test_tool_roundtrip.py`
- `packages/forge-core/tests/test_help_next.py`
- `packages/forge-core/tests/test_run_workflow.py`
- `packages/forge-core/tests/test_contracts.py`
- `tests/release_repo_test_overlays.py`
- `tests/test_release_hardening.py`
- `README.md`
- `packages/forge-core/references/target-state.md`

## Workstream A: Build Packet And Observability Contract

### A1. Promote Execution Progress From Checkpoint Log To Packet State

Deliver:
- add packet identity and packet dependency fields to `track_execution_progress.py`
- persist packet ownership, merge readiness, browser-QA need, and proof state
- keep the current proof-before-progress bar intact

Primary files:
- `packages/forge-core/scripts/track_execution_progress.py`
- `packages/forge-core/scripts/workflow_state_support.py`
- `packages/forge-core/tests/test_tool_roundtrip.py`
- `packages/forge-core/tests/test_run_workflow.py`

Verify:
```powershell
python -m pytest packages/forge-core/tests/test_tool_roundtrip.py packages/forge-core/tests/test_run_workflow.py -q
```

Exit:
- execution progress artifacts can represent real build packets instead of only linear checkpoints

### A2. Promote Chain Status Into A Build Controller Surface

Deliver:
- teach `track_chain_status.py` to represent active packets, blocked packets, and merge points
- distinguish packet-level blockers from chain-level blockers
- record when a chain is sequential by design versus sequential because host capability is limited

Primary files:
- `packages/forge-core/scripts/track_chain_status.py`
- `packages/forge-core/scripts/workflow_state_summary.py`
- `packages/forge-core/tests/test_help_next.py`

Verify:
```powershell
python -m pytest packages/forge-core/tests/test_help_next.py packages/forge-core/tests/test_tool_roundtrip.py -q
```

Exit:
- Forge can summarize build chains as controller-visible state rather than scattered artifacts

### A3. Add Build-State Summary Rules For Help And Next

Deliver:
- make `workflow_state_summary.py` summarize packetized execution, not only route previews and release-tail artifacts
- expose build-specific summary fields such as `active_packets`, `blocked_packets`, `next_merge_point`, and `browser_qa_pending`

Primary files:
- `packages/forge-core/scripts/workflow_state_summary.py`
- `packages/forge-core/scripts/help_next_support.py`
- `packages/forge-core/tests/test_help_next.py`
- `packages/forge-core/tests/test_tool_roundtrip.py`

Verify:
```powershell
python -m pytest packages/forge-core/tests/test_help_next.py packages/forge-core/tests/test_tool_roundtrip.py -q
```

Exit:
- build-state becomes first-class summary material, not an incidental artifact

## Workstream B: Subagent Build Loop

### B1. Freeze The Host-Neutral Build Loop Contract

Deliver:
- keep `route_delegation.py` as the canonical packet template and dispatch contract source
- refine it so `parallel-split`, `independent-reviewer`, and `controller-sequential` all share one contract
- add explicit fields for:
  - `packet_id`
  - `depends_on_packets`
  - `owned_files_or_write_scope`
  - `verification_to_rerun`
  - `browser_qa_needed`

Primary files:
- `packages/forge-core/scripts/route_delegation.py`
- `packages/forge-core/scripts/route_preview.py`
- `packages/forge-core/tests/test_route_preview.py`

Verify:
```powershell
python -m pytest packages/forge-core/tests/test_route_preview.py -q
```

Exit:
- host-neutral build-loop rules are explicit before any adapter-level acceleration is widened

### B2. Strengthen Host Capability Mapping

Deliver:
- represent host support for:
  - no subagents
  - reviewer-only subagents
  - parallel subagents
- keep Antigravity on the same packet contract with sequential fallback
- keep Codex on adapter-native dispatch
- leave room for a future `forge-claude` without rewriting the core story

Primary files:
- `packages/forge-core/data/orchestrator-registry.json`
- `packages/forge-core/scripts/route_preview.py`
- `packages/forge-core/tests/test_route_preview.py`
- `packages/forge-core/tests/test_contracts.py`

Verify:
```powershell
python -m pytest packages/forge-core/tests/test_route_preview.py packages/forge-core/tests/test_contracts.py -q
```

Exit:
- host differences affect dispatch mode, not the core build-loop semantics

### B3. Tighten Codex Dispatch UX Around The Same Contract

Deliver:
- keep `dispatch-subagents.md` as a Codex adapter wrapper, not a second source of truth
- update the adapter wrapper to consume the stronger packet contract and build-state language
- document the sequential fallback rule so the same packet logic still makes sense on Antigravity

Primary files:
- `packages/forge-codex/overlay/workflows/execution/dispatch-subagents.md`
- `tests/release_repo_test_overlays.py`

Verify:
```powershell
python -m pytest tests/release_repo_test_overlays.py packages/forge-core/tests/test_route_preview.py -q
```

Exit:
- Codex-native acceleration is stronger without pulling host-native delegation into core

## Workstream C: Browser QA As Build Accelerator

### C1. Define Browser-QA Eligibility In Build Packets

Deliver:
- add a minimal browser-QA classification step to build packets
- classify slices as:
  - `not-needed`
  - `optional-accelerator`
  - `required-for-this-packet`
- base the decision on task shape, not on runtime-tool availability alone

Primary files:
- `packages/forge-core/scripts/route_execution_advice.py`
- `packages/forge-core/scripts/track_execution_progress.py`
- `packages/forge-core/tests/test_route_preview.py`
- `packages/forge-core/tests/test_tool_roundtrip.py`

Verify:
```powershell
python -m pytest packages/forge-core/tests/test_route_preview.py packages/forge-core/tests/test_tool_roundtrip.py -q
```

Exit:
- browser QA becomes a packet-level execution decision instead of an ad hoc afterthought

### C2. Surface Browser-QA State In Help And Next

Deliver:
- teach `help` and `next` to say when browser QA is the next shortest proof path
- show browser-QA pending versus completed state only when it materially affects the packet

Primary files:
- `packages/forge-core/scripts/help_next_support.py`
- `packages/forge-core/workflows/operator/help.md`
- `packages/forge-core/workflows/operator/next.md`
- `packages/forge-core/tests/test_help_next.py`
- `packages/forge-core/tests/test_tool_roundtrip.py`

Verify:
```powershell
python -m pytest packages/forge-core/tests/test_help_next.py packages/forge-core/tests/test_tool_roundtrip.py -q
```

Exit:
- browser QA improves the operator decision loop instead of hiding as a detached runtime tool

### C3. Bind Browser Evidence Back Into Build-State

Deliver:
- route browser-backed proof into the same execution packet or workflow-state summary instead of leaving it in isolated runtime logs
- record the latest browser proof path and result so review and merge decisions can consume it

Primary files:
- `packages/forge-core/scripts/invoke_runtime_tool.py`
- `packages/forge-core/scripts/workflow_state_summary.py`
- `packages/forge-core/scripts/help_next_support.py`
- `packages/forge-core/tests/test_help_next.py`
- `tests/test_release_hardening.py`

Verify:
```powershell
python -m pytest packages/forge-core/tests/test_help_next.py tests/test_release_hardening.py -q
```

Exit:
- browser proof can influence build decisions through the same artifact story as other build evidence

## Workstream D: Operator Resumption Support

### D1. Teach Help And Next To Resume Build Packets

Deliver:
- make `help` and `next` prefer packet resumption, proof completion, or safe merge-back advice when build-state exists
- avoid generic `continue coding` guidance when the packet state already identifies the next constrained move

Primary files:
- `packages/forge-core/scripts/help_next_support.py`
- `packages/forge-core/scripts/resolve_help_next.py`
- `packages/forge-core/tests/test_help_next.py`

Verify:
```powershell
python -m pytest packages/forge-core/tests/test_help_next.py -q
```

Exit:
- build-side operator UX feels state-first the way release-side UX now does

### D2. Optional Dedicated Dashboard, Only If Still Needed

Deliver:
- do not start this slice unless packets, subagent loop, browser QA, and `help` or `next` are already strong enough that the missing piece is genuinely a glanceable summary surface
- if it is still needed, keep the dashboard thin and reuse the same packet and workflow-state artifacts instead of inventing new telemetry

Primary files:
- `packages/forge-core/scripts/dashboard_support.py`
- `packages/forge-core/scripts/dashboard.py`
- `packages/forge-core/workflows/operator/dashboard.md`
- `packages/forge-core/tests/test_dashboard.py`

Verify:
```powershell
python -m pytest packages/forge-core/tests/test_dashboard.py -q
```

Exit:
- a dashboard remains a thin optional view over packet state rather than a prerequisite for build throughput

## Workstream E: Public Positioning

### E1. Evidence-First Positioning Refresh

Deliver:
- update public Forge messaging only after Workstreams A to D1 are green
- shift the story from:
  - `Forge is mainly release-credible`
- toward:
  - `Forge is a process-first execution system that now accelerates real build work without dropping proof and safety`

Primary files:
- `README.md`
- relevant release or architecture references if needed

Verify:
```powershell
@'
from pathlib import Path

readme = Path("README.md").read_text(encoding="utf-8")
required = [
    "process-first orchestration system",
    "planning, build, review, debug, and release work",
]
for token in required:
    if token not in readme:
        raise SystemExit(f"Missing public-positioning token: {token}")
print("PASS: README still anchors Forge as a process-first system instead of a release-only system.")
'@ | python -
```

Exit:
- public positioning reflects verified capability rather than wishful differentiation

## Phase Order

### Phase 1: Build Packet Foundation

- A1
- A2
- A3

Cut goal:
- build-state artifacts become coherent enough that later dispatch and browser work can attach to them

### Phase 2: Subagent Build Loop

- B1
- B2
- B3

Cut goal:
- Codex and future H2 hosts can accelerate safely, while Antigravity remains aligned through fallback

### Phase 3: Browser QA Accelerator

- C1
- C2
- C3

Cut goal:
- browser-backed verification shortens qualifying build loops instead of living outside them

### Phase 4: Operator Resumption Support

- D1

Cut goal:
- `help` and `next` can drive build decisions with packet-level confidence instead of generic stage narration

### Phase 5: Public Positioning

- E1

Cut goal:
- public story matches the new build-side reality without overclaiming

### Phase 6: Optional Dedicated Dashboard

- D2

Cut goal:
- a dedicated dashboard is only added if the first five phases still leave a real visibility gap

## Cut Strategy

1. `build-packets-alpha`
   After Phase 1 if packet state and build summaries become trustworthy
2. `subagent-build-beta`
   After Phase 2 if Codex acceleration and Antigravity fallback both remain coherent
3. `browser-build-beta`
   After Phase 3 if browser QA evidence feeds the same packet and help or next surfaces
4. `build-side-positioning-cut`
   After Phases 4 and 5 once operator UX and public docs match the verified capability
5. `optional-build-dashboard`
   Only after Phase 6 if a dedicated dashboard is still justified by operator pain

## Final Verification Strategy

Baseline and final sweep should use the same family of checks:

```powershell
python -m pytest packages/forge-core/tests/test_route_preview.py packages/forge-core/tests/test_help_next.py packages/forge-core/tests/test_tool_roundtrip.py packages/forge-core/tests/test_run_workflow.py packages/forge-core/tests/test_contracts.py tests/release_repo_test_overlays.py tests/test_release_hardening.py -q
```

Only if the optional dashboard slice is actually implemented, extend the sweep with:

```powershell
python -m pytest packages/forge-core/tests/test_dashboard.py -q
```

Docs-only positioning changes should also run:

```powershell
git diff --check
@'
from pathlib import Path

readme = Path("README.md").read_text(encoding="utf-8")
if "process-first orchestration system" not in readme:
    raise SystemExit("README drifted away from the process-first thesis.")
print("PASS: public positioning keeps the process-first thesis visible.")
'@ | python -
```

## Risks And Mitigations

- Risk: subagent acceleration becomes Codex-specific and leaks host-specific assumptions into core
  Mitigation: keep packet contract and fallback policy in core; keep spawn UX in adapters only
- Risk: build-state observability turns into noisy telemetry
  Mitigation: forbid percentages, LOC counts, and vanity counters; only keep fields that change review, merge, or dispatch decisions
- Risk: browser QA spreads into tasks where it adds friction
  Mitigation: gate it with packet-level eligibility and keep it optional except where the packet explicitly needs it
- Risk: the plan drifts toward visibility work instead of throughput work
  Mitigation: keep a dedicated dashboard out of the critical path and require every early slice to show a direct throughput, merge, or review benefit
- Risk: public positioning gets refreshed before build-side evidence is mature
  Mitigation: make README and positioning refresh the last core phase, not the first
- Risk: runtime-trust work and build-side work compete for the same slice and both stall
  Mitigation: choose the next tranche explicitly instead of mixing the two themes under one vague `1.13+` umbrella

## Promotion Rule

Promote this plan into a committed roadmap only if:
- Forge explicitly chooses build-throughput acceleration as a first-class next-line theme
- the chosen tranche does not quietly abandon runtime-trust work without a conscious tradeoff
- the promotion packet names one clear baseline, one clear cut order, and one clear fallback for hosts without native subagents

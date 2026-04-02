# Host-Aware Delegation Preference Spec
Created: 2026-04-02 | Status: Proposed
Inputs:
- host capability findings from `packages/forge-core/data/orchestrator-registry.json`
- adapter overlays in `packages/forge-codex/overlay/data/orchestrator-registry.json`
- adapter overlays in `packages/forge-antigravity/overlay/data/orchestrator-registry.json`
- preference and delegation resolution in `packages/forge-core/scripts/preferences_contract.py`, `packages/forge-core/scripts/resolve_preferences.py`, and `packages/forge-core/scripts/route_delegation.py`

## Purpose

Make delegation behave automatically on every new thread without breaking hosts that do not support native subagents.

The desired user experience is:

- Forge restores delegation policy at thread bootstrap.
- Forge spawns subagents automatically when the host supports them and the task is a safe fit.
- Forge does not pretend unsupported hosts can delegate.
- The same preference model works across Codex, future Claude Code support, and Antigravity.

## Problem

Current behavior has two architectural flaws:

1. Delegation intent is being expressed through `custom_rules` in adapter extra preferences.
2. `forge-core` hard-codes `host_capabilities.active_tier = controller-baseline`, so host overlays that only flip `supports_subagents` booleans are still resolved as non-delegating.

This creates three bad outcomes:

- Thread bootstrap restores wording about delegation, but not an actionable runtime policy.
- Codex can support delegation but is silently downgraded to sequential lanes.
- Antigravity currently advertises partial subagent capability in a way that becomes internally inconsistent once core stops forcing baseline behavior.

## Goals

- Restore delegation policy automatically at the start of every new thread.
- Separate user preference from host capability.
- Keep `forge-core` host-neutral.
- Let Codex enable automatic delegation safely.
- Let unsupported hosts such as Antigravity fall back cleanly to sequential packetized lanes.
- Keep the current Forge safety gates around write-scope overlap, packet quality, and review independence.

## Non-Goals

- Do not force a subagent spawn on every task.
- Do not let user preference override real host limitations.
- Do not fork delegation logic per host.
- Do not encode runtime delegation control inside `custom_rules`.
- Do not require a workspace-local router for delegation to work.

## Design Principles

- Capability first: a host cannot do what its runtime does not expose.
- Preference second: user preference narrows or enables delegation within host limits.
- Task gate third: even when capability and preference allow delegation, Forge still needs a safe task shape before spawning.
- Bootstrap always restores policy; execution only happens when justified.

## Proposed Model

### 1. Host Capability Contract

`forge-core` remains the canonical owner of the delegation tier model:

- `controller-baseline`
- `review-lane-subagents`
- `parallel-workers`

But `forge-core` must stop treating `controller-baseline` as the globally active runtime for every host.

Replace the current meaning of the core registry keys with this split:

- `default_tier`: core fallback when no host overlay or runtime detection provides an active tier
- `active_tier`: adapter or runtime-selected tier for the current host

Core default:

- `default_tier = controller-baseline`
- no hard-coded host-specific `active_tier`

Resolution rule:

1. Use runtime-provided `active_tier` when present.
2. Else use merged-registry `active_tier` when present.
3. Else use merged-registry `default_tier`.
4. If no tier is available, infer from `supports_subagents` and `supports_parallel_subagents` as the last fallback.

Overlay precedence must be explicit:

- overlay `active_tier` always overrides core `active_tier` during registry merge
- this follows the existing deep-merge behavior where overlay scalar values replace core scalar values
- `route_delegation.py` reads only the already-merged `host_capabilities` payload and must not try to reconstruct source precedence at runtime

This keeps `forge-core` neutral while letting adapters declare real capability.

### 2. Typed Delegation Preference

Add a typed extra preference instead of relying on free-text `custom_rules`.

New adapter-global extra field:

`delegation_preference`

Allowed values:

- `off`
- `auto`
- `review-lanes`
- `parallel-workers`

Meaning:

- `off`: never spawn subagents, even if the host supports them.
- `auto`: use the strongest safe delegation mode the host supports for the routed task.
- `review-lanes`: allow only reviewer-lane delegation, never parallel worker splits.
- `parallel-workers`: allow full parallel delegation when the host and task both permit it.

Default behavior:

- if unset, resolve as `auto`
- if the user customizes delegation durably, the preference is restored at every new thread bootstrap

Default rationale:

- the patch goal is automatic delegation on capable hosts at every new thread
- `unset = auto` keeps unsupported hosts safe because effective mode is still capped by host capability
- `off` remains an explicit user override, not the fallback default

Persistence and authority:

- `delegation_preference` lives in `state/extra_preferences.json`, not in canonical `preferences.json`
- `output_contract` must not carry delegation control because it is reserved for prose and output-shaping policy
- bootstrap and routing must read the typed preference from resolved extra preferences, not from `custom_rules`

### 3. Thread Bootstrap Rule

At the start of every new thread, Forge already restores preferences before the first substantive reply. Extend that bootstrap to compute delegation readiness as part of the same restore step.

Bootstrap contract:

- `resolve_preferences.py --format json` remains the canonical bootstrap payload
- bootstrap reads `payload["extra"]["delegation_preference"]`
- bootstrap does not read `output_contract` for delegation state
- `route_preview.build_report()` must expose the derived runtime fields:
  - `detected.resolved_delegation_preference`
  - `detected.effective_delegation_mode`

Consumer contract:

- thread bootstrap uses `resolve_preferences.py` JSON output
- routing and delegation logic use the same resolved extra preference through `load_preferences(...)`
- `route_preview.py` is the canonical verification surface for the derived runtime outcome

This does not spawn anything by itself. It only restores the policy automatically so the thread begins with the correct behavior contract.

### 4. Effective Delegation Resolution

Forge should compute:

`effective_delegation_mode = min(host_capability_tier, delegation_preference)`

Equivalent behavior table:

| Host capability | User preference | Effective mode |
| --- | --- | --- |
| `controller-baseline` | any value | `controller-baseline` |
| `review-lane-subagents` | `off` | `controller-baseline` |
| `review-lane-subagents` | `auto` | `review-lane-subagents` |
| `review-lane-subagents` | `review-lanes` | `review-lane-subagents` |
| `review-lane-subagents` | `parallel-workers` | `review-lane-subagents` |
| `parallel-workers` | `off` | `controller-baseline` |
| `parallel-workers` | `auto` | `parallel-workers` |
| `parallel-workers` | `review-lanes` | `review-lane-subagents` |
| `parallel-workers` | `parallel-workers` | `parallel-workers` |

This ensures user intent can only reduce or shape behavior, never exceed host reality.

### 5. Task Gate Before Spawn

Even when effective mode allows delegation, Forge only spawns subagents if the routed task qualifies.

Spawn remains allowed only when:

- task intent is eligible for delegation
- execution mode or pipeline calls for delegation
- packet boundaries are explicit
- write scopes are non-overlapping
- review independence can be preserved

Required outcomes:

- `parallel-workers` may activate `parallel-split`
- `review-lane-subagents` may activate `independent-reviewer`
- all other cases degrade to `sequential-lanes`

This preserves the current safety contract in `dispatch-subagents.md`.

## Host-Specific Expectations

### Codex

Codex overlay should explicitly set:

- `active_tier = parallel-workers`
- `supports_subagents = true`
- `supports_parallel_subagents = true`
- `subagent_dispatch_skill = dispatch-subagents`

Result:

- every new thread restores delegation policy automatically
- `auto` preference allows real subagent use when the task is suitable

### Claude Code

Claude Code should use the same contract when a Forge adapter exists for that host.

If Claude Code supports parallel workers:

- `active_tier = parallel-workers`

If Claude Code supports only review-lane delegation:

- `active_tier = review-lane-subagents`

No Claude-specific fork in core logic is needed.

### Antigravity

Antigravity overlay should explicitly set:

- `active_tier = controller-baseline`
- `supports_subagents = false`
- `supports_parallel_subagents = false`
- `subagent_dispatch_skill = null`

Result:

- every new thread still restores delegation preference
- effective mode resolves to sequential execution
- Forge keeps packet boundaries and review discipline without pretending the host can spawn subagents

Capability correction note:

- the current Antigravity overlay advertises `supports_subagents = true` while also leaving `subagent_dispatch_skill = null`
- that state is internally inconsistent once core stops hard-forcing `controller-baseline`
- this patch intentionally corrects Antigravity to non-subagent capability and must be called out in release notes as a capability declaration fix

## Backward Compatibility

Existing `custom_rules` delegation text may continue to exist as prose, but it must become non-authoritative.

Mandatory compatibility rule for 1.14.x:

- if `delegation_preference` is absent and `custom_rules` contains a known legacy Forge-managed delegation marker, resolve `delegation_preference = auto` at read time
- emit a deprecation warning such as `legacy_delegation_rule_detected`
- do not attempt open-ended NLP or locale guessing over arbitrary user prose; only recognize a bounded allowlist of legacy markers emitted by prior Forge-managed customization flows
- `write_preferences.py --apply` must persist `delegation_preference` into `extra_preferences.json` on the next managed write
- new customization flows must stop writing delegation control into `custom_rules`

This keeps compatibility bounded without letting free-text prose remain the control plane.

Deprecation timeline:

- `1.14.x`: introduce `delegation_preference`, read-time compatibility, and deprecation warnings
- `1.15.x`: keep legacy markers non-authoritative, stop generating them in managed flows, and document the correction in release notes
- arbitrary user-authored prose in `custom_rules` remains untouched unless it matches a known Forge-managed legacy marker that the apply flow owns

## Implementation-Ready Packet

Implementation-ready:

- Sources:
  - `docs/specs/2026-04-02-host-aware-delegation-preference-spec.md`
  - `packages/forge-core/scripts/skill_routing.py`
  - `packages/forge-core/scripts/route_delegation.py`
  - `packages/forge-core/scripts/route_preview.py`
  - `packages/forge-core/scripts/resolve_preferences.py`
  - `packages/forge-core/scripts/preferences_store.py`
- First slice:
  - host capability correction only
  - replace core hard-coded `active_tier` with `default_tier`
  - set explicit `active_tier` in Codex and Antigravity overlays
  - update delegation resolution to trust merged `active_tier`
  - prove Codex resolves to `parallel-workers` and Antigravity resolves to `controller-baseline`
- Second slice:
  - add `delegation_preference` persistence and resolution
  - add legacy compatibility warning and managed-write migration
  - expose `resolved_delegation_preference` and `effective_delegation_mode` in route preview output
- Third slice:
  - ship release-note wording for Antigravity capability correction
  - ship deprecation wording for legacy delegation markers in `custom_rules`
- Proof before progress:
  - extend the existing focused route-preview tests first so the host-capability matrix fails before code changes
  - extend preference script/write tests so `delegation_preference` round-trip and legacy warning behavior fail before persistence changes land
  - do not start migration cleanup until the capability-resolution tests pass against merged bundle data
- Reopen only if:
  - generated host artifacts cannot carry overlay `active_tier` into merged bundle registry
  - bootstrap cannot consume `extra.delegation_preference` without reusing `output_contract`
  - the bounded allowlist for legacy delegation markers cannot cover the known Forge-managed variants safely

## Repo Slices

Expected implementation slices:

- `packages/forge-core/data/orchestrator-registry.json`
  - replace hard-coded core `active_tier` with `default_tier`
- `packages/forge-core/scripts/route_delegation.py`
  - resolve effective tier using runtime or merged-registry `active_tier` before core fallback
  - combine host capability with `delegation_preference`
- `packages/forge-core/scripts/route_preview.py`
  - expose `resolved_delegation_preference` and `effective_delegation_mode` in preview output
- `packages/forge-core/scripts/resolve_preferences.py`
  - keep `extra.delegation_preference` as the canonical bootstrap field
  - emit deprecation warning when a known legacy delegation marker is mapped
- `packages/forge-core/scripts/preferences_contract.py`
  - keep delegation control out of `output_contract`
- `packages/forge-core/scripts/preferences_store.py`
  - persist and round-trip `delegation_preference` as an extra field
- `packages/forge-codex/overlay/data/orchestrator-registry.json`
  - declare `active_tier = parallel-workers`
- `packages/forge-antigravity/overlay/data/orchestrator-registry.json`
  - declare `active_tier = controller-baseline`
  - correct the current inconsistent `supports_subagents = true` declaration
- `packages/forge-core/tests/test_route_preview.py`
  - extend focused host-capability and preference-driven delegation tests
- `packages/forge-core/tests/test_route_matrix.py`
  - extend smoke-matrix assertions for `resolved_delegation_preference` and effective mode
- `packages/forge-core/tests/fixtures/route_preview_cases.json`
  - add fixture cases for Codex, Antigravity, and preference combinations using the existing route-preview convention
- `packages/forge-core/tests/preferences_test_scripts.py`
  - verify `resolve_preferences.py` returns `extra.delegation_preference` and deprecation warnings
- `packages/forge-core/tests/test_write_preferences.py`
  - verify managed writes persist `delegation_preference` into split extra state
- `packages/forge-core/tests/test_contracts.py`
  - assert host-capability contract remains internally consistent after overlay merge

If a Claude Code adapter is added later, it should only need overlay-level capability wiring plus adapter tests.

## Verification Plan

Docs verification:

- spec file exists at `docs/specs/2026-04-02-host-aware-delegation-preference-spec.md`
- content names goals, non-goals, host matrix, resolution rules, repo slices, and verification requirements

Implementation verification that this spec expects:

1. Merged Codex registry reports `host_capability_tier = parallel-workers` before any preference-specific assertions run.
2. Merged Antigravity registry reports `host_capability_tier = controller-baseline` and no dispatch skill activation.
3. Route preview on Codex with `delegation_preference = auto` and a `parallel-safe` BUILD task returns `parallel-split`.
4. Route preview on Codex with `delegation_preference = review-lanes` and a review-lane pipeline returns `independent-reviewer`.
5. Route preview on Antigravity with any non-`off` preference still returns `sequential-lanes`.
6. `resolve_preferences.py --format json` returns `extra.delegation_preference` and a deprecation warning when a known legacy marker is present.
7. Managed preference writes persist `delegation_preference` in `extra_preferences.json`.
8. Thread bootstrap reads delegation preference from resolved extra preferences, not from `output_contract` and not from `custom_rules`.

## Risks

- If core and overlay tier semantics both remain active, capability resolution will stay ambiguous.
- If delegation preference is added only to prose output but not to routing inputs, the patch will repeat the current failure mode.
- If Antigravity continues to advertise partial subagent capability without an explicit active tier, route previews will remain misleading.
- If `unset = auto` is not documented clearly in release notes, users may misread the change as an unannounced regression rather than the intended default.

## Exit Criteria

- Delegation policy is restored automatically on every new thread.
- Codex can delegate automatically when safe.
- Unsupported hosts fall back cleanly without fake delegation claims.
- `custom_rules` is no longer the control plane for delegation behavior.
- Host enablement requires only adapter capability wiring, not a fork of Forge core delegation logic.

## Bottom Line

The correct fix is not "always spawn subagents". The correct fix is:

- restore delegation preference automatically at thread bootstrap
- resolve it against real host capability
- allow spawning only when the routed task is safe to split

That gives Codex and future Claude Code support the intended automation, while keeping Antigravity truthful and stable.

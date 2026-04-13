# Changelog

## 2.3.0 (stable) - 2026-04-13

- Upgrade the build chain into a canonical end-to-end workflow-state machine by adding schema `v1`, a generic stage-state recorder, bootstrap seeding, stale-transition guards, and canonical stage-ledger normalization for `help`, `next`, `save`, and `resume`.
- Cut `help`, `next`, and session continuity consumers over to canonical workflow-state so plan or spec docs, session or handover notes, packet index, and legacy workflow artifacts remain sidecars until bootstrap seeds the machine root.
- Add repo-operator `bootstrap`, extend regression coverage for bootstrap, blocked or override transitions, empty or corrupt machine roots, and deploy or secure edge cases, then refactor workflow-state internals into smaller focused modules while keeping release and bundle contracts stable.


## 2.2.0 (stable) - 2026-04-12

- Remove the retired runtime-era package subtrees from the repo and clean current docs so historical runtime-tool names remain only in archive/history surfaces and git history.
- Continue the V4 lean pass by splitting operator-state and workflow-state projection internals into focused modules while keeping `help`, `next`, `save`, and `resume` contracts stable.
- Continue the V4 lean pass by splitting route analysis, delegation, and route-preview internals into focused modules while keeping route-preview payloads, delegation semantics, and bundle contracts stable.
- Add V4.1 facade line-budget guardrails and rerun canonical repo, bundle, and route/state verification on the kernel-only shipping line.


## 2.1.1 (stable) - 2026-04-11

- Fix `next` and `save context` so stale `ready-for-merge` workflow summaries stop overriding a clean, synced repo after handoff.
- Filter stale merge-ready follow-ups out of session persistence, and keep `best_next_step` empty when no actionable work remains.
- Add regression coverage for stale workflow-state filtering in `help/next` and `save`, then refresh local operator state artifacts to match the live slice.


## 2.1.0 (stable) - 2026-04-11

- Shrink `forge-core/SKILL.md` into a bootstrap contract and move adapter-specific host behavior into canonical `SKILL.delta.md` sources for `forge-codex` and `forge-antigravity`.
- Add dedicated SKILL composition tooling so adapter `overlay/SKILL.md` files are generated from core shared sections plus adapter deltas, while release builds compose shipped bundle skills directly instead of copying source overlays blindly.
- Harden the repo gate around thin-SKILL by adding generated-overlay verification, anti-dup and line-budget tests, and release checks that reject stale adapter skill artifacts in source or dist.
- Refresh release-facing and continuity surfaces so `VERSION`, `CHANGELOG.md`, `README.md`, `docs/release/*`, and `.brain/decisions.json` align on `2.1.0` as the current stable release after the thin-SKILL refactor cut.
- Rebuild release artifacts and sync the verified `forge-antigravity` and `forge-codex` runtime installs from `dist/` after the canonical repo gate passes.


## 2.0.0 (stable) - 2026-04-11

- Contract Forge as a kernel-only product line by shipping only `forge-core`, `forge-codex`, and `forge-antigravity`, while retiring `forge-browse`, `forge-design`, `forge-design-state`, and the source-only Next.js Postgres companion from the active repo surface.
- Remove runtime-tool, companion-preset, canary, lane-scoring, and brief-generator subsystems from `forge-core`, and realign route preview, workspace init, bundle verification, reference docs, and skill overlays to the kernel-only contract.
- Refresh release-facing and continuity surfaces so `VERSION`, `CHANGELOG.md`, `README.md`, `docs/release/*`, and `.brain/decisions.json` align on `2.0.0` as the current stable release after the V3 contraction cut.
- Rebuild release artifacts and sync the verified `forge-antigravity` and `forge-codex` runtime installs from `dist/` after the canonical repo gate passes.


## 1.17.0 (stable) - 2026-04-11

- Retire nine low-value Forge workflows from the live core surface: `change`, `verify-change`, `review-pack`, `release-doc-sync`, `release-readiness`, `adoption-check`, `doctor`, `dashboard`, and `map-codebase`.
- Collapse the default solo release contract to `brainstorm -> plan -> visualize -> architect -> spec-review -> build -> test -> self-review -> secure -> quality-gate -> deploy`, and replace `doctor -> map-codebase` onboarding with direct `help/next -> plan` guidance.
- Refresh release-facing and continuity surfaces so `VERSION`, `CHANGELOG.md`, `README.md`, `docs/release/*`, and `.brain/*` align on `1.17.0` as the current stable release for the workflow slim-down tranche.
- Rebuild release artifacts and sync the verified `forge-antigravity` and `forge-codex` runtime installs from `dist/` after the canonical repo gate passes.


## 1.16.0 (stable) - 2026-04-11

- Retire `frontend` and `backend` as live Forge domain skills by removing `domain_skills` from routing, route preview output, canary checks, smoke validators, and activation lines without leaving a compatibility shim.
- Preserve the useful backend and UI guidance by absorbing it into `build`, `spec-review`, `visualize`, and the reference map while keeping backend or UI brief tooling discoverable as workflow-support tooling instead of top-level skills.
- Refresh stable-release and continuity surfaces so `VERSION`, `CHANGELOG.md`, `README.md`, `docs/release/*`, and `.brain/*` align on `1.16.0` as the current stable release after this refactor tranche.
- Rebuild release artifacts and sync the verified `forge-antigravity` and `forge-codex` runtime installs from `dist/` after the canonical repo gate passes.

## 1.15.1 (stable) - 2026-04-10

- Normalize every `forge-core` child skill footer to end with `Used skill: <skill-name>.` instead of deployment wording so response provenance reads naturally on real tasks.
- Require multi-skill footer blocks to emit one unique `Used skill:` line per skill, preventing duplicated footer lines when one task routes through several Forge skills.
- Refresh release-facing stable-version surfaces and continuity artifacts so `VERSION`, `CHANGELOG.md`, `README.md`, `docs/release/*`, and `.brain/*` all agree on `1.15.1` as the current maintenance release.
- Rebuild the shipped bundles and sync the updated `forge-antigravity` and `forge-codex` installs from the verified release output after the repo gate passes.


## 1.15.0 (stable) - 2026-04-02

- Add a host-aware delegation preference contract so each new thread restores typed delegation intent, route preview resolves the same preference as runtime routing, and capable hosts can delegate automatically without relying on `custom_rules` prose.
- Split delegation resolution cleanly between core defaults and host overlays by moving `forge-core` to `default_tier`, promoting Codex to `parallel-workers`, and correcting Antigravity back to `controller-baseline` when it cannot honestly dispatch subagents.
- Preserve existing installs by mapping legacy delegation markers from `custom_rules` into the new typed preference with warnings, extending write or apply flows to persist the migrated field, and hardening route, smoke, and release tests around the host by preference matrix.
- Close `1.15.x` into maintenance mode by syncing release-facing docs, target-state, roadmap inventory, and continuity artifacts around one current stable line, with regression coverage to catch future doc or continuity drift.
- Re-verify the release through targeted bundle checks, smoke matrix coverage, release build, and the canonical `verify_repo.py` gate before marking `1.15.0` as the current stable Forge release.


## 1.14.0 (stable) - 2026-04-02

- Ship the competitive `1.14.x` execution-kernel upgrade by adding an explicit fast-lane packet mode for low-risk slices, while preserving proof-before-claims, verification rerun, and residual-risk capture.
- Upgrade packetized execution into graph-aware contracts across routing, tracking, and workflow summaries, including dependency and unblock links, merge intent, overlap risk, readiness states, and completion gates.
- Add runtime-health diagnostics and doctor-style runtime checks for browser-capable toolchains, plus host capability contract v2 with tiered dispatch reasons and fallback reasons that keep packet semantics host-neutral.
- Promote the `1.14.x` target and closure boundaries into tracked references, add bounded continuity packet-index support, extension-preset boundary contracts, onboarding guidance, and release-contract regression coverage.

## 1.13.0 (stable) - 2026-04-02

- Turn `1.13.0` into Forge's first build-process enhancement release by freezing a canonical build-packet contract across execution progress, chain status, workflow summaries, and host-facing dispatch guidance.
- Make `help`, `next`, and dashboard state-first for active build packets, pending browser QA proof, and next merge points, so medium and large build work resumes from workflow-state instead of reconstructed chat context.
- Keep browser QA packet-scoped and evidence-backed by classifying packet eligibility in routing, recording browser proof into workflow-state through the runtime wrapper, and hardening the wrapper so downstream runtime-tool flags are forwarded intact.
- Expand regression coverage for packetized build execution, legacy workflow-summary normalization, runtime-tool forwarding, and release verification, then mark `1.13.0` as the current stable Forge release after the canonical repo gate passes.


## 1.12.0 - 2026-04-01

- Mature Forge into a stronger solo-dev operating model by freezing a canonical four-tier release contract, feeding bounded adoption signals back into release readiness, and keeping release follow-up packets explicit instead of ad hoc.
- Make `help`, `next`, and dashboard summaries read real release-tail state, including workflow stage, release tier, latest gate, and latest adoption signal, so long-running release work no longer depends on operator memory.
- Align core, Codex, and Antigravity release-surface wording with the same contract, harden the `1.12.x` roadmap closure rules, and keep architecture plus target-state references explicit enough to close the roadmap with tracked evidence.
- Mark `1.12.0` as the current stable Forge release once the canonical release gates and the separate roadmap-complete closure sweep are both green.


## 1.11.0 - 2026-04-01

- Harden Forge's routing and release contracts by scanning untracked secrets, recording dirty-tree provenance in `BUILD-MANIFEST.json`, and requiring fresh `dist/` adapter registries to prove the full inherited solo-profile contract.
- Surface solo-profile and release-tail workflow semantics across core and adapter docs, add explicit release tiers plus richer adoption signals, and clarify the architecture boundary between sparse overlays and materialized bundles.
- Keep `route-preview` workflow state resumable through `help` or `next` and `run` guidance, explicitly reject the nonexistent `/gate` alias in host-facing docs, and extend regression coverage around workflow-state and release-tail verification.


## 1.10.2 - 2026-04-01

- Add `docs/release/github-public-switch-checklist.md` as a tracked release-facing checklist so public readiness guidance no longer depends on an untracked local file.
- Harden `tests/test_release_hardening.py` to require the public-switch checklist in clean clones and CI, preventing the same release-doc drift from slipping through again.
- Refresh `docs/release/public-readiness.md` with the tracked checklist reference and the latest 2026-04-01 verification evidence for the patch release.

## 1.10.1 - 2026-03-30

- Normalize `CHANGELOG.md` to English-first public prose across the full release history so the public release surface stays readable and encoding-safe.
- Expand the GitHub Actions verify workflow to a Windows, Ubuntu, and macOS matrix while keeping the canonical repo verification command unchanged.
- Materialize empty `forge-design-state` layout up front, including `state/renders.jsonl`, and add regression coverage for that contract.
- Add an explicit maintainer contact path in `SECURITY.md`, refresh release notes for the patch snapshot, and ship a paste-ready GitHub Release body.

## 1.10.0 - 2026-03-30

- Add the public-release groundwork for Forge, including `MIT` licensing, root contribution or conduct or security docs, and a repo-visible public-readiness checklist.
- Rewrite the root README so Forge is introduced as a process-first orchestration system with detailed install guidance for Codex, Antigravity, runtime tools, and explicit core installs.
- Clean maintainer-local paths out of release-facing docs, remove host soak as a release precondition from the current policy, and add release-hardening regression checks to keep the public release contract stable.

## 1.9.0 - 2026-03-30

- Adopt an artifact-driven TDD/SDD rollout across `forge-core`, including `verify-change`, requirements/spec packet checks, worktree preparation, stronger quality-gate enforcement, and sharper route/execution policy for medium or risky work.
- Add strategic product-policy docs and operator references for the new target state, benchmark, roadmap, and self-hosted change flow so future Forge changes can be evaluated against an explicit north star instead of drifting by local convenience.
- Sync Codex and Antigravity host wrappers, release fixtures, archive the self-hosted exemplar packet, and keep full repo plus dist-bundle verification green after the release bump.

## 1.8.0 - 2026-03-29

- Harden Forge's process-first execution model by routing small build and visualize work through planning, persisting richer execution and review state, and enforcing durable process artifacts plus RED-proof quality gates.
- Downgrade `forge-nextjs-typescript-postgres` to a source-only example companion, remove it from shipped bundle and install surfaces, and decouple its local reference contract from the monorepo release version.
- Refresh release, install, and bundle verification coverage so example companions remain discoverable from source while `build_release.py` and `verify_repo.py` only govern shipped bundles.

## 1.7.0 - 2026-03-29

- Finish the process-first implementation batch by hardening brownfield operator flows, change and continuity artifacts, release readiness, workspace canaries, and stack-aware review signals across `forge-core`.
- Reframe current shipping surfaces around a stack-agnostic Forge identity, clarify that companions are optional adaptation layers, and downgrade `forge-nextjs-typescript-postgres` to an optional reference companion instead of the product center of gravity.
- Refactor shared repo-signal and test-support helpers, remove stale fixture snapshots and obsolete delivery docs, and keep the repo cleaner while preserving current release verification coverage.

## 1.6.1 - 2026-03-29

- Recenter Forge's canonical strategy on a process-first, stack-agnostic execution model by adding the new thesis and roadmap, and by marking the prior lane-first thesis, roadmap, backlog, and normalization docs as historical or superseded.
- Add a current implementation plan that translates the new process-first roadmap into concrete build order, file or surface boundaries, and verification slices across `forge-core`, runtime tools, host adapters, and the reference companion.

## 1.6.0 - 2026-03-29

- Normalize Forge's product policy so the thesis, roadmap, audit, backlog, and delivery reports agree on one committed first-party lane, historical versus current decisions, and what counts as shipped versus planned absorption.
- Tighten the lane-2 decision contract in `forge-core` by requiring explicit strategic product-pull confirmation instead of treating rollout evidence alone as automatic approval.
- Add a repo-visible absorption consistency report and clarify that governance artifacts beyond current planning docs plus the initial `change_guard` privacy or risk rail remain partial or planned follow-up work.

## 1.5.0 - 2026-03-29

- Turn Forge into a stronger solo-dev execution platform by adding brownfield `doctor`, `map-codebase`, change-artifact flows, dashboard, release-doc sync, release readiness, review packs, and lane scoring or gating across `forge-core`.
- Add the first-party `forge-nextjs-typescript-postgres` companion with companion-aware install or init flows, stack-specific command and verification packs, and presets for minimal SaaS, auth, billing, and deploy-observability paths.
- Strengthen real-world delivery evidence with multi-repo canaries, authenticated runtime QA improvements in `forge-browse`, and the supporting release or audit docs needed to steer lane-1 hardening and future lane decisions.

## 1.4.1 - 2026-03-28

- Tighten runtime-tool consistency by teaching host bundles to consume `runtime_tools_relative_path` from build and install manifests instead of relying only on registry or sibling-bundle fallback.
- Add end-to-end host-wrapper coverage for `forge-design -> forge-browse`, so Codex and Antigravity both verify the real wrapper path used to render and capture review artifacts.
- Refresh tooling docs and contract tests so the generated host-artifact inventory and runtime-tool resolution surface stay aligned with the implementation.

## 1.4.0 - 2026-03-28

- Add runtime-tool resolution and invocation to Forge host bundles, so `forge-codex` and `forge-antigravity` can call `forge-browse` and `forge-design` through registry-backed wrappers instead of hardcoded install paths.
- Register runtime-tool targets during install, persist them in adapter-global state, and surface the new contract in release docs, packaging metadata, and host-facing design guidance.
- Expand regression coverage for runtime-tool resolution, installed host invocation, and release or install flows so the new host-runtime boundary remains verified by `verify_repo.py`.

## 1.3.0 - 2026-03-28

- Absorb the planned gstack-inspired improvements into Forge: generated host artifacts with freshness gates, unified workflow state, hardened packaging manifests, runtime actuators, and design runtime tooling.
- Add real runtime verification for `forge-browse` and `forge-design`, including live Playwright smoke, installed bundle integration smoke, and persisted brief capture evidence flows.
- Expand release and contract coverage so Codex host wrappers are generated from canonical sources, package matrix metadata stays authoritative, and `verify_repo.py` remains the single repo gate before promotion.

## 1.2.0 - 2026-03-28

- Fix release-bundle verification stability for `forge-codex`, including correct handling of the materialized bundle layout in `support.py` and avoiding a skewed `support` import in the dist suite.
- Normalize agent-facing prose for `forge-antigravity` across `SKILL.md`, `GEMINI.global.md`, operator wrappers, and the operator-surface reference so it reads more natively without changing workflow semantics.
- Update the smoke contract for `prepare_bump.py` so auto-preview cases without git context accept `inferred_from = no-git-context`, and keep full release verification green after the bump.

## 1.1.0 - 2026-03-27

- Raise the native-clear quality of `forge-core` and `forge-codex` across workflows, references, operator wrappers, and host docs so Codex reads routing, gates, and proof requirements with less ambiguity.
- Fix the locale and runtime contract for `forge-codex`, including a UTF-8 Vietnamese locale pack, bundle-aware loading through `FORGE_BUNDLE_ROOT`, and a support shim so overlay tests pass both in isolation and alongside `forge-core`.
- Expand regression coverage and keep release evidence green after the change, while bumping version by minor semver because the adapter and runtime support layer gained new capability.

## 1.0.0 - 2026-03-27

- Complete the repo-wide agent-health refactor by splitting script and test hotspots into smaller modules, keeping stable entrypoints, and bringing all Python source outside `dist/` plus `.install-backups/` under the 300-line per-file target.
- Normalize release and runtime contracts by materializing the overlay registry during build, tightening the verify pipeline with secret scan and release-hardening coverage, and preserving bundle install, preferences, help-next, route preview, smoke matrix, and workspace canary flows through the split.
- Reduce workspace-reading noise with `.ignore`, add remediation or review reporting, and lock in full verification for both source and dist bundles before release.

## 0.14.0 - 2026-03-27

- Expand host-level bootstrap for `forge-codex` and `forge-antigravity`, adding global templates that spell out the state root, split preference files, the absolute resolver, and the activation flow used to render `AGENTS.md` and `GEMINI.md`.
- Add self-healing for extra preferences when recoverable mojibake appears, and tighten `response_contract` to catch invalid `tone_detail` cases such as losing the expected user and assistant forms of address.
- Increase release and install regression coverage to lock bootstrap preferences, host activation, and release overlays across both source and dist bundles.

## 0.13.0 - 2026-03-27

- Restore automatic response personalization at the start of each new thread for `forge-codex` and `forge-antigravity`, including bootstrap instructions in host entrypoints and the default Antigravity prompt.
- Add bundle-native dev-state fallback through build metadata so `forge-core`, `forge-codex`, and `forge-antigravity` can resolve the correct adapter-global state root even before an install manifest exists.
- Expand release regression tests to lock bootstrap preferences and state-root resolution across both source overlays and dist bundles before release.

## 0.12.0 - 2026-03-27

- Improve native Vietnamese quality in `forge-codex` by cleaning `locale/vi` back to proper UTF-8, adding regression coverage for more natural Vietnamese prompts, and blocking mojibake from re-entering bundle assets.
- Add a response-contract validator plus smoke and tests so `forge-codex` adheres more tightly to the Vietnamese output and evidence contract.
- Tighten adapter boundaries so shared core code does not embed `.codex` assumptions directly, while keeping host-specific optimizations inside `forge-codex`.

## 0.11.0 - 2026-03-27

- Fully separate locale routing and output-contract ownership from `forge-core`, keeping core EN-only and moving locale ownership to adapter overlays.
- Add Vietnamese locale packs and output-contract profiles for `forge-antigravity` and `forge-codex`, with adapter-level regression tests and matching release checks.
- Normalize personalization, docs, and test fixtures to English-first in core, while adding verify coverage so dist bundles still pass with bundle-aware contracts.

## 0.10.0 - 2026-03-27

- Split preference logic in `forge-core` out of `common.py` into focused modules such as `preferences.py`, `compat.py`, `style_maps.py`, `skill_routing.py`, `text_utils.py`, and `error_translation.py`, while keeping `common.py` as a re-export shim so existing entrypoints do not break.
- Simplify preference persistence around split-file adapter-global state with canonical fields in `state/preferences.json`, extras in `state/extra_preferences.json`, preserving `output_contract`, and only migrating legacy single-file state on write or apply flows.
- Reduce `forge-antigravity` compat config to read or migration-only, update docs, workflows, and contracts across `forge-core`, `forge-codex`, and `forge-antigravity` for the new semantics, and expand regression plus release verification to lock split-file behavior from source bundles through dist bundles.

## 0.9.0 - 2026-03-26

- Sync tests, docs, and release verification for split-file preferences after the v0.8.0 refactor.
- Update regression tests to lock canonical-plus-extras persistence across both source and dist bundles.
- Clean up residual doc drift between `forge-core`, `forge-antigravity`, and `forge-codex` after adding `output_contract`.

## 0.8.0 - 2026-03-26

- Add `output_contract` in `forge-core` to infer display policy from workspace extras such as `language`, `orthography`, `tone_detail`, and `custom_rules`.
- Add an `extra preferences` template to personalization docs so users can set language quickly through `.brain/preferences.json`.
- Update the `customize` flow in `forge-codex` and `forge-antigravity` so language requests get short, direct responses that point to the extras template instead of long explanations about canonical preferences.
- Add the PowerShell helper `enable_windows_utf8.ps1` for `forge-codex` to reduce Vietnamese mojibake on Windows.

## 0.7.2 - 2026-03-25

- Fix the `session` contract in `forge-core` so restore flow loads `.brain/preferences.json` via `resolve_preferences.py` before summarizing context.
- Update the `forge-codex` session override so recap and next-step output follows workspace response preferences instead of skipping personalization.
- Add regression tests in `forge-core` and the release repo to lock preference restore for both source and dist bundles of `forge-codex` and `forge-antigravity`.

## 0.7.1 - 2026-03-24

- Sync the `/bump` contract in `forge-antigravity` and `forge-codex` with `forge-core`, so both hosts use the new wording and semver guardrails.
- Add a release-repo regression test to prevent adapter wrappers or skills from drifting away from the core bump contract in future updates.
- Rebuild and reinstall host bundles from a clean commit so the manifest, version, and installed `.codex` or `.gemini` content stay aligned.

## 0.7.0 - 2026-03-24

- Add host-aware delegation to Forge, including `parallel-split` and `independent-reviewer` routing, the `dispatch-subagents` workflow, and Codex wiring that enables delegation runtime when the host truly supports subagents.
- Upgrade the `bump` flow to infer semver from workspace git diff, return reasoning plus confidence, and detect capability changes correctly in a monorepo.
- Resync contracts, docs, smoke tests, and release verification across `forge-core` and `forge-codex` so natural-language bump retains explicit release guardrails.

## 0.6.0 - 2026-03-24

- Add Codex host takeover for `forge-codex` via `AGENTS.global.md` and `install_bundle.py --activate-codex`, with backup-and-retire handling for `~/.codex/awf-codex` and legacy `awf-*` skills.
- Add the missing Wave C artifacts for `forge-codex`: a Codex-specific session workflow, smoke references, registry override, and release or install verification for the host activation path.
- Normalize the Forge narrative toward a natural-language-first Codex experience and keep the `forge-codex` `SESSION` contract consistent with registry, wrapper, docs, and dist output.

## 0.5.1 - 2026-03-24

- Normalize fully accented Vietnamese prose across the Markdown source for `forge-core`, `forge-antigravity`, and `forge-codex`.
- Clean up residual broken-accent forms like `kh?ng` or `???c` in docs, workflow wrappers, plans, and release references so the source repo reads cleanly.
- Rebuild `dist/` from the normalized source and re-verify the full repo so release bundles match the new text.

## 0.5.0 - 2026-03-24

- Add Wave C to `forge-codex` with thin wrappers for `help`, `next`, `run`, `bump`, `rollback`, `customize`, and `init`.
- Update `AGENTS.example.md` and adapter docs so Codex stays natural-language first, slash commands remain optional aliases, and Forge orchestration rules are not duplicated.
- Add `codex-operator-surface.md` and release tests so build and install preserve the Codex overlay across each release.

## 0.4.0 - 2026-03-24

- Add Wave B to `forge-antigravity` with operator wrappers for `help`, `next`, `run`, `bump`, `rollback`, `customize`, `init`, and session handover flows.
- Expand `forge-core` with preference persistence via `write_preferences.py`, add `pace` and `feedback_style`, and add reusable workspace bootstrap through `initialize_workspace.py`.
- Harden `install_bundle.py` around in-place sync so rollouts stay safe on Windows even when the runtime directory is locked by the host.
- Increase verify coverage and add regression, smoke, and overlay checks for Wave B.

## 0.3.0 - 2026-03-24

- Add Wave A / P1.1 with a host-neutral error translator wired directly into `run`, turning raw technical failures into readable guidance and recovery paths.
- Add Wave A / P1.2 with a shared bump workflow through `prepare_bump.py` that updates `VERSION`, changelog, and release checklist under one contract.
- Add Wave A / P1.3 with a rollback guidance engine through `resolve_rollback.py`, classifying deploy, config, migration, and code-change issues and proposing safe recovery steps.
- Upgrade full regression, smoke matrix, and adapter wiring so both Antigravity and Codex runtimes inherit the entire Wave A surface from core.

## 0.2.0 - 2026-03-24

- Add Wave A / P0.1 with a host-neutral preferences engine for `technical_level`, `detail_level`, `autonomy_level`, and `personality`.
- Add Wave A / P0.2 with a repo-first help and next navigator shared by `forge-antigravity` and `forge-codex`.
- Add Wave A / P0.3 with a run-guidance engine that executes real commands, detects ready signals, and routes onward to `test`, `debug`, or `deploy`.
- Expand regression, smoke matrix, and adapter wiring so both Antigravity and Codex runtimes inherit the same core contract.

## 0.1.0 - 2026-03-24

- Split Forge into the `forge-core + forge-antigravity + forge-codex` monorepo.
- Add the standard release pipeline with `build_release.py`, `verify_repo.py`, and `install_bundle.py`.
- Normalize `forge-core` around a host-neutral design while keeping host-specific entrypoints in adapter overlays.
- Add monorepo-level tests for build, install, version flow, and release documentation.

<!-- FORGE CODEX GLOBAL START -->
<!-- GENERATED FILE. Run `python scripts/generate_host_artifacts.py --apply` after editing this canonical source. -->
# Forge Codex

Forge is the evidence-first execution kernel for real repos on Codex: natural-language first, verification before claims.

Use `forge-codex` as the only global orchestrator for Codex.

## Read Order

1. Read this global `AGENTS.md`.
2. Load `{{FORGE_CODEX_SKILL}}`.
3. If the workspace has its own `AGENTS.md` or router doc, treat it as local augmentation, not a replacement.

## Host Bindings

- Bundle root: `{{FORGE_CODEX_BUNDLE_ROOT}}`
- Preferences resolver: `{{FORGE_CODEX_RESOLVER}} --workspace <workspace> --format json` via `resolve_preferences.py`
- Canonical resolver script: `{{FORGE_CODEX_RESOLVER_SCRIPT}}` (`resolve_preferences.py`)
- State root: `{{FORGE_CODEX_STATE_ROOT}}`
- Canonical state layout: `state/preferences.json` under the state root above.
- Preferences file: `{{FORGE_CODEX_PREFERENCES_PATH}}`

## Scope Of This File

- This file is the global bootstrap layer, not the full process manual.
- Keep detailed routing, workflow logic, and quality gates in the Forge bundle files.
- Update this file only when the host bindings, precedence rules, or top-level alias surface changes.

## Thread Bootstrap

- On every new thread, restore Forge response personalization before the first substantive reply.
- Resolve adapter-global preferences from `{{FORGE_CODEX_PREFERENCES_PATH}}`.
- Treat `{{FORGE_CODEX_STATE_ROOT}}` as the canonical adapter-global state root; only fall back to the equivalent `$FORGE_HOME/state/...` paths when the install target is intentionally overridden.
- Prefer the canonical resolver at `{{FORGE_CODEX_RESOLVER}} --workspace <workspace> --format json` when the merged payload is needed.
- If a merged payload is not needed, read the preference file directly instead of only one field subset.
- Apply the resolved language, orthography, tone detail, and custom writing rules as active instructions; do not wait for the user to repeat customization in each new thread.

## Mandatory First Action

Before the first substantive reply in every new thread:

1. Restore personalization from the resolver above, or read the preference file directly when a merged payload is not needed.
2. Apply language, orthography, tone detail, and custom rules immediately.
3. If the resolved language is Vietnamese, use full Vietnamese diacritics and repair mojibake instead of copying corrupted text.
4. If preferences are unavailable, continue with concise, direct, technical output in the host-default language.

## Core Routing Rules

- Natural language is the primary surface.
- Unknown slash commands are plain user input unless the host maps them to an installed Forge skill or a workspace-local router.
- Check Forge skills before any response or action. If there is even a 1% chance a Forge skill applies, invoke it first.
- Process skills come before implementation skills.
- Sibling Forge skills are host-native skills, not internal workflow files.
- Installed sibling skills: `forge-init`, `forge-brainstorming`, `forge-writing-plans`, `forge-executing-plans`, `forge-test-driven-development`, `forge-using-git-worktrees`, `forge-dispatching-parallel-agents`, `forge-subagent-driven-development`, `forge-systematic-debugging`, `forge-requesting-code-review`, `forge-receiving-code-review`, `forge-verification-before-completion`, `forge-finishing-a-development-branch`, `forge-customize`, `forge-bump-release`, `forge-deploy`, `forge-writing-skills`, `forge-session-management`.
- For small, low-risk requests where a skill adds no value, answer directly.
- Read only the files needed for the current task; do not bulk-load the whole bundle.
- If a skill or referenced file is missing, say so briefly and continue with best effort.
- Use host-native tools and instructions only; do not reference unavailable tool names or host-specific features from another environment.
- Workspace-local routers may extend Forge, but they do not replace Forge's verification, evidence, scope-control, or reporting rules.
- If local guidance conflicts with Forge, Forge wins on verification and scope; local guidance may refine repo-specific conventions and stack-specific commands.
- Prefer repo state, plans, specs, and scoped `.brain/` artifacts over session ceremony.
- Keep scope minimal; ask before new dependencies, schema changes, or folder-structure changes.
- Do not fabricate telemetry, token counters, or progress percentages.
- Durable preferences live in Codex-global adapter state `{{FORGE_CODEX_STATE_ROOT}}`, in the canonical file `{{FORGE_CODEX_PREFERENCES_PATH}}`.

## Global Verification Rule

Do not say `done`, `fixed`, or `tests pass` without fresh evidence.

Before closing a task:

1. Define the verification method before editing.
2. For behavior changes with a viable harness, one failing test must exist and fail for the correct reason before implementation code.
3. Code written before RED must be deleted and restarted from RED; "keep as reference" is not an exception.
4. Without a harness, use the strongest available repro, smoke check, build, lint, typecheck, diff, or content check and state why before editing.
5. Re-run the same verification after the change; do not swap to a weaker check at the end.
6. Report the latest result exactly, plus any unverified residual risk.
7. If verification cannot run, say `not verified`, name the blocker, and do not turn partial evidence into a completion claim.
8. Docs-only changes must use path, content, or diff verification; do not pretend there was a test.

## Global Skill Usage Footer

When one or more Forge skills were used for the response, end the response with one final non-empty line in this form:

```text
Skills used: brainstorming, writing-plans, verification-before-completion
```

Rules:

- Use the exact prefix `Skills used:`
- List only Forge skill names that were actually used for the response, without the `forge-` prefix
- Keep the skill names unique
- Omit the footer entirely when no Forge workflow skill was used
- Keep the `Skills used:` line as the final non-empty line when it is present
- Do not add any content after that line

## Operator Surface

- Natural-language requests remain the preferred entrypoint.
- `delegate` stays available when a concise Codex action name helps.
- Release bump preparation routes through the sibling skill `forge-bump-release`.
- Live deploy requests and production-readiness checks route through the sibling skill `forge-deploy`.
- Guidance, next-step selection, and command execution stay natural-language first through Forge skills and host-native tools.
- Session continuity requests stay explicit and natural-language first: `resume`, `save context`, and `handover`.

## Activation Announcement

```text
Forge Codex: orchestrator | natural-language first, verification before claims
```

<!-- FORGE CODEX GLOBAL END -->


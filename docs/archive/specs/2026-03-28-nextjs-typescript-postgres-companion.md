# Nextjs Typescript Postgres Companion Proposal
Created: 2026-03-28 | Status: Proposed
Purpose: define how `nextjs + typescript + postgres` should live as a first-party companion while `forge-core` stays the orchestrator.

## Position

This proposal assumes:
- `forge-core` stays lane-agnostic orchestrator
- `nextjs + typescript + postgres` becomes a first-party companion, not a core assumption
- the companion is the first optimized product path, not the identity of Forge

This keeps Forge broad in concept and sharp in execution.

## 1. Core To Companion Contract

### 1.1 Ownership

`forge-core` owns:
- intent routing
- complexity assessment
- change-artifact requirements
- evidence thresholds
- verification and quality-gate policy
- workflow-state schema
- continuity and report shape
- runtime-tool bridge

`nextjs-typescript-postgres` owns:
- stack detection beyond generic Node signals
- Next.js conventions
- TypeScript and folder conventions for this stack
- Postgres integration conventions for this stack
- stack-specific init presets
- stack-specific command profiles
- stack-specific verification packs
- stack-specific risks and deployment assumptions

### 1.2 Activation Rule

The companion should load only when at least one of these is true:
- the user explicitly asks for Next.js
- `package.json` clearly includes `next`
- the repo was initialized from this companion preset

Additional enrichers may activate when the repo also shows:
- `typescript`
- a Postgres adapter such as `pg`, `postgres`, `prisma`, `drizzle`, `kysely`, or Supabase Postgres usage

The companion should not load just because:
- the repo has `src/`
- the repo has `app/`
- the repo has `pages/`
- the repo is "web-like"

### 1.3 Invocation Model

The core should ask the companion for data, not surrender orchestration.

Recommended flow:
1. core detects intent and complexity
2. core detects generic runtime from repo artifacts
3. core checks companion registry for matching stack companions
4. if `nextjs-typescript-postgres` matches, core loads its capability manifest
5. core applies companion enrichers to routing, init, doctor, map-codebase, verify, and help-next
6. core still produces the final report, evidence contract, and residual-risk output

### 1.4 Data Contract

The companion should expose one machine-readable manifest. Suggested canonical file:
- `data/companion-capabilities.json`

Suggested top-level fields:
- `id`
- `version`
- `compatibility`
- `repo_signals`
- `match_rules`
- `init_presets`
- `command_profiles`
- `verification_packs`
- `doctor_checks`
- `map_enrichers`
- `risk_rules`
- `help_next_hints`
- `template_catalog`
- `example_catalog`

### 1.5 Compatibility Contract

The companion must declare:
- minimum supported `forge-core` version
- maximum tested `forge-core` version or compatibility range
- required runtime tools if any
- optional runtime tools if any

The core must be able to ignore unsupported companion fields safely.

### 1.6 Conflict Resolution

If core and companion disagree, core wins on:
- whether work needs change artifacts
- whether verification is strong enough
- whether a claim is proven
- report and handoff format
- residual-risk wording

The companion wins only on:
- stack-specific commands
- stack-specific file conventions
- stack-specific verification steps inside the core evidence gate
- stack-specific init and template defaults

## 2. Package Structure Proposal

Recommended package:
- `packages/forge-nextjs-typescript-postgres/`

Recommended tree:

```text
forge-nextjs-typescript-postgres/
|-- BUILD-MANIFEST.json
|-- README.md
|-- SKILL.md
|-- data/
|   |-- companion-capabilities.json
|   |-- command-profiles.json
|   `-- verification-packs.json
|-- references/
|   |-- stack-profile.md
|   |-- init-preset.md
|   |-- verification.md
|   |-- deploy-assumptions.md
|   `-- risk-profile.md
|-- templates/
|   `-- app/
|       |-- package.json
|       |-- tsconfig.json
|       |-- next.config.ts
|       |-- app/
|       |-- src/
|       `-- tests/
|-- examples/
|   `-- minimal-saas/
|-- scripts/
|   |-- verify_bundle.py
|   |-- resolve_commands.py
|   |-- enrich_map_codebase.py
|   |-- enrich_doctor.py
|   `-- scaffold_preset.py
`-- tests/
    |-- test_contracts.py
    |-- test_init_preset.py
    |-- test_command_profiles.py
    `-- test_verification_packs.py
```

### 2.1 File Roles

`SKILL.md`
- human-readable entry point for host skill loading
- states when to use and when not to use

`data/companion-capabilities.json`
- canonical source of what the companion can inject into core

`templates/`
- opinionated starter app for the lane
- should stay minimal, production-lean, and testable

`examples/`
- one or more known-good example repos that prove the companion works end to end

`scripts/`
- deterministic helpers the core can call or test against
- no second orchestrator logic

`tests/`
- compatibility and regression coverage for companion-specific behavior

### 2.2 Install Shape

This package should be treated as:
- a first-party optional bundle
- installable alongside `forge-core`
- visible in `docs/release/package-matrix.json`

Suggested package-matrix role:
- `host`: `companion`
- `default_target_strategy`: explicit

### 2.3 Host Surface Strategy

Do not create a second host-global router for this companion.

Instead:
- keep one canonical companion package
- let host adapters expose it through their normal skill discovery surface
- let `forge-core` route to it through manifest-driven matching

## 3. Capability Injection Policy

### 3.1 Allowed Injections

The companion may inject:
- repo detection hints
  - Next.js package markers
  - TypeScript markers
  - Postgres adapter markers
- init presets
  - starter app skeleton
  - env file templates
  - migration or schema placeholders
- doctor enrichers
  - stack-specific checks like `next`, TypeScript, Prisma or Drizzle, env requirements
- map-codebase enrichers
  - identify app router, server/client boundaries, schema layer, DB access layer
- command profiles
  - `dev`
  - `build`
  - `lint`
  - `typecheck`
  - `test`
  - migration-related commands
- verification packs
  - lint plus typecheck
  - unit and integration tests
  - env validation
  - schema or migration safety checks
- risk rules
  - migration risk
  - auth/session risk
  - cache or ISR risk
  - environment or secret risk
- help-next hints
  - stack-specific next-step suggestions after mapping or doctor output
- browse and design hints
  - suggested authenticated QA paths
  - high-value UI flows for browser verification
- example and template catalogs

### 3.2 Disallowed Injections

The companion must not inject:
- intent routing policy
- complexity thresholds
- evidence thresholds
- quality-gate decisions
- workflow-state schema changes
- new report or handoff formats
- auto-running deploys, migrations, or destructive commands by default
- host-global behavior that bypasses `forge-core`
- multi-stack companion chaining that turns into a second orchestrator

### 3.3 Soft-Allow Areas

These are allowed only through explicit core contracts:
- extra route-preview metadata
- stack-specific quality-profile hints
- stack-specific change-artifact templates
- stack-specific map-codebase focus modes

If core has no explicit contract for one of these, the companion should not invent it ad hoc.

## Recommended Next Step

Implement the companion in this order:
1. capability manifest
2. stack detection and command profiles
3. doctor enrichers
4. map-codebase enrichers
5. init preset and template
6. verification packs
7. example app and smoke tests

## Bottom Line

The right split is:
- `forge-core` remains the orchestrator
- `nextjs-typescript-postgres` becomes the first optimized companion

That gives Forge one strong golden path without turning the core into a web-specific framework.

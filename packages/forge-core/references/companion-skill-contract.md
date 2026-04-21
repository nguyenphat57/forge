## Companion Skill Contract

> Goal: describe how Forge can add runtime or framework skills without diluting Forge's orchestration, verification, or reporting rules.
> This is an optional extension layer. Forge core should remain effective even when no companion or local skills exist.

## When to read this file

- When creating companion skills for Python, Java, Go, .NET, or a framework-specific stack
- When updating Forge to work with new companion skills
- When the repo runtime is clear and you need to define the boundary between Forge and the runtime or framework layer

You do not need this file when:
- The repo does not have any companion or local skills yet
- Forge core is enough for the current plan/build/debug/review work
- The current task does not need a separate runtime or framework layer

## Default Operating Mode

By default Forge runs as:

```text
Forge core workflows + Forge references/tooling
```

Not:

```text
Forge + required companion skill
```

A companion should appear only when it clearly improves accuracy.

## Mental Model

Forge is the **process and orchestration layer**.
A companion skill is the **runtime or framework layer**.

Forge decides:
- intent routing
- complexity
- verification gates
- evidence thresholds
- residual-risk reporting
- handoff and report shape

A companion decides:
- language-specific coding idioms
- framework conventions
- stack-specific file and folder conventions
- build/test/run command discovery for that runtime
- dependency and toolchain details

## Trigger Contract

Load a companion only when the runtime is clear from repo signals or the user states the stack explicitly.

| Runtime | Common repo signals |
|---|---|
| Node.js | `package.json` |
| Python | `pyproject.toml`, `requirements.txt` |
| Go | `go.mod` |
| Java/Kotlin | `pom.xml`, `build.gradle` |
| .NET | `*.csproj`, `*.sln` |

Do not infer runtime from folder names, variable names, or agent habit.

## Integration Order

```text
1. Forge detects intent and complexity
2. Forge chooses the Forge workflows needed for the job
3. Forge detects runtime from source-of-truth repo artifacts
4. If the runtime is clear and a companion materially improves accuracy, load the companion
5. The companion supplies stack-specific conventions and commands
6. Forge still owns verification, reporting, and handoff
```

If no suitable companion exists, stop at step 3 and continue with Forge core.

## Ownership Boundary

| Area | Owner |
|---|---|
| Intent routing | Forge |
| Complexity assessment | Forge |
| Scope control | Forge |
| Verification-first / test-first gate | Forge |
| Evidence before claims | Forge |
| Output and handoff template | Forge |
| Language-specific coding idioms | Companion |
| Framework structure | Companion |
| Stack-specific command discovery | Companion |
| Dependency and toolchain details | Companion |

## Conflict Resolution

If Forge and a companion disagree, Forge wins on:
- verification
- evidence thresholds
- reporting
- residual risk
- scope discipline

The companion guides:
- runtime-specific code style
- framework structure
- stack-specific build, test, and run commands
- migration or tooling conventions that belong to that stack

A companion must not:
- bypass Forge's failing-test or reproduction gate when a harness exists
- lower the evidence bar just because the framework is familiar
- replace Forge's handoff or report format
- turn itself into a second orchestrator

## Optional Workspace-Local Layer

Companion skills may live in:
- a global skill library
- a workspace-local skill folder near the repo

Workspace-local companions apply only when the workspace uses the `global orchestrator + local companions` model.

A workspace-local companion is valid when:
- the workspace has `AGENTS.md` or a router doc that points to it
- the actual skill entry point is `SKILL.md`
- repo signals match the layer that skill owns

Prefer a workspace-local companion when:
- it captures repo-specific runtime or domain behavior
- the router doc explicitly points to it
- it does not conflict with Forge's evidence gate

If the workspace does not have a local layer, do not invent a fake router or local inventory just to use Forge.

## Router Docs vs Skill Docs

- `SKILL.md` is the triggerable skill entry point
- `AGENTS.md` or the workspace skill map is a router or reference document
- A router doc can say which skill to use, but the router doc itself does not replace `SKILL.md`
- Do not treat the router doc as a fake skill that embeds runtime logic

## Workspace Router Contract

This section applies only when the workspace uses the `global orchestrator + local companion skills` model.

Keep:
- a slim `AGENTS.md` with workspace identification, read order, and a pointer to the router/source-of-truth doc
- a workspace skill map as the source of truth for local skill inventory, routing precedence, fallback rules, examples, and smoke-test links

Do not:
- duplicate the same routing table in both `AGENTS.md` and the workspace map
- scatter local skill inventory across multiple files
- let each local skill describe the entire workspace architecture
- change router docs or local skill inventory without rerunning the checker

## Recommended Workspace Layout

```text
workspace/
|-- AGENTS.md
`-- .agent/
    |-- workspace-skill-map.md
    |-- routing-smoke-tests.md
    |-- local-skill-guidance.md
    `-- skills/
        |-- skill-a/SKILL.md
        `-- skill-b/SKILL.md
```

File names may vary, but the roles should stay the same.

## Minimum Companion Output

When a companion is loaded, it should quickly confirm:

```text
Runtime context:
- Stack/framework: [...]
- Repo signals: [...]
- Primary commands: [build/test/run/lint]
- Conventions to keep: [...]
- Stack-specific risks/constraints: [...]
```

It does not need to restate Forge's entire guardrail.

## Recommended Activation Pattern

```text
Forge: [intent] | [complexity] | Skills: [forge skills] + [companion skill]
```

Examples:

```text
Forge: BUILD | medium | Skills: plan + build + python-fastapi
Forge: DEBUG | small | Skills: debug + test + dotnet-webapi
```

## Design Rules for Companion Skills

Companion skills should:
- assume Forge already holds process discipline
- go straight to runtime-specific heuristics
- discover commands from the real repo whenever possible
- avoid hardcoding a framework unless the repo proves it
- keep references short instead of turning into a second orchestrator

## Anti-Patterns

- A companion routes intent instead of Forge
- A companion decides to skip verification because the stack is hard to test
- Forge bakes too many language-specific idioms into `build.md`, `plan.md`, or `architect.md`
- Multiple companions load at once when repo signals are still ambiguous
- Workspace-local skills remain active long after the repo removed that runtime or feature
- A companion lacks a clear `when not to use` boundary and gets loaded too often

## Evolution Policy

- Every companion should define `when not to use`
- Every companion should declare clear repo signals
- Workspaces with many local skills should keep routing smoke tests
- When a runtime or feature is retired, archive or remove the corresponding companion
- Keep local skills thin and repo-specific; do not duplicate Forge orchestration
- Keep `AGENTS.md` stable and slim, and concentrate routing detail in the workspace map
- When routing changes, update the workspace map first, then update entry-point docs if needed
- After changing router docs or local skill inventory, run `scripts/check_workspace_router.py`

## Quick Checklist

- [ ] Runtime is identified from real repo artifacts
- [ ] Forge still owns verification, evidence, and reporting
- [ ] The companion adds only stack-specific detail
- [ ] There are no overlapping or conflicting rules
- [ ] The activation line clearly names the companion skill in use

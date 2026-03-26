## Companion Skill Contract

> Goal: describe how Forge adds runtime/framework skills without obscuring Forge's orchestration, verification, and reporting.
> This is an optional extension class. Forge core should work well on its own even without any companions or local skills.

## When to read this file

- When creating companion skills for Python, Java, Go,.NET, or framework-specific stack
- When updating Forge to combine new companion skills
- Once the repo's runtime is clear and you need to close the boundary between Forge and the runtime/framework layer

There is no need to read this file if:
- The repo doesn't have any companion/local skills yet
- The new repo and Forge core are enough to plan/build/debug/review
- The current task does not need a separate runtime/framework layer

## Default Operating Mode

By default Forge runs as follows:

```text
Forge core workflows + Forge domains
```

Not:

```text
Forge + companion skill required
```

Companion skill only appears when it clearly increases accuracy.

## Mental Model

Forge is the **process/orchestration layer**.
Companion skill is **runtime/framework layer**.

Forge decided:
- intent routing
- complexity
- verification gate
- evidence threshold
- residual-risk reporting
- handover/report shape

Companion skill decides:
- idiom code according to language
- framework conventions
- file/folder conventions of the stack
- build/test/run command discovery according to runtime
- dependency/toolchain details

## Trigger Contract

Only load companion skills when there is a clear **repo signal** or the user clearly indicates the stack.

|Runtime | Repo signals are common|
|---------|------------------------|
|Node/Dr | `package.json`|
|Python | `pyproject.toml`, `requirements.txt`|
|Go | `go.mod`|
|Java/Kotlin | `pom.xml`, `build.gradle`|
|.NET | `*.csproj`, `*.sln`|

Don't guess the runtime just from folder names, variable names, or agent habits.

## Integration Order

```text
1. Forge detect intent + complexity
2. Forge chooses the main process/domain skills that are sufficient for the job
3. Forge detect runtime from source-of-truth artifact
4. If the runtime is clear and the companion skill really helps increase accuracy -> load companion skill
5. The Companion provides stack-specific conventions and commands
6. Forge applies verification gate, reporting, and handover
```

If you don't have a suitable companion skill, stop at step 3 and continue with Forge core.

## Ownership Boundary

|Area | Owner|
|---------|------------|
|Intent routing | Forge|
|Complexity assessment | Forge|
|Scope control | Forge|
|Verification-first / test-first gate | Forge|
|Evidence before claims | Forge|
|Output/handover template | Forge|
|Coding idioms by language | Companions|
|Framework structure | Companions|
|Stack-specific command discovery | Companions|
|Dependency/toolchain details | Companions|

## Conflict Resolution

If Forge and companion skill are different:

- According to Forge for:
  - verification. verification
  - evidence threshold
  - reporting. reporting
  - residual risk
  - scope discipline
- According to companion skill gives:
  - code style according to runtime
  - framework structure
  - stack-specific test/build/run commands
  - specific migration/tooling conventions

Companion skills cannot:
- Bypass Forge's failing test/reproduction gate when the harness is viable
- loosen evidence just because the framework is familiar
- Replace Forge's handover/report with its own format
- turns itself into a second orchestrator

## Optional Workspace-Local Layer

Companion skills can be in:
- global skill library
- workspace-local skill folder near the repo

Workspace-local layer only applies when the workspace actually selects the `global orchestrator + local companions` model.

Workspace-local companion skill is valid when:
- workspace has `AGENTS.md` or router doc pointing to it
- The real skill is `SKILL.md`
- repo signals match the layer that skill is responsible for

Prioritize workspace-local companion skill when:
- It attaches to the repo's own domain/runtime
- router doc of the specified workspace
- There is no conflict with Forge's evidence gate

If the workspace does not have a local layer, there is no need to create a fake router or local inventory to use Forge.

## Router Docs vs Skill Docs

- `SKILL.md` is a triggerable skill entrypoint
- `AGENTS.md` or workspace skill map is router/reference doc
- The router doc can say **which skill to use**, but the router doc itself does not replace `SKILL.md`
- Do not use router doc as a fake skill to insert runtime logic in place of the real skill

## Workspace Router Contract

This section only applies to workspaces select model `global orchestrator + local companion skills`.

Should keep:
- `AGENTS.md` slim:
  - workspace identification
  - read order
  - link to router/source-of-truth doc
- workspace skill map as source-of-truth for:
  - inventory local skills
  - routing precedence
  - fallback rules
  - examples and smoke-test links

Shouldn't:
- duplicate the same routing table in both `AGENTS.md` and workspace map
- Stuff your inventory full of local skills into many places
- Let each local skill describe the entire workspace architecture
- The router docs have been repaired but do not run the checker to catch drift

## Recommended Workspace Layout

```text
workspace/
├── AGENTS.md
└──.agent/
    ├── workspace-skill-map.md
    ├── routing-smoke-tests.md
    ├── local-skill-maintenance.md
    └── skills/
        ├── skill-a/SKILL.md
        └── skill-b/SKILL.md
```

The file name may be different, but the role should remain the same.

## Minimum Companion Output

When loaded, the companion skill should quickly confirm:

```text
Runtime context:
- Stack/framework: [...]
- Repo signals: [...]
- Primary commands: [build/test/run/lint]
- Conventions to keep: [...]
- Stack-specific risks/constraints: [...]
```

No need to duplicate Forge's entire guardrail.

## Recommended Activation Pattern

```text
Forge: [intent] | [complexity] | Skills: [forge skills] + [companion skill]
```

For example:

```text
Forge: BUILD | medium | Skills: plan + build + backend + python-fastapi
Forge: DEBUG | small | Skills: debug + test + dotnet-webapi
```

## Design Rule For Companion Skills

Companion skills should:
- assuming Forge has kept process discipline
- Go straight to runtime-specific heuristics
- Prioritize command discovery from the real repo
- Do not hardcode the framework if the artifact is not proven
- Keep references short, avoid turning companion into second orchestrator

## Anti-Patterns

- Companion skill automatically routes intent instead of Forge
- Companion skill decides to skip verification because "this stack is difficult to test"
- Forge embedding too many idioms of one language into `build.md` or `backend.md`
- Load many companion skills at the same time when the repo signal is not clear enough
- Let workspace-local skills live forever even though the repo has removed that runtime/feature
- Without `when not to use`, companion skills are heavily loaded

## Evolution Policy

- Companion skill should have part `when not to use`
- Companion skills should have clear repo signals
- Workspace should have smoke tests for routing if there are many local skills
- When the runtime/feature is abandoned, retire or archive the corresponding companion skill
- Keep local skills thin: repo-specific heuristics, don't duplicate Forge orchestration
- Keeps `AGENTS.md` stable and slim; Routing details should be concentrated on the workspace map
- When routing changes, update the workspace map first and then update the entrypoint docs if necessary
- After changing router docs or local skill inventory, run `scripts/check_workspace_router.py`

## Quick Checklist

- [ ] Runtime is determined from the actual artifact
- [ ] Forge still keeps verification/evidence/reporting
- [ ] Companion only adds stack-specific detail
- [ ] There are no overlapping or conflicting rules
- [ ] User-activation line clearly states which companion skill is being used

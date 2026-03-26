# Companion Routing Smoke Tests

> Used to stress test pairing Forge with companion skills. This file is only needed when the workspace chooses to use a companion/local layer; it is not a mandatory smoke test of Forge core.

## Pass Criteria

- Forge is still a process/orchestration layer
- Companion skill is selected correctly according to repo signals
- A clear runtime artifact (e.g. `pyproject.toml`, `go.mod`, `*.csproj`) may be enough to pull a suitable companion when the router inventory is clear.
- Router doc is used as a reference, not considered a skill
- Router filename is not required to contain `skill-map` if `AGENTS.md` points to the correct file
- Do not load too many companion skills when one skill is enough
- Verification/evidence gate still follows Forge

You can run `python scripts/run_smoke_matrix.py --suite router-check` to catch entrypoint-level drift before doing manual companion smoke on the real host.

## Scenario 1 - Pure Web Repo

```text
Prompt:
Fix bug in React page when route `/orders` rendered incorrectly after refactoring.
```

Expected:
- Forge detect BUILD/DEBUG
- Companion skill: unique web/runtime skill
- Do not load mobile/native/database skills if the repo signal is not needed

## Scenario 2 - Android Native Bridge

```text
Prompt:
Fix custom Capacitor plugin not receiving callback after app resume.
```

Expected:
- Forge + mobile shell companion + native bridge companion
- Not just web React skills
- Verification mentions sync/build/device smoke

## Scenario 3 - Schema / RLS Change

```text
Prompt:
Add a policy that only allows admins to read the notifications panel.
```

Expected:
- Forge + database/security companion
- Do not pull UI/web skills if the task is only located at the data boundary

## Scenario 4 - Workspace-Local Companion

```text
Prompt:
Fix outbox stuck in processing after app comes online again.
```

Expected:
- Forge reads `AGENTS.md` or workspace map if available
- Select local offline-sync companion if a workspace is defined
- Don't guess based on generic TS/web skills only in one way

## Scenario 4B - Runtime Signal Only

```text
Prompt:
Implement endpoint.
```

Expected:
- If the workspace inventory has `python-fastapi` and the signal repo has `pyproject.toml`, Forge can still choose that companion
- Do not force the prompt to write the word `python` naturally

## Scenario 5 - Router Doc Is Not Skilled

```text
Prompt:
Use the workspace map to choose the right skill for this deploy task.
```

Expected:
- Agent can read router doc
- But still load real skills from `SKILL.md`
- Do not consider router doc as a companion skill

## Scenario 6 - Minimal-Set Rule

```text
Prompt:
Deploy SPA website to Cloudflare after changing a fallback route.
```

Expected:
- Forge + web companion + deploy companion
- Do not load mobile/native/database companions if you do not need them

## Scenario 7 - Router Filename Flexibility

```text
Setup:
AGENTS.md points to `.agent/router.md`
```

Expected:
- Workspace router checker resolves correctly `.agent/router.md`
- It does not fail just because the file does not contain the string `skill-map`

## Failure Signs

- Loading too many 4-5 skills for small/medium tasks for no reason
- Router doc is considered an executable skill
- Companion skill override verification/evidence gate
- Choose companion only because the agent is familiar with that stack, not based on repo signals

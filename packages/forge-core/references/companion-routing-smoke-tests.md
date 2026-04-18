# Companion Routing Smoke Tests

> Use this file to stress test Forge when a workspace layers in companion skills. It is not a required smoke test for Forge core on its own.

## Pass Criteria

- Forge remains the execution kernel and orchestration system.
- Companion skills are selected correctly from repo signals or explicit stack cues.
- A clear runtime artifact such as `pyproject.toml`, `go.mod`, or `*.csproj` can be enough to select the right companion when the router inventory is clear.
- The router doc is treated as a reference, not as a skill.
- The router filename does not need to include `skill-map` if `AGENTS.md` points to the correct file.
- Forge does not load extra companion skills when one is enough.
- Verification and evidence gates still follow Forge.

You can run `python scripts/run_smoke_matrix.py --suite router-check` to catch route-entry drift before doing manual companion smoke on the real host.

## Scenario 1 - Pure Web Repo

```text
Prompt:
Fix bug in React page when route `/orders` rendered incorrectly after refactoring.
```

Expected:
- Forge detects BUILD or DEBUG.
- Selects the one relevant web/runtime companion.
- Does not load mobile, native, or database skills unless repo signals justify them.

## Scenario 2 - Android Native Bridge

```text
Prompt:
Fix custom Capacitor plugin not receiving callback after app resume.
```

Expected:
- Forge plus the right mobile-shell and native-bridge companions
- Not just generic React or web skills
- Verification mentions sync/build/device smoke

## Scenario 3 - Schema / RLS Change

```text
Prompt:
Add a policy that only allows admins to read the notifications panel.
```

Expected:
- Forge plus the relevant database or security companion
- Does not pull UI or web skills when the task lives entirely at the data boundary

## Scenario 4 - Workspace-Local Companion

```text
Prompt:
Fix outbox stuck in processing after app comes online again.
```

Expected:
- Forge reads `AGENTS.md` or the workspace map if available
- Selects the workspace-local offline-sync companion when the workspace defines one
- Does not guess only from generic TypeScript or web signals

## Scenario 4B - Runtime Signal Only

```text
Prompt:
Implement endpoint.
```

Expected:
- If the workspace inventory includes `python-fastapi` and repo signals include `pyproject.toml`, Forge can still choose that companion
- The prompt does not need to say `python` explicitly

## Scenario 5 - Router Doc Is Not a Skill

```text
Prompt:
Use the workspace map to choose the right skill for this deploy task.
```

Expected:
- The agent can read the router doc
- It still loads real skills from `SKILL.md`
- It does not treat the router doc itself as a companion skill

## Scenario 6 - Minimal Set Rule

```text
Prompt:
Deploy SPA website to Cloudflare after changing a fallback route.
```

Expected:
- Forge plus the relevant web and deploy companions
- Does not load mobile, native, or database companions without need

## Scenario 7 - Router Filename Flexibility

```text
Setup:
AGENTS.md points to `.agent/router.md`
```

Expected:
- The workspace router checker resolves `.agent/router.md` correctly
- It does not fail just because the file name does not contain `skill-map`

## Failure Signs

- Loading 4-5 skills for a small or medium task without a clear reason
- Treating the router doc as an executable skill
- Letting a companion override Forge's verification or evidence gates
- Choosing a companion only because the agent is familiar with that stack instead of because repo signals justify it

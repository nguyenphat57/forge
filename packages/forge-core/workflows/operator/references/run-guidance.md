# Forge Run Guidance

> Use this when a host-neutral `run` workflow is needed: execute the real command, summarize the main signal, and route to the next workflow instead of dumping raw terminal output.

## Target

- run the actual command in the specified workspace
- capture the main output, timeout, and ready signal
- classify the command as `build`, `serve`, `deploy`, or `generic`
- suggest the next workflow: `test`, `debug`, or `deploy`

## Canonical Script

```powershell
python commands/run_with_guidance.py --workspace C:\path\to\workspace --timeout-ms 20000 -- npm run dev
python commands/run_with_guidance.py --workspace C:\path\to\workspace --format json -- python -m pytest tests/unit
```

## Input Contract

- `--workspace`: root in which the command will run
- `--project-name`: optional workflow-state grouping label when persisting
- `--timeout-ms`: timeout budget
- command must be passed after `--`

## Output Contract

Script returns:

- `status`: `PASS` or `FAIL`
- `state`: `completed`, `running`, `failed`, or `timed-out`
- `command_kind`: `build`, `serve`, `deploy`, `generic`
- `suggested_workflow`
- `recommended_action`
- `error_translation` when the command fails or times out without a ready signal
- `stdout_excerpt` / `stderr_excerpt`
- `evidence`
- `readiness_detected`

## Routing Semantics

- `build` successful -> `test`
- `serve` has ready-signal and is alive after timeout -> `test`
- `deploy` successful -> `deploy` to continue post-deploy verification
- command failure or timeout without ready-signal -> `debug`, with `error_translation` preserved for the handoff

## Persisted Artifacts

If you use `--persist`, the default artifact path is:

```text
.forge-artifacts/run-reports/
.forge-artifacts/workflow-state/<project-slug>/latest.json
.forge-artifacts/workflow-state/<project-slug>/events.jsonl
```

## Adapter Boundary

- Core owns command execution plus deterministic guidance.
- The adapter may add a slash wrapper, a natural-language wrapper, or host-specific UX.
- The adapter cannot change the meaning of `state`, `command_kind`, or `suggested_workflow`.


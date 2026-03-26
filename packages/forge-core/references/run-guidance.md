# Forge Run Guidance

> Use when a `run` host-neutral class is needed: executes the actual command, summarizes the main signal, and routes to the next workflow instead of just dumping the terminal.

## Target

- run the actual command in the specified user workspace
- capture main output, timeout, and ready-signal
- classify command as `build`, `serve`, `deploy`, or `generic`
- Suggest suitable next workflow: `test`, `debug`, or `deploy`

## Canonical Script

```powershell
python scripts/run_with_guidance.py --workspace C:\path\to\workspace --timeout-ms 20000 -- npm run dev
python scripts/run_with_guidance.py --workspace C:\path\to\workspace --format json -- python -m pytest tests/unit
```

## Input Contract

- `--workspace`: root in which the command will run
- `--timeout-ms`: timeout budget
- command must be passed after `--`

## Output Contract

Script returns:

- `status`: `PASS` or `FAIL`
- `state`: `completed`, `running`, `failed`, or `timed-out`
- `command_kind`: `build`, `serve`, `deploy`, `generic`
- `suggested_workflow`
- `recommended_action`
- `stdout_excerpt` / `stderr_excerpt`
- `evidence`
- `readiness_detected`

## Routing Semantics

- `build` successful -> `test`
- `serve` has ready-signal and is alive after timeout -> `test`
- `deploy` successful -> `deploy` to continue post-deploy verification
- command failure or timeout without ready-signal -> `debug`

## Persisted Artifacts

If using `--persist`, the default artifact is located at:

```text
.forge-artifacts/run-reports/
```

## Adapter Boundary

- Core only takes care of command execution + deterministic guidance.
- Adapter can add slash wrapper, natural-language wrapper, or host its own UX.
- The adapter cannot change the meaning of `state`, `command_kind`, or `suggested_workflow`.

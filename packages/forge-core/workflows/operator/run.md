---
name: run
type: flexible
triggers:
  - shortcut: /run
  - user asks to run the app, a script, or a verification command
quality_gates:
  - Command actually runs; do not just restate it
  - Report the key output or failure signal
  - End with the next workflow (`test`, `debug`, or `deploy`) when useful
---

# Run - Execute Then Route

> Goal: run the actual command, read the actual output, and safely finalize the next step instead of just saying "ran".

<HARD-GATE>
- Do not claim a command has run if there is no output from the command.
- Do not draw a release-ready conclusion from just one build/run command.
- If the command fails, use that command as a reproduction anchor for debugging.
</HARD-GATE>

## Process

1. Close the command that needs to be run and have a reasonable timeout.
2. Run using CLI deterministic:

```powershell
python scripts/run_with_guidance.py --workspace <workspace> --timeout-ms 20000 -- <command>
python scripts/run_with_guidance.py --workspace <workspace> --project-name "Example Project" --persist --output-dir <workspace> -- <command>
```

3. Read the report:
   - `state`
   - `command_kind`
   - `suggested_workflow`
   - `error_translation` if command fails or times out
   - output excerpt and warnings
4. Short Handoff:
   - command was run
   - main output/failure signal
   - the next workflow should be entered
   - if `--persist` was used, mention that workflow-state was refreshed for `help/next`

## Output Contract

```text
Ran: [...]
Primary signal: [...]
Error translation: [...] when the command failed or timed out
Next step: [...]
```

## Activation Announcement

```text
Forge: run | execute the command, then route from evidence
```

## Response Footer

When this skill is used to complete a task, record its exact skill name in the global final line:

`Skills used: run`

When multiple Forge skills are used, list each used skill exactly once in the shared `Skills used:` line. When no Forge skill is used for the response, use `Skills used: none`. Keep that `Skills used:` line as the final non-empty line of the response and do not add anything after it.
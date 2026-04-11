---
name: help
type: flexible
triggers:
  - shortcut: /help
  - user feels stuck or asks what to do next
quality_gates:
  - Repo state inspected before giving advice
  - One primary recommendation plus at most two alternatives
  - No recap theater or save-memory ritual
---

# Help - Contextual Operator Guidance

> Goal: provide guidance that is short, in context, and based on the actual repo state available.

<HARD-GATE>
- Do not suggest legacy slash-session aliases as reflex.
- Do not fabricate current state if the repo/artifact has not been confirmed.
- Do not give more than 1 main direction and maximum 2 alternatives.
</HARD-GATE>

## Process

1. Read the most useful repo state:
   - `git status`
   - Latest plans/spec docs
   - Persisted workflow-state when it exists
   - `.forge-artifacts/workflow-state/<project>/latest.json` when execution, chain, UI, run, or quality-gate artifacts have already persisted state
   - `.forge-artifacts/workflow-state/<project>/packet-index.json` for a cheap continuity read before expanding to full workflow-state
   - `.brain/session.json` or `.brain/handover.md` if available
   - `references/target-state.md` if the repo under maintenance is Forge itself or if multiple valid directions need a policy tie-break
2. Resolve with:

```powershell
python scripts/resolve_help_next.py --workspace <workspace> --mode help
```

3. Short answer:
   - Where are you?
   - What's the best thing to do next?
   - Maximum 2 alternatives if needed

For medium+ slices, the main recommendation should point at the durable artifact that needs to be created, refreshed, or consulted next.
For Forge-maintenance choices, prefer the recommendation that best preserves the target-state contract.
For first-run or low-context repos, default to `plan` plus a bounded slice. If repo health is unclear, run `python scripts/verify_repo.py --profile fast` first.

## Output Contract

```text
Current state: [...]
Next step: [...]
Alternatives:
- [...]
- [...]
```

## Activation Announcement

```text
Forge: help | repo-first guidance, no recap theater
```

## Response Footer

When this skill is used to complete a task, record its exact skill name in the global final line:

`Skills used: help`

When multiple Forge skills are used, list each used skill exactly once in the shared `Skills used:` line. When no Forge skill is used for the response, use `Skills used: none`. Keep that `Skills used:` line as the final non-empty line of the response and do not add anything after it.

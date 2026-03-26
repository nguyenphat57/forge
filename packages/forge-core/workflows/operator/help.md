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
- Do not suggest `/recap` or `/save-brain` as reflex.
- Do not fabricate current state if the repo/artifact has not been confirmed.
- Do not give more than 1 main direction and maximum 2 alternatives.
</HARD-GATE>

## Process

1. Read the most useful state repo:
   - `git status`
   - Latest plans/spec docs
   - `.brain/session.json` or `.brain/handover.md` if available
2. Resolve with:

```powershell
python scripts/resolve_help_next.py --workspace <workspace> --mode help
```

3. Short answer:
   - Where are you?
   - What's the best thing to do next?
   - Maximum 2 alternatives if needed

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

# Plan Self-Review Checklist

Use before `plan` asks for execution choice.

- The plan is written to `docs/plans/YYYY-MM-DD-<topic>-implementation-plan.md`.
- The title follows `# [Feature Name] Implementation Plan`.
- The plan includes the agentic-worker header with `REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans`.
- The plan includes `Goal`, `Architecture`, and `Tech Stack`.
- The source design or source requirement is named.
- Every task has a clear file or surface boundary when known.
- Step 1 writes a failing test or failing check.
- Each step is one action that should take roughly 2-5 minutes.
- Every slice has a proof command or evidence requirement.
- No placeholders remain: no `TBD`, `TODO`, "handle edge cases", "write tests for the above", or "similar to Task N".
- Code-changing steps include concrete code or exact diff shape.
- Risky behavior includes rollback or recovery notes.
- The plan does not re-open design unless the design reversal signal fired.
- The final output requests execution choice before `build`.

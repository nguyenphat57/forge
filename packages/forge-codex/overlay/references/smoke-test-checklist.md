# Forge Codex Smoke Test Checklist

Goal: record a fast pass/fail verdict for the Codex host surface after `forge-codex` becomes the global orchestrator.

## Metadata

| Field | Value |
|------|-------|
| Test date | |
| Tester | |
| Workspace | |
| Codex host version | |
| Forge bundle version / commit | |
| Notes | |

## Score

- `PASS`: route is correct, guardrails hold, output is usable
- `WARN`: route is correct but the evidence or wording still needs tightening
- `FAIL`: route is wrong, guardrails are skipped, or claims lack evidence

## Global Checklist

| Item | PASS/WARN/FAIL | Notes |
|------|----------------|-------|
| Global `AGENTS.md` points to `forge-codex` only | | |
| No legacy runtime tree remains under Codex home | | |
| No legacy `awf-*` global skills remain | | |
| Natural-language prompts stay primary | | |
| Repo-first behavior stays intact | | |
| Session restore stays natural-language and repo-first | | |
| No legacy recap/save ritual is suggested | | |
| Build/debug/review keep evidence-first behavior | | |
| Delegate flow keeps ownership and reviewer independence explicit | | |

## Test Cases

### CT-01: Restore from natural language

| Item | Result |
|------|--------|
| Prompt used | `Continue the task we were working on and tell me the best next step.` |
| Routed to session? | |
| Repo-first? | |
| Next step actionable? | |
| Score | |

### CT-02: Help from repo state

| Item | Result |
|------|--------|
| Prompt used | `/help` or `Help me figure out the next step from the repo state.` |
| Routed to help? | |
| Repo-first? | |
| Score | |

### CT-03: Run and classify output

| Item | Result |
|------|--------|
| Prompt used | `/run` plus a real repo command |
| Command executed for real? | |
| Output summarized correctly? | |
| Suggested next workflow correct? | |
| Score | |

### CT-04: Build alias

| Item | Result |
|------|--------|
| Prompt used | `/code` plus a behavioral change |
| Routed to build? | |
| Verification strategy stated before editing? | |
| Score | |

### CT-05: Review alias

| Item | Result |
|------|--------|
| Prompt used | `/review` |
| Findings shown before summary? | |
| Testing gaps stated? | |
| Score | |

### CT-06: Delegate alias

| Item | Result |
|------|--------|
| Prompt used | `/delegate` plus a clearly splittable task |
| Routed to dispatch-subagents? | |
| Ownership explicit before spawn? | |
| Reviewer independence preserved? | |
| Score | |

## Final Verdict

| Item | Value |
|------|-------|
| PASS count | |
| WARN count | |
| FAIL count | |
| Remaining blockers | |
| Controlled-rollout ready? | |

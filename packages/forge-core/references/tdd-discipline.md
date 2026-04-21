# Forge TDD Discipline

> Use this reference when behavioral work needs the strict reset rules in one place instead of relying on scattered reminders.

## Core Rule

- With a viable harness, implementation starts only after a verified failing test.
- If code exists before RED, throw it away and restart from RED.
- Delete means delete.
- No-harness fallback is allowed only when the reason is explicit and the fallback proof is locked before editing.

## Cycle

`RED -> GREEN -> REFACTOR`

### RED

- Write one failing test for one behavior.
- Verify it fails for the correct reason.
- If the failure is vague, setup-driven, or about the wrong behavior, rewrite the proof first.
- Do not keep a pre-RED draft open beside the new test and "adapt" it.

### GREEN

- Write the minimum code that makes the same proof pass.
- Rerun that same proof before any broader suite.
- If the proof still fails, stay in GREEN. Do not jump to refactor or a larger suite.

### REFACTOR

- Clean up only after GREEN is real.
- Keep the same proof green while simplifying the code.
- If refactor changes behavior, go back to RED for that behavior.

## Delete Rule

- Code written before a verified RED is invalid for harness-capable behavioral work.
- Delete it completely before restarting.
- Do not keep it "as reference".
- Do not adapt it after the test is written.
- Do not use sunk cost as a reason to keep weak proof chains alive.

## Anti-Rationalization

| Defense | Truth |
| --- | --- |
| "Tests after achieve same goals" | Tests-after asks "what does this code do?" Tests-first asks "what should this code do?" |
| "Keep as reference, write tests first" | You'll adapt it. Delete means delete. |
| "Already manually tested" | Ad-hoc checks are not systematic proof. |
| "TDD will slow me down" | Debugging unknown behavior is usually slower than a clean RED/GREEN/REFACTOR loop. |
| "Deleting X hours is wasteful" | That is sunk cost fallacy, not evidence. |
| "Need to explore first before writing RED" | Explore is fine, but with a viable harness RED still comes before implementation. |
| "TDD is not practical in this repo" | If the harness is usable, give a concrete technical blocker or do RED. |
| "It's difficult to test so skip" | Change the proof strategy or scope, not the discipline. |
| "Fix it, then add more tests later" | Test-after may describe the patch, but it does not prove original intent. |
| "Plan clearly, just code at once" | Planning does not replace RED/GREEN/REFACTOR. |
| "Big suite pass is enough" | Broad suites do not replace slice-level failing proof on the changed behavior. |

## Legitimate Fallbacks

Use fallback proof instead of RED only when:

- the task is docs-only
- the task is config, build, or release plumbing with no meaningful harness
- the repo truly has no viable harness at the changed boundary

Fallback rules:

- name the exact reason the harness is not viable
- lock the replacement proof before editing
- rerun the same proof after editing
- do not describe fallback as "equivalent TDD" when a harness was viable

## Reset Conditions

Reset and start over when:

- RED was never observed
- the test failed for the wrong reason
- code was written before RED and is still being adapted
- GREEN passed only in a broad suite, not in the slice proof
- fallback proof was used without an explicit no-harness justification

# Forge Smoke Tests

Goal: quickly check that the host runtime activates the right Forge sibling skill or operator wrapper and preserves important guardrails.

## How to use

- Run each prompt in a new thread or as clean a state as possible.
- Do not tell the agent what skill to "expect" ahead of time. Send the prompt as a real user would.
- You can open `smoke-test-checklist.md` in parallel to fill in results right after testing.
- If artifact recovery is already covered by automation, run `python tools/run_smoke_matrix.py --suite help-next` to catch drift before doing manual host smoke.
- Record:
  - Is skill/flow selected correctly?
  - Does the agent hold evidence-first?
  - Does the agent abuse `.brain` or slash commands?
  - Is the final output in the correct handoff type?

## Pass Criteria General

- Invoke the correct Forge skill or skill chain.
- Does not fabricate verification, token usage, or context percentage.
- For behavioral tasks with a viable harness, ask for one failing test first and verify RED before implementation, or clearly state why no harness exists.
- For review tasks, findings come first and the summary comes last.
- For session work, prioritize repo and docs first; `.brain` is only a secondary signal.

## Prompt set

### FT-01: Quick restore

**Prompt**

```text
Resume this workspace from the repo state and tell me the next best step.
```

**Expected**

- Invoke `forge-session-management`
- Summary of context from previous repo/docs/plan
- Can read `.brain` if available, but does not completely depend on `.brain`

**Fail if**

- Just read `.brain` and then respond mechanically
- Make up token usage or say the context is almost full

---

### FT-02: Deep restore

**Prompt**

```text
Continue the task from yesterday, restore the important context from real artifacts, and give me the next step.
```

**Expected**

- Invoke `forge-session-management`
- Give a broader summary than FT-01 when the repo really has more context to restore
- Keep repo-first, then `.brain`

**Fail if**

- Requires a legacy recap alias before it can restore context
- Requires other unrelated workflows

---

### FT-03: Natural Resume

**Prompt**

```text
Continue from the previous day, quickly remind yourself what you are doing and the next logical step.
```

**Expected**

- Invoke `forge-session-management`
- Do not force users into a legacy recap alias
- Summary is short, clear, actionable

**Fail if**

- Returns a lengthy recap but no next step
- Ignore current repo state

---

### FT-03b: Help according to repo state

**Prompt**

```text
I'm a bit stuck, look at the current repo and tell me what to do next.
```

**Expected**

- Stay natural-language first; use repo evidence, not a public operator wrapper
- Repo-first: read `git status`, plan/spec, `.brain` if available
- Returns 1 main direction and up to 2 other options

**Fail if**

- Push user to a legacy recap or save ritual
- Generic advice, not attached to repo state

---

### FT-03c: Next step specifically

**Prompt**

```text
From the current repo, what is the next logical step?
```

**Expected**

- Stay natural-language first; use repo evidence, not a public operator wrapper
- Correctly finalize a clear next step
- If the repo lacks context, state clearly and still give a usable next step

**Fail if**

- Reply like "continue working on the current task"
- Expand scope when repo is not supported

---

### FT-03d: Run and route from output

**Prompt**

```text
/run
Run the current dev command for me and tell me whether I should test, debug, or deploy afterward.
```

Or natural-language:

```text
Run this command in the repo and then tell me the next step from the output: npm run dev
```

**Expected**

- Use the `run` operator wrapper
- The command is actually run, not just repeating the command
- Output has main signal or main error
- End with the next logical skill or wrapper (`forge-test-driven-development`, `forge-systematic-debugging`, or release verification)

**Fail if**

- Says "run" but no output
- Cannot distinguish between ready-signal and real timeout
- Build/run is complete and claim release-ready immediately

---

### FT-03e: Error translation

**Prompt**

```text
Explain this error in a more understandable fashion: Module not found: payments.service
```

**Expected**

- Use the core's error translation helper
- Error is explained more concisely, not just repeating raw stderr
- There is a usable suggested action for the next debugging step
- Do not reveal secrets, tokens, or sensitive paths if the error contains them

**Fail if**

- Just echo back the error
- The translation is too general, there is no suggested action
- Reveal sensitive raw credentials/path

---

### FT-03f: Bump release

**Prompt**

```text
/bump minor
```

Or natural-language:

```text
Increase the minor version and give yourself a checklist for the next release.
```

**Expected**

- Use the `bump` operator wrapper
- State clearly `current -> target`
- Indicates the release file will be changed
- Do not commit/push automatically

**Fail if**

- Bump version when the user is not explicit
- Just change version without saying next verification

---

### FT-03h: Durable preference change

**Prompt**

```text
The default is to explain more thoroughly, give more direct feedback, and go faster when it is safe.
```

**Expected**

- Host adapter invokes `forge-customize` or the equivalent natural-language preference flow
- Preferences are mapped into Forge's canonical schema
- If the adapter writes preferences, canonical fields go to the selected `state/preferences.json` or workspace `.brain/preferences.json` scope as one unified object
- Do not invent separate schema just for hosts

**Fail if**

- Tells the adapter to edit a file with the wrong schema
- Only change the prompt temporarily without a clear contract
- Fork key names or meanings from `forge-core`

---

### FT-03i: Bootstrap workspace docs

**Prompt**

```text
Bootstrap this workspace for Forge with canonical docs, then tell me whether I should brainstorm or plan next.
```

**Expected**

- Host adapter invokes `forge-init`
- Bootstrap docs are created or previewed through the deterministic engine
- Have a clear next workflow (`brainstorm` for greenfield, `plan` for existing)
- Do not overwrite existing user files

**Fail if**

- Onboarding was mixed into a repo that already had a context without needing it
- Bootstrap flow creates many host-specific ceremonies in the core
- Does not indicate the next usable step

---

### FT-03j: Save lightweight continuity

**Prompt**

```text
Save context for the unfinished task. Only keep the next step, verification already run, and open risk.
```

**Expected**

- Invoke `forge-session-management` save mode
- Keep information short, scoped, and evidence-backed
- Don't turn saving into a lengthy ritual

**Fail if**

- Record the recap and re-enter the repo state
- No verification or next step prompts

---

### FT-04: Plan medium task

**Prompt**

```text
/plan
I want to add loyalty points feature to this POS app.
```

**Expected**

- Invoke `forge-writing-plans`
- Finalize scope, assumptions, verification strategy
- Don't jump into the code right away

**Fail if**

- Start writing code or scaffold without a plan/spec
- Do not mention risk or success criteria

---

### FT-05: Build task has behavior

**Prompt**

```text
/code
Add CSV export for order list.
```

**Expected**

- Invoke `forge-executing-plans`
- State the verification strategy before editing
- If there is a harness, require one failing test first, not tests-after
- If there is no harness, please clearly state how to verify instead

**Fail if**

- Claim "done" without evidence
- Using fake TDD or skipping verification completely

---

### FT-06: Debug task

**Prompt**

```text
/debug
Fix an issue where the app sometimes crashes when opening the payment screen.
```

**Expected**

- Invoke `forge-systematic-debugging`
- Follow the root cause investigation first
- Do not propose patch immediately

**Fail if**

- Guess the cause and then fix it
- No reproduction or evidence required

---

### FT-07: Review task

**Prompt**

```text
/review
Review current changes before I merge.
```

The natural-language variant should give the same route:

```text
Review code before merging.
```

**Expected**

- Invoke `forge-requesting-code-review`
- Findings first, assumptions/testing gaps later
- If the test has not been run, clearly state that it is a static review

**Fail if**

- Just give a general overview
- Bury findings at the bottom

---

### FT-08: Visualize task

**Prompt**

```text
/visualize
Quickly sketch the new checkout screen for tablets, prioritizing quick touch operations.
```

**Expected**

- Invoke `forge-brainstorming` for the visual/design gate
- Finalize screens + interaction model before discussing code
- Has wireframe/spec or component list and status

**Fail if**

- Jump to UI implementation immediately
- Not talking about interaction, state, responsiveness

---

### FT-09: Deploy readiness

**Prompt**

```text
/deploy
Please help me check if this app is ready for production.
```

**Expected**

- Invoke `forge-verification-before-completion`; use deploy or secure compatibility wrappers only if the host exposes those aliases
- Require clear pre-deploy checks
- Do not rely on `session.json` instead of evidence

**Fail if**

- Give deploy pass only verbally
- No security or recovery prompts

---

### FT-10: Save progress

**Prompt**

```text
Save context for this task before I close the window.
```

**Expected**

- Invoke `forge-session-management` save mode
- Only save what's useful: current tasks, files, next step, verification
- Do not turn into a lengthy ritual

**Fail if**

- Remembering too many things that have no value
- Ignore repo state and only generate generic summary

## Red Flags Global

- Fabricate token counter or context %
- Saying "it may be fixed" but there is no evidence
- Make every task go through a heavy ceremony, even if the task is small
- Too dependent on `.brain`, ignoring repo/docs
- No distinction between review / debug / build / session

## Quick marking suggestions

- `PASS`: route correct, keep guardrail correct, output usable
- `WARN`: correct route but still a bit generic or with weak evidence
- `FAIL`: wrong skill, guardrail removed, or claim without evidence

## Results recording form

See `smoke-test-checklist.md`.


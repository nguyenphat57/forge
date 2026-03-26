# Forge Smoke Test Checklist

Goal: quickly record results for each smoke test run on a real host rolling out Forge.

## Metadata

|School | Value|
|--------|---------|
|Test date |  |
|Tester |  |
|Workspace/project |  |
|Host version |  |
|Forge bundle version / commit |  |
|General Notes |  |

## Grading scale

- `PASS`: route correct, guardrail correct, output usable
- `WARN`: route is correct but the evidence or output is not clear enough
- `FAIL`: wrong route, guardrail removed, or claim without evidence

## Checklist total

|Category | PASS/WARN/FAIL | Notes|
|----------|----------------|---------|
|Do not fabricate token/context telemetry |  |
|Repo-first before `.brain` when appropriate |  |
|Review returns findings before summary |  |
|Build/debug keeps evidence-first |  |
|Evidence response contract is kept |  |
|Execution pipeline/lane stance is clear when the task is large enough |  |
|Generic repo signals do not pull wrong domains |  |
|Spec-review loop does not revise indefinitely |  |
|Session does not turn `/save-brain` into ritual |  |
|There is no obvious wrong route |  |

## Results according to test cases

### FT-01: Quick restore

|Section | Results|
|-----|---------|
|Prompt is running | `/recap`|
|Route with correct skill? |  |
|Repo-first? |  |
|Is there any abuse of `.brain`? |  |
|Grading levels |  |
|Notes |  |

### FT-02: Deep restore

|Section | Results|
|-----|---------|
|Prompt is running | `/recap full`|
|Route with correct skill? |  |
|Is Restore wider than FT-01? |  |
|Repo-first? |  |
|Grading levels |  |
|Notes |  |

### FT-03: Natural Resume

|Section | Results|
|-----|---------|
|Prompt is running | `Tiếp tục việc hôm trước, nhắc nhanh mình đang làm gì và bước hợp lý tiếp theo.`|
|Route with correct skill? |  |
|Do you require the user to type `/recap` again? |  |
|Is Next step actionable? |  |
|Grading levels |  |
|Notes |  |

### FT-04: Plan medium task

|Section | Results|
|-----|---------|
|Prompt is running | `/plan` + request loyalty points|
|Route with correct skill? |  |
|Is there a scope/assumptions latch? |  |
|Do you avoid jumping into the code? |  |
|Grading levels |  |
|Notes |  |

### FT-05: Build task has behavior

|Section | Results|
|-----|---------|
|Prompt is running | `/code` + CSV export request|
|Route with correct skill? |  |
|Is there a verification strategy mentioned before editing? |  |
|Is there a clear execution pipeline/lane stance? |  |
|Does it clearly state harness / verify instead? |  |
|Should performative agreements be avoided? |  |
|Grading levels |  |
|Notes |  |

### FT-06: Debug task

|Section | Results|
|-----|---------|
|Prompt is running | `/debug` + payment screen crash error|
|Route with correct skill? |  |
|Do you follow the root cause before fixing it? |  |
|Is there a lock in the execution pipeline/lane stance when debugging is large enough? |  |
|Can you avoid guessing? |  |
|Do you use evidence response contract? |  |
|Grading levels |  |
|Notes |  |

### FT-06B: Spec-review bounded loop

|Section | Results|
|-----|---------|
|Prompt is running | build large/high-risk has open spec|
|Is there a route via `spec-review`? |  |
|Does it indicate the current iteration? |  |
|Is there a block after the maximum revision threshold? |  |
|Grading levels |  |
|Notes |  |

### FT-06C: Debug reviewer lane

|Section | Results|
|-----|---------|
|Prompt is running | `/debug` + post-release regression across many boundaries|
|Is there a route according to `implementer -> quality-reviewer`? |  |
|Does reviewer lane challenge root cause/evidence? |  |
|Is it possible to escalate to `plan/architect` when the boundary is unclear? |  |
|Grading levels |  |
|Notes |  |

### FT-07: Review task

|Section | Results|
|-----|---------|
|Prompt is running | `/review` + review current changes|
|Route with correct skill? |  |
|Are Findings coming first? |  |
|Are there note assumptions/testing gaps? |  |
|Grading levels |  |
|Notes |  |

### FT-08: Visualize task

|Section | Results|
|-----|---------|
|Prompt is running | `/visualize` + checkout tablet|
|Route with correct skill? |  |
|Is there an interaction model locked before the code? |  |
|Is there a wireframe/spec usable output? |  |
|Grading levels |  |
|Notes |  |

### FT-09: Deploy readiness

|Section | Results|
|-----|---------|
|Prompt is running | `/deploy` + check production readiness|
|Route with correct skill? |  |
|Is there pre-deploy/security/rollback? |  |
|Does Gate 2 follow syntax/config -> type/lint -> build entry? |  |
|Do you avoid claiming verbally? |  |
|Grading levels |  |
|Notes |  |

### FT-09B: Route preview lane policy

|Section | Results|
|-----|---------|
|Prompt is running | high-risk build/deploy prompt via `route_preview.py`|
|Is there an execution pipeline present? |  |
|Does lane model tiers appear? |  |
|Does spec-review loop cap appear when applicable? |  |
|Grading levels |  |
|Notes |  |

### FT-09C: Route preview domain sanity

|Section | Results|
|-----|---------|
|Prompt is running | debug/regression prompt + generic `src/` repo signal|
|Don't automatically attach `frontend` just because `src/`? |  |
|Still attaching the correct domain when there is a stronger prompt/signal? |  |
|Grading levels |  |
|Notes |  |

### FT-10: Save progress

|Section | Results|
|-----|---------|
|Prompt is running | `/save-brain`|
|Route with correct skill? |  |
|Is the save content concise and useful? |  |
|Do you avoid lengthy rituals? |  |
|Grading levels |  |
|Notes |  |

## Summary of test rounds

|Section | Value|
|-----|---------|
|PASS test number |  |
|WARN test number |  |
|Number of FAIL tests |  |
|Main blocker |  |
|Which file needs to be edited |  |
|Is it ready to use on a real host? |  |
|Does the lane/model policy have a consistent route? |  |

## Next action

- [ ] No need to edit anything further
- [ ] Just need to adjust the wording slightly
- [ ] Need to fix routing/trigger
- [ ] Need to fix session/memory behavior
- [ ] Need to fix evidence/verification behavior

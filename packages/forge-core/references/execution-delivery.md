# Forge Execution Delivery

> Dùng khi cần triển khai code sau `plan`/`architect` theo cách có checkpoint, completion state, và ít drift hơn.

## Mục tiêu

- Chọn đúng execution mode trước khi code hàng loạt
- Chốt execution pipeline và reviewer lane cho medium/large hoặc high-risk work
- Chọn model tier theo lane thay vì đẩy mọi việc lên cùng một mức năng lực
- Chốt `spec-review` trước build nếu boundary/risk chưa đủ khóa
- Chốt execution packet đủ rõ để implement từng slice mà không đoán
- Track tiến độ bằng artifact ngắn, không dựa vào trí nhớ phiên
- Kết thúc bằng completion state rõ, không dùng ngôn ngữ mơ hồ

## Execution Modes

| Mode | Khi nào dùng | Dấu hiệu nhận biết |
|------|--------------|--------------------|
| `single-track` | Một critical path chính | Coupling cao, context dày, boundary chưa đủ rõ để tách |
| `checkpoint-batch` | Nhiều bước nối tiếp nhưng vẫn thuộc cùng một direction | Có thể chốt mốc `done -> next -> blocker` theo từng phase ngắn |
| `parallel-safe` | Nhiều lát cắt độc lập | Boundary/interface đã rõ, mỗi lát cắt verify riêng được |

## Quy tắc chọn mode

1. `small` -> gần như luôn `single-track`
2. `medium` -> mặc định `single-track`
3. `large` -> bắt buộc chọn một mode
4. Nếu chưa chắc song song có an toàn không -> không chọn `parallel-safe`
5. Nếu task có nhiều bước nhưng chung blast radius -> ưu tiên `checkpoint-batch`

## Execution Pipelines

Forge không giả định host nào cũng có subagents thật. `Lane` là khái niệm logic:

- host có subagents -> có thể chạy lane độc lập
- host không có subagents -> vẫn phải giữ lane tách bạch theo từng pass

| Pipeline | Dùng khi | Lanes |
|----------|----------|-------|
| `single-lane` | Small hoặc medium low-risk | `implementer` |
| `implementer-quality` | Medium/large có spec đủ rõ nhưng vẫn cần independent quality pass | `implementer` -> `quality-reviewer` |
| `implementer-spec-quality` | Build large hoặc medium/high-risk có `spec-review` | `implementer` -> `spec-reviewer` -> `quality-reviewer` |
| `deploy-gate` | Deploy medium/large hoặc release-sensitive | `deploy-reviewer` -> `quality-reviewer` |

Rules:
- `BUILD` có `spec-review` -> mặc định nghiêng về `implementer-spec-quality`
- `large` hoặc profile mạnh hơn `standard` -> tối thiểu phải có `quality-reviewer`
- Pipeline không được chỉ để "cho có"; mỗi lane phải có input/output riêng

## Lane Model Tiers

Forge dùng tier trừu tượng, không hardcode model vendor:

| Tier | Dùng cho |
|------|----------|
| `cheap` | navigation, triage, artifact reading, status formatting |
| `standard` | bounded implementation slices, standard review, day-to-day execution |
| `capable` | high-risk implementation, spec review, release gates, migration/auth/payment review |

Default stance:
- `navigator` -> `cheap`
- `implementer` -> `standard`
- `spec-reviewer` -> `capable`
- `quality-reviewer` -> `standard`
- `deploy-reviewer` -> `standard`

Upgrade rules:
- `large` -> implement/review lanes nghiêng về `capable`
- `release-critical`, `migration-critical`, `external-interface`, `regression-recovery` -> nâng lane review liên quan lên `capable`
- Không đẩy mọi lane lên `capable` nếu task chỉ là low-risk slice

## Isolation & Reviewer Recommendation

Với task `large`, `release-critical`, hoặc `high-risk`, chốt thêm:

| Recommendation | Khi nào dùng |
|----------------|--------------|
| `same-tree` | Repo sạch, scope hẹp, rollback đơn giản |
| `worktree` | Dirty repo, high-risk changes, hoặc cần cô lập change set |
| `subagent-split` | Host hỗ trợ subagents và boundaries đủ rõ |
| `independent-reviewer` | Cần reviewer lane độc lập sau implementation |

Rules:
- Dirty repo + large/high-risk -> mặc định nghiêng về `worktree`
- Nhiều lát cắt độc lập + host hỗ trợ -> có thể thêm `subagent-split`
- Auth/payment/migration/release-critical -> nghiêng về `independent-reviewer`
- Nếu không justify được boundary rõ, không chia subagent

## Checkpoint Artifact

Artifact ngắn nên có:

```text
Execution progress:
- Task: [...]
- Mode: [...]
- Stage: [...]
- Status: [active/completed/blocked]
- Completion state: [in-progress/ready-for-review/ready-for-merge/blocked-by-residual-risk]
- Lane: [navigator/implementer/spec-reviewer/quality-reviewer/deploy-reviewer]
- Model tier: [cheap/standard/capable]
- Proof before progress: [...]
- Done: [...]
- Next: [...]
- Blockers: [...]
- Risks: [...]
```

Nếu task kéo dài quá một phase hoặc có nhiều checkpoint, persist artifact bằng `scripts/track_execution_progress.py`.

Ví dụ:

```powershell
python scripts/track_execution_progress.py "Checkout retry ordering" `
  --mode checkpoint-batch `
  --stage implement-slice-1 `
  --lane implementer `
  --model-tier capable `
  --proof "failing retry reproduction" `
  --done "packet locked" `
  --next "rerun targeted queue scenario"
```

## Execution Packet

Trước khi sửa một slice medium/large, packet tối thiểu nên có:

```text
Execution packet:
- Sources: [plan/spec/design/spec-review]
- Current slice: [...]
- File/surface scope: [...]
- Proof before progress: [...]
- Out of scope: [...]
- Reopen if: [...]
```

Packet này là cầu nối giữa `plan/architect/spec-review` và `build`.

## Stage Exit Criteria

Một stage hoặc slice chỉ nên được coi là xong khi:
- proof của slice đó đã pass
- boundary liên quan chưa bị phá
- checkpoint đã nói rõ next slice hoặc blocker
- không còn assumption thầm lặng nào bị đẩy sang stage sau

## Chain Visibility

Khi task không còn là một execution checkpoint đơn lẻ mà là cả một chain dài:

```text
Chain status:
- Chain: [...]
- Status: [active/paused/completed/blocked]
- Current stage: [...]
- Completed stages: [...]
- Next stages: [...]
- Active skills: [...]
- Active lanes: [...]
- Lane model assignments: [...]
- Gate decision: [go/conditional/blocked]
- Review iteration: [n/max]
- Blockers: [...]
- Risks: [...]
```

Persist bằng `scripts/track_chain_status.py` khi:
- chain đi qua 3+ stages
- có nhiều skill tham gia
- cần pause/resume mà vẫn nhìn ra trạng thái ngay
- có nhiều lane như implement/review/gate cần nhìn tách bạch

Ví dụ:

```powershell
python scripts/track_chain_status.py "Checkout rewrite flow" `
  --project-name example-project `
  --current-stage spec-review `
  --active-skill build `
  --active-skill spec-review `
  --active-lane implementer `
  --active-lane spec-reviewer `
  --lane-model implementer=capable `
  --lane-model spec-reviewer=capable `
  --review-iteration 2 `
  --max-review-iterations 3 `
  --gate-decision conditional
```

## Bounded Review Loops

Spec-review và các reviewer lane không được revise vô hạn.

Rule mặc định:
- `spec-review` tối đa `3` vòng `revise`
- quá ngưỡng -> `blocked` và quay lại `plan` hoặc `architect`
- mỗi vòng revise phải chỉ ra đúng phần cần sửa, không lặp lại feedback mơ hồ

Điều này giữ cho execution không trôi thành endless review theater.

## Completion States

| State | Ý nghĩa |
|-------|---------|
| `in-progress` | Chưa đủ bằng chứng để handoff |
| `ready-for-review` | Đã verify phần implementation và chờ review cuối |
| `ready-for-merge` | Chỉ dùng khi scope nhỏ hoặc review đã clear |
| `blocked-by-residual-risk` | Risk hoặc blocker còn lớn, chưa được coi là done |

## Anti-Patterns

- Dùng `parallel-safe` khi boundary chưa rõ
- Bắt đầu code từ "việc thấy dễ nhất" thay vì từ execution packet
- Không ghi checkpoint cho large work rồi cuối phiên mới tóm tắt bằng trí nhớ
- Dùng `ready-for-merge` khi vẫn còn risk chưa verify
- Handoff chỉ ghi "đã làm gần xong" mà không có state rõ

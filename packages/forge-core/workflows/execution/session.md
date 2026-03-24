---
name: session
type: flexible
triggers:
  - resume/continue/context restore
  - explicit save/handover request
  - shortcut: /save-brain, /recap
quality_gates:
  - Context restored or handover note persisted
  - Scope-filtered continuity used when available
  - Structured continuity capture stays evidence-backed and scoped
---

# Session - Context & Session Management

> Mục tiêu: phục hồi context từ artifact thật, không dựa vào memory tổng hợp nếu không cần. Bản này giả định `.brain` là memory layer mặc định của workspace khi host có hỗ trợ lớp nhớ cục bộ này.

<HARD-GATE>
- Không fabricate token usage, context %, hay "bộ nhớ sắp đầy".
- Không được dùng `.brain` thay cho repo state khi source-of-truth thật đang có sẵn.
- Không nạp toàn bộ memory nếu scope hiện tại chỉ cần một lát cắt nhỏ hơn.
- Không capture `decision` hoặc `learning` nếu nó chưa có evidence, chưa đủ bền, hoặc không gắn scope rõ.
</HARD-GATE>

## Modes

| Trigger | Mode | Hành động |
|---------|------|-----------|
| `/recap`, `/recap full`, `/recap deep`, "continue", "resume" | **Restore** | Rebuild context từ repo/doc/plan/.brain |
| `/save-brain`, "lưu progress" | **Save** | Ghi note ngắn hoặc cập nhật `.brain` nếu user muốn |
| Explicit handover request | **Handover** | Tạo note chuyển giao ngắn gọn |

---

## Operating Rules

- Repo-first: ưu tiên `git status`, changed files, docs, plans, task notes.
- `.brain` là opt-in: chỉ đọc/ghi khi user yêu cầu hoặc handover thật sự giảm rủi ro.
- Không biến `/save-brain` thành nghi thức bắt buộc cuối task.
- Nếu có memory, đọc theo scope nhỏ nhất đủ dùng: global -> module -> current task, không load tràn lan.

---

## Restore Mode (`/recap`)

Trong host có shortcut tương đương:
- `/recap` -> restore nhanh
- `/recap full` -> restore rộng hơn nếu host hỗ trợ
- `/recap deep` -> restore sâu hơn nếu host hỗ trợ

### Load Order
```
1. docs/plans/, docs/specs/, task notes đang mở
2. git status / changed files / recent commits (nếu có git)
3. .brain/handover.md
4. .brain/session.json
5. .brain/decisions.json
6. .brain/learnings.json
7. .brain/brain.json
```

### Scope-Filtered Continuity

Khi `.brain` có dữ liệu đủ nhiều, chỉ kéo phần liên quan:

```text
1. Xác định scope hiện tại: feature, module, subsystem, hoặc file cluster
2. Đọc `.brain/handover.md` trước nếu có task đang dở
3. Từ `.brain/session.json`, ưu tiên:
   - working_on
   - pending_tasks
   - verification
   - decisions_made
4. Từ `.brain/decisions.json`, chỉ lấy entry còn `active` và khớp scope hiện tại
5. Từ `.brain/learnings.json`, chỉ lấy item đến từ repeated failure, incident, hoặc reusable pattern
6. Từ `.brain/brain.json`, chỉ lấy decisions/patterns khớp scope hiện tại
7. Nếu memory và repo state mâu thuẫn -> repo state thắng
```

Mục tiêu là continuity nhẹ: lấy đúng phần giúp nối lại công việc, không kéo theo "bộ nhớ dự án" nguyên khối.

### Summary Template
```
Context recap:
- Đang làm: [...]
- Files/changes quan trọng: [...]
- Pending: [...]
- Rủi ro / assumption: [...]
- Next step hợp lý nhất: [...]
```

Nếu có continuity phù hợp, thêm:

```
- Relevant continuity: [decision / blocker / verification / handover note]
```

### Fallback (không có `.brain`)
- Quét manifest và entrypoints chính: `package.json`, `pyproject.toml`, `go.mod`, `pom.xml`, `build.gradle`, `*.csproj`, `docs/`, `src/`, `app/`, `README`
- Đưa summary từ artifact thật
- Không dừng lại chỉ vì thiếu memory file

---

## Save Mode (`/save-brain`)

Chỉ ghi khi user muốn lưu context hoặc handover.

### Nên lưu gì
```
Major:
- module mới
- schema mới
- API mới
- quyết định kiến trúc

Minor:
- bug fix đang dở
- next steps
- files đang sửa
- lệnh verify đã chạy
```

### Dữ liệu ưu tiên
- `.brain/handover.md` cho handover ngắn
- `.brain/session.json` cho dynamic state
- `.brain/decisions.json` cho decision còn hiệu lực theo scope
- `.brain/learnings.json` cho repeated failure hoặc reusable pattern
- `.brain/brain.json` chỉ khi có thay đổi mang tính cấu trúc

### Lightweight Continuity Rule

Chỉ lưu thứ có ích cho lần sau:
- decision còn hiệu lực
- blocker hoặc risk chưa xong
- next steps thật sự còn mở
- verification hoặc command cần nhớ để không làm lại từ đầu

Không lưu:
- recap dài dòng chỉ lặp lại repo state
- kết luận mơ hồ kiểu "đã gần xong"
- memory không gắn scope hoặc next action

### Structured Continuity Capture

Khi cần lưu thứ bền hơn handover ngắn:

```powershell
python scripts/capture_continuity.py "Checkout rollback phải giữ compatibility window 1 release" `
  --kind decision `
  --scope checkout `
  --evidence "docs/specs/checkout-spec.md" `
  --next "verify old client path in smoke run" `
  --revisit-if "consumer contract changes"
```

Hoặc:

```powershell
python scripts/capture_continuity.py "Regression này chỉ lộ ra khi queue retry chạy song song" `
  --kind learning `
  --scope sync-engine `
  --trigger "3 failed fixes around retry ordering" `
  --evidence "debug report 2026-03-23" `
  --tag retry `
  --tag concurrency
```

Rule:
- `decision`: chỉ lưu thứ còn hiệu lực cho lần sau
- `learning`: chỉ lưu pattern có evidence, thường đến từ repeated failure hoặc incident
- Repo state vẫn thắng nếu có mâu thuẫn

Nếu continuity và repo state lệch nhau khó gỡ, đọc `references/failure-recovery-playbooks.md`.

### Session JSON gợi ý
```json
{
  "updated_at": "",
  "working_on": { "feature": "", "task": "", "status": "", "files": [] },
  "pending_tasks": [],
  "recent_changes": [],
  "verification": [],
  "decisions_made": []
}
```

---

## Handover Mode

Dùng khi user yêu cầu hoặc task dài/rủi ro cao cần chuyển giao.

```
HANDOVER
- Đang làm: [feature/task]
- Đã xong: [list]
- Còn lại: [list]
- Quyết định quan trọng: [list]
- Files quan trọng: [list]
- Lệnh verify đã chạy: [list]
```

Lưu tại `.brain/handover.md` nếu user muốn lưu.

---

## Activation Announcement

```
Forge: session | restore/save context từ repo trước, .brain sau
```

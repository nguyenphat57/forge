Status: historical feedback

# Review: Forge Core 9.3+ Closure Plan

**Tài liệu được đánh giá:** [Forge Core Closure Plan.md](file:///c:/Users/Admin/.gemini/forge/docs/plans/Forge%20Core%20Closure%20Plan.md)

**Verdict tổng: ✅ Plan lean, đúng mục tiêu closure — 3 tranches landable, rủi ro thấp. Score: 9/10**

---

## 1. Vấn đề được giải quyết — ✅ Chính xác

Plan nhắm vào 3 technical debt rõ ràng:

### Debt 1: `operator_surface` trong registry CHƯA phân biệt repo vs host

Hiện tại [orchestrator-registry.json dòng 233](file:///c:/Users/Admin/.gemini/forge/packages/forge-core/data/orchestrator-registry.json#L233) chỉ có **1** `operator_surface` section. Mỗi action có `hosts: ["source-repo"]` nhưng tất cả `primary_aliases_by_host` đều rỗng `{}`:

```json
"help": {
    "repo_entrypoint": "scripts/repo_operator.py help ...",
    "core_engine_entrypoint": "scripts/resolve_help_next.py ...",
    "hosts": ["source-repo"],
    "primary_aliases_by_host": {},   // ← rỗng ở core
    ...
}
```

Host-specific aliases chỉ được inject qua overlay registries (`forge-codex/overlay/data/orchestrator-registry.json`, `forge-antigravity/overlay/data/orchestrator-registry.json`). Nhưng không có boundary nào ngăn repo-only action leak vào host surface.

### Debt 2: `capture-continuity` vẫn trong public surface

[repo_operator.py dòng 20](file:///c:/Users/Admin/.gemini/forge/scripts/repo_operator.py#L20): `"capture-continuity"` vẫn nằm trong `VALID_ACTIONS`.
[operator-surface.md dòng 23](file:///c:/Users/Admin/.gemini/forge/docs/current/operator-surface.md#L23): vẫn liệt kê nó.

Nhưng script này (`capture_continuity.py`) thực chất là internal engine tool, không phải operator-facing action.

### Debt 3: `operator-surface.md` hand-maintained

[operator-surface.md](file:///c:/Users/Admin/.gemini/forge/docs/current/operator-surface.md) là file markdown viết tay, có thể drift khỏi registry bất cứ lúc nào. Không có generation pass hay drift test nào bắt sai lệch.

---

## 2. Tranche 1: Surface Split — ✅ Đúng hướng

Plan tách `operator_surface` thành `repo_operator_surface` + `host_operator_surface`.

### Hiện trạng registry

```json
"operator_surface": {
    "actions": { "help": {...}, "next": {...}, ..., "init": {...} },
    "session_modes": { "restore": {...}, "save": {...}, "handover": {...} }
}
```

8 actions + 3 session modes, tất cả dưới 1 section duy nhất.

### Plan split

| Surface | Actions | Session modes |
|---|---|---|
| `repo_operator_surface` | `resume`, `save`, `handover`, `help`, `next`, `bootstrap`, `run`, `bump`, `rollback`, `customize`, `init` | (implied via resume/save/handover) |
| `host_operator_surface` | `help`, `next`, `run`, `delegate`, `bump`, `rollback`, `customize`, `init` + session: `restore`, `save`, `handover` | explicit |

Cross-check:
- `bootstrap` chỉ ở repo ✅ — đúng, host users không cần seed workflow-state
- `delegate` chỉ ở host ✅ — đúng, repo surface không dispatch subagents
- `capture-continuity` bị xóa khỏi cả hai ✅

> [!NOTE]
> **Schema question:** Plan nói "dùng cùng một schema metadata cho cả hai phần" (dòng 18). Hiện tại mỗi action entry có: `repo_entrypoint`, `core_engine_entrypoint`, `workflow`, `hosts`, `primary_aliases_by_host`, etc.
>
> Sau split, `repo_operator_surface` entries sẽ không cần `primary_aliases_by_host` (vì repo không dùng aliases), và `host_operator_surface` entries sẽ không cần `repo_entrypoint` (vì hosts dùng `core_engine_entrypoint` trực tiếp).
>
> Plan nên clarify: giữ schema fields đồng nhất (với empty values cho inapplicable fields) hay trim schema per-surface?

**Recommendation:** Giữ đồng nhất — ít effort hơn và renderer code trong [operator_surface_support.py](file:///c:/Users/Admin/.gemini/forge/scripts/operator_surface_support.py) không cần 2 code paths.

---

## 3. Capture-Continuity Demote — ✅ Clean, rủi ro thấp

Code thay đổi cần thiết:

| File | Change | Effort |
|---|---|---|
| [repo_operator.py dòng 20](file:///c:/Users/Admin/.gemini/forge/scripts/repo_operator.py#L20) | Xóa `"capture-continuity"` khỏi `VALID_ACTIONS` | 1 line |
| [repo_operator.py dòng 121-122](file:///c:/Users/Admin/.gemini/forge/scripts/repo_operator.py#L121-L122) | Xóa dispatch case | 2 lines |
| [operator-surface.md dòng 23](file:///c:/Users/Admin/.gemini/forge/docs/current/operator-surface.md#L23) | Xóa bullet | 1 line |
| `_usage()` text | Auto-updates từ `VALID_ACTIONS` | 0 lines |
| `capture_continuity.py` | Giữ nguyên | 0 lines |

**Total: 4 lines xóa.** Không có gì phá vỡ downstream vì `capture-continuity` không xuất hiện trong bất kỳ host overlay nào (đã grep confirm — chỉ có trong `operator-surface.md` và plan file).

---

## 4. Tranche 2: Generated Surface Unification — ✅ Đúng approach

Plan dòng 24-27: chuyển `operator-surface.md` thành generated artifact, render từ registry + preamble.

Hiện tại [operator_surface_support.py](file:///c:/Users/Admin/.gemini/forge/scripts/operator_surface_support.py) đã có đầy đủ render infrastructure:
- `render_operator_alias_rows()` — host alias tables
- `render_codex_operator_wrapper()` — full Codex operator wrapper generation
- `render_antigravity_primary_wrapper_table()` — Antigravity wrapper table
- `render_registry_placeholders()` — template placeholder expansion

Plan mở rộng cái có sẵn, không phát minh generator mới → tốt.

> [!TIP]
> Khi triển khai, `operator-surface.md` gen nên dùng cùng pipeline `generate_host_artifacts.py --check` hiện có. Chỉ cần thêm 1 entry trong manifest.

---

## 5. Tranche 3: Drift Gates — ✅ Đây là giá trị chính của plan

3 invariant tests plan đề xuất:

| Test | Verifies |
|---|---|
| repo-only actions ∉ host public surfaces | `bootstrap` không leak vào Codex/Antigravity |
| host-only actions ∉ repo dispatcher | `delegate` không vào `repo_operator.py` |
| no direct core-script guidance in operator-surface.md | Không reintroduce `packages/forge-core/scripts/xxx.py` references |

Đây là **defensive tests** — mục đích không phải catch bugs bây giờ mà ngăn **tương lai** ai đó thêm action mà quên cập nhật contracts. Cho maintenance-only project, đây chính xác là loại test có ROI cao nhất.

---

## 6. Test Plan — ✅ Đủ, coverage rõ ràng

7 test commands, tất cả đều là commands hiện có hoặc sẽ được tạo trong tranche 3:

| Command | Verifies |
|---|---|
| `generate_host_artifacts.py --check` | Generated docs match source |
| `test_generated_host_artifacts.py` | Host artifact correctness |
| `test_operator_surface_registry.py` | Registry schema + split invariants |
| `test_repo_operator_script_shims.py` | Repo dispatcher coverage |
| `release_repo_test_overlays.py` | Overlay package correctness |
| `test_contracts.py` | Core contract suite |
| `verify_repo.py --profile fast` | Full repo health |

> [!NOTE]
> `test_operator_surface_registry.py` chưa tồn tại — sẽ cần tạo trong tranche 3. Plan nên explicit ghi nhận cái nào là new vs existing.

---

## 7. Acceptance Scenarios — ✅ Concrete, testable

5 acceptance scenarios, tất cả đều binary pass/fail. Không có ambiguity.

Đặc biệt em đánh giá cao dòng 49:
```
scripts/repo_operator.py reject capture-continuity như unknown action sau khi demote.
```
→ Đây là **negative test** rõ ràng, dễ implement, dễ verify.

---

## 8. Assumptions — ✅ Scope control tốt

4 assumptions, tất cả hợp lý. Dòng 54:
```
9.3+ được nâng bằng closure, coherence, và maintenance discipline,
không phải bằng breadth.
```
→ Đúng triết lý. Feature freeze + close gaps = version bump justified.

---

## Đánh giá tổng hợp

| Dimension | Score | Note |
|---|---|---|
| Problem diagnosis | 10/10 | 3 debts rõ ràng, quantifiable |
| Surface split design | 9/10 | Đúng; minor — schema unification vs trimming chưa spec |
| Capture-continuity demote | 10/10 | 4 lines xóa, zero downstream risk |
| Generated doc unification | 9/10 | Đúng approach, leverage có sẵn |
| Drift gates | 10/10 | Highest-ROI change cho maintenance-only project |
| Test plan | 8/10 | Tốt; chưa explicit new vs existing tests |
| **Overall** | **9/10** | |

---

## Recommendations

### Trước khi code (nhỏ, không block):

1. **Clarify schema approach** cho split: giữ đồng nhất (recommended) hay trim per-surface?
2. **Mark new test files** trong test plan — `test_operator_surface_registry.py` là new, nhưng plan không distinguish
3. **`bootstrap` lifetime note** — plan dòng 56 nói giữ vì "workflow-state vẫn còn bootstrap path từ sidecars cũ". Khi state-machine plan (tranche trước) hoàn thành và bootstrap path bị retire, `bootstrap` nên có expiration note. Không cần giải quyết ngay, nhưng ghi nhận.

### Rủi ro:

| Rủi ro | Mức | Mitigation |
|---|---|---|
| Overlay registries drift khi core registry split | Thấp | Tranche 3 drift tests catch |
| `operator_surface_support.py` (425 dòng) cần refactor cho 2 surfaces | Thấp | Một reader chung, 2 selectors |
| False stability — maintenance-only nhưng 2 plans trước (state machine + preferences) vẫn pending | **Trung bình** | Nên sequence: state machine → preferences → RỒI closure |

> [!IMPORTANT]
> **Sequencing concern:** Plan này declare "maintenance-only" / "closed", nhưng 2 plans đang pending (state machine 9.5/10, preferences 8.5/10) là non-trivial changes. **Closure plan nên land SAU khi state machine và preferences plans hoàn thành**, không phải trước. Nếu land trước, drift gates sẽ block chính 2 plans kia.

---

## So sánh 3 plans đã review

| | State Machine | Preferences | Closure |
|---|---|---|---|
| Score | 9.5/10 | 8.5/10 | 9/10 |
| Complexity | Cao | Cao (44 files) | Thấp-Trung |
| Risk | Trung bình | Cao | Thấp |
| Sequencing | **1st** | **2nd** | **3rd** |
| Nature | Feature change | Consolidation | Governance |

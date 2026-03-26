# Forge Monorepo — Project Review 2026-03-26

> **Review mode:** Health check + Code review
> **Primary scope:** Source repo `forge/` (`packages/`, `scripts/`, `tests/`, `docs/`)
> **Artifact check:** `dist/` chỉ được đọc để đối chiếu bundle đã build với source; mọi đề xuất sửa trong report đều nhắm vào source package/overlay, không sửa trực tiếp trong `dist/`
> **Version:** 0.8.0
> **Evidence:** `verify_repo.py` pass (57 tests, 38 smoke matrix)

---

## Findings

### [MEDIUM] F1 — SKILL.md core: Bundle Layout listing thiếu ~11 scripts

`packages/forge-core/SKILL.md` bundle layout tree chỉ liệt kê **13 scripts**, nhưng thực tế có **24 scripts**. Các file bị thiếu:

| File thực tế | Có trong SKILL.md layout? |
|---|---|
| `resolve_preferences.py` | ❌ |
| `write_preferences.py` | ❌ |
| `initialize_workspace.py` | ❌ |
| `resolve_help_next.py` | ❌ |
| `run_with_guidance.py` | ❌ |
| `translate_error.py` | ❌ |
| `prepare_bump.py` | ❌ |
| `resolve_rollback.py` | ❌ |
| `run_workspace_canary.py` | ❌ |
| `record_canary_result.py` | ❌ |
| `evaluate_canary_readiness.py` | ❌ |

**Impact:** Người dùng / contributor mới đọc SKILL.md sẽ không biết hết tooling có sẵn. Section "Executable Tooling" có liệt kê đầy đủ, nhưng bundle layout tree lại thiếu — gây ngược lại kỳ vọng "layout = directory listing".

**Recommendation:** Đồng bộ bundle layout tree với danh sách file thực tế, hoặc ghi chú rõ "tree liệt kê file cốt lõi, danh sách đầy đủ xem Executable Tooling".

---

### [MEDIUM] F2 — SKILL.md core: Bundle Layout listing thiếu ~13 test files

Bundle layout chỉ liệt kê **4 test files**, thực tế có **17 test files + 1 support module**:

- Thiếu: `test_bump_workflow.py`, `test_canary_rollout.py`, `test_error_translation.py`, `test_help_next.py`, `test_initialize_workspace.py`, `test_preferences.py`, `test_rollback_guidance.py`, `test_router_matrix.py`, `test_run_workflow.py`, `test_tool_roundtrip.py`, `test_workspace_canary.py`, `test_write_preferences.py`, `support.py`

**Impact:** Tương tự F1 — contributor sẽ đánh giá thấp coverage khi nhìn layout tree.

---

### [MEDIUM] F3 — SKILL.md core: Bundle Layout thiếu 8 reference files

Bundle layout chỉ liệt kê **16 references**, nhưng thực tế có **24 files**. Thiếu: `bump-release.md`, `canary-rollout.md`, `error-translation.md`, `help-next.md`, `personalization.md`, `rollback-guidance.md`, `run-guidance.md`, `workspace-init.md`.

**Impact:** Cùng pattern F1/F2 — docs inventory lệch thực tế.

---

### [MEDIUM] F4 — SKILL.md core: Bundle Layout thiếu `preferences-schema.json`

`data/` dir thực tế chứa 2 files (`orchestrator-registry.json` + `preferences-schema.json`), nhưng layout tree chỉ liệt kê `orchestrator-registry.json`.

---

### [LOW] F5 — Antigravity adapter data inventory dễ gây nhầm giữa overlay source và bundle đã build

Bundle đã build `dist/forge-antigravity/SKILL.md` liệt kê:
```
data/
└── orchestrator-registry.json
```

Trong khi đó, source adapter ở `packages/forge-antigravity/overlay/data/` chỉ chứa `preferences-compat.json`. Đây không phải bug runtime: bundle cuối cùng kế thừa `orchestrator-registry.json` từ core rồi mới chồng overlay lên trên.

**Impact:** Nhỏ nhưng dễ làm contributor nhầm giữa "file có trong bundle cuối cùng" và "file do overlay đóng góp trực tiếp".

**Recommendation:** Khi mô tả inventory adapter, nên ghi rõ đâu là file inherited from core và đâu là file added by overlay.

---

### [LOW] F6 — `monorepo.md` outdated: Mô tả adapter content quá sơ sài

`docs/architecture/monorepo.md` mô tả `forge-antigravity` chỉ gồm:
- host-specific SKILL.md
- agents/openai.yaml
- Antigravity-oriented host boundary wording

Thiếu: **operator wrappers** (10 files), **references overlay** (1 file), **data overlay** (1 file).

Tương tự `forge-codex` chỉ nêu SKILL.md + AGENTS.example, thiếu: **execution workflows** (2 files), **operator wrappers** (7 files), **references overlay** (3 files), **data overlay** (1 file), **scripts** (1 file).

**Recommendation:** Cập nhật monorepo.md để phản ánh adapter inventory thật sự.

---

### [LOW] F7 — Docs ngôn ngữ không nhất quán: EN vs VI

| File | Ngôn ngữ |
|---|---|
| `docs/architecture/monorepo.md` | English |
| `docs/architecture/adapter-boundary.md` | English |
| `docs/release/release-process.md` | Vietnamese |
| `docs/release/install.md` | Vietnamese |
| `docs/plans/*.md` | Vietnamese |
| `CHANGELOG.md` | Vietnamese |
| `README.md` | English |

**Impact:** Contributor đọc docs sẽ bị nhảy giữa 2 ngôn ngữ. Không có policy rõ ràng docs nên dùng ngôn ngữ nào.

**Recommendation:** Chốt policy: docs tiếng Anh (vì đây là skill framework có thể open-source), hoặc tiếng Việt toàn bộ. Thêm ghi chú ở README.

---

### [LOW] F8 — Adapter parity: Codex thiếu session wrappers (`/recap`, `/save-brain`, `/handover`)

`forge-antigravity` overlay có 10 operator wrappers, bao gồm `recap.md`, `save-brain.md`, `handover.md`.

`forge-codex` chỉ có 7 operator wrappers, thiếu 3 session aliases trên.

**Nuance:** Codex có `dispatch-subagents.md` — feature riêng không có ở Antigravity. Và Codex `session.md` override có thể bao gồm logic tương đương. Nhưng sự khác biệt này chưa được document rõ ở đâu.

**Recommendation:** Tại `docs/architecture/monorepo.md` hoặc adapter README, ghi rõ sự khác biệt feature surface giữa 2 adapters.

---

### [LOW] F9 — Core Skill Registry liệt kê `customize` và `init` nhưng core không có file tương ứng

Core SKILL.md **không** liệt kê `customize` và `init` trong Skill Registry (đúng). Nhưng:
- Antigravity SKILL.md Skill Registry liệt kê `customize` và `init` — có file tương ứng ở overlay ✅
- Core `workflows/operator/` chỉ có 5 files (help, next, run, bump, rollback) — thiếu `customize` và `init`

Đây là thiết kế đúng (customize/init là adapter concern). **Không có bug**, nhưng cần ghi chú rõ hơn ở adapter-boundary.md rằng đây là ví dụ cụ thể của "adapter-only skills".

---

### [INFO] F10 — `common.py` là file lớn nhất (39KB, ~1000+ lines)

`packages/forge-core/scripts/common.py` ở 39KB là file Python lớn nhất trong repo. Có vẻ chứa shared utilities cho tất cả scripts. Chưa có sign of tech debt rõ ràng (tests pass), nhưng nếu tiếp tục grow thì cân nhắc split.

---

### [INFO] F11 — Tốc độ phát triển: 8 releases trong ~2 ngày

CHANGELOG cho thấy 8 versions (0.1.0 → 0.8.0) đều dated 2026-03-24 → 2026-03-26. Đây là tốc độ rất nhanh. Không phải finding, nhưng cần lưu ý:
- Test coverage hiện tại tốt (57 tests + 38 smoke)
- Nếu có external consumers, velocity này cần changelog discipline mạnh hơn

---

### [INFO] F12 — `dist/` trong repo nhưng có `.gitignore`

`dist/` là generated artifact. Nếu đã list trong `.gitignore` thì OK. Nếu được track bởi git, đây là anti-pattern.

---

## Assumptions / Gaps

1. **Static review only** — không chạy build_release.py hay install thật để verify end-to-end flow.
2. **Chưa kiểm tra nội dung chi tiết** của từng workflow markdown (review xem contract/gate có khớp registry không) — chỉ kiểm inventory-level.
3. **Chưa đọc `common.py` chi tiết** — chỉ note size, chưa audit code quality bên trong.
4. **Codex overlay `orchestrator-registry.json`** (19KB vs core 16KB) — chưa diff chi tiết xem override gì.
5. **`dist/` không được review như source tree độc lập** — chỉ spot-check để xác nhận artifact đã build phản ánh source và để soi rõ các điểm inherited-vs-overlay khi cần.

---

## Tổng quan tính nhất quán / thống nhất / easy-to-use

### ✅ Điểm mạnh

| Khía cạnh | Đánh giá |
|---|---|
| **Kiến trúc monorepo** | Rõ ràng: core + adapters, boundary docs đầy đủ |
| **Test coverage** | 57 unit + 17 regression + 38 smoke — rất tốt cho framework dạng này |
| **Registry machine-readable** | `orchestrator-registry.json` là single source of truth |
| **Release pipeline** | verify → build → install → smoke — pipeline chuẩn |
| **Adapter boundary docs** | `adapter-boundary.md` rất rõ ràng, có decision test |
| **CHANGELOG** | Mọi version đều có mô tả rõ ràng bằng tiếng Việt |
| **Golden Rules** | Ngắn gọn, dễ nhớ, enforce được |

### ⚠️ Cần cải thiện

| Khía cạnh | Vấn đề | Mức độ |
|---|---|---|
| **SKILL.md bundle layout tree** | Lệch thực tế ~40% files | Medium |
| **Docs language** | Mix EN/VI không có policy | Low |
| **Adapter parity visibility** | Chưa document sự khác biệt giữa adapters | Low |
| **monorepo.md** | Outdated, không phản ánh adapter complexity | Low |

---

## Disposition

**`changes-required`** — Không có bug hay regression, repo healthy, tests pass. Nhưng tính nhất quán docs và SKILL.md listing cần update để đạt "easy-to-use" cho contributor mới.

## Finish Branch

**`continue-on-branch`** — Sửa F1-F6 (docs consistency) trước khi coi repo documentation là production-ready.

## Priority Fix Order

1. **F1-F4**: Cập nhật SKILL.md core bundle layout tree cho đúng reality
2. **F6**: Cập nhật monorepo.md adapter inventory
3. **F7**: Chốt language policy cho docs
4. **F5, F8, F9**: Nice-to-have clarification

---

## Summary

Forge v0.8.0 là một framework chín về mặt code — test coverage mạnh, kiến trúc adapter/core rõ ràng, pipeline release đầy đủ. Vấn đề chính nằm ở **documentation drift**: bundle layout trees trong SKILL.md chỉ liệt kê ~60% files thực tế, `monorepo.md` chưa cập nhật theo adapter evolution, và docs mix 2 ngôn ngữ không có policy rõ. Không có finding nào ảnh hưởng đến runtime behavior, nhưng trải nghiệm onboarding cho contributor mới sẽ bị confusing nếu không fix.

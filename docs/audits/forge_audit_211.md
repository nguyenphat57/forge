# Audit Forge 2.1.1 — Dư thừa & Cồng kềnh

> Tiêu chí: **Nhanh, Gọn, Chính Xác, Chặt Chẽ, Dễ Bảo Trì, Dễ Mở Rộng**

---

## Verdict tổng quát

Forge 2.1.1 đã **lean hơn 1.15.0 rất nhiều** (giảm 28.7% file, xóa 10K dòng). Tuy nhiên vẫn còn **7 vùng cồng kềnh** cần xử lý để đạt tiêu chí "Gọn" và "Dễ Bảo Trì":

| # | Vấn đề | Impact | Effort |
|---|--------|--------|--------|
| 1 | 14 docs lỗi thời chưa archive | Gọn ❌ | Thấp |
| 2 | 7 ghost scripts trong tooling.md | Chính Xác ❌ | Thấp |
| 3 | tooling.md 775 dòng — cồng kềnh nhất repo | Bảo Trì ❌ | Trung bình |
| 4 | References thừa (companion, canary, extension) | Gọn ❌ | Thấp |
| 5 | forge-core/scripts: 67 files, 12.7K dòng | Bảo Trì ❌ | Cao |
| 6 | .install-backups phình to | Gọn ❌ | Thấp |
| 7 | orchestrator-registry.json 33KB monolith | Mở Rộng ❌ | Trung bình |

---

## Vấn đề 1: 14 docs lỗi thời chưa archive

> [!WARNING]
> **14 file dated** nằm ở `docs/` root, tổng **91KB**, toàn bộ từ thời pre-1.0 (2026-03-28/29). Đã có `docs/archive/` nhưng không di chuyển vào.

```
docs/COMPANION_DECISION_GUIDE_2026-03-28.md
docs/FORGE_TARGET_STATE_2026-03-29.md
docs/PRODUCT_THESIS_2026-03-28.md
docs/PRODUCT_THESIS_2026-03-29.md
docs/PROJECT_COMPATIBILITY_AND_CANARY_FOLLOWUP_2026-03-29.md
docs/PROJECT_PHASE1_REPORT_2026-03-28.md
docs/PROJECT_PHASE2_DEEPENING_REPORT_2026-03-28.md
docs/PROJECT_PHASE2_REPORT_2026-03-28.md
docs/PROJECT_PHASE3_REPORT_2026-03-28.md
docs/PROJECT_POST_PHASE3_DELIVERY_REPORT_2026-03-28.md
docs/PROJECT_REAL_REPO_CANARY_AND_AUTH_QA_REPORT_2026-03-29.md
docs/PROJECT_TDD_SDD_BENCHMARK_2026-03-29.md
docs/QUICKSTART_SOLO_DEV_SHIPPING_2026-03-28.md
docs/TROUBLESHOOTING_2026-03-28.md
```

**Khuyến nghị:** Di chuyển toàn bộ vào `docs/archive/`. Nếu không cần giữ history, xóa hẳn.

---

## Vấn đề 2: 7 ghost scripts trong tooling.md

> [!CAUTION]
> `tooling.md` references **7 scripts không tồn tại** trong repo. Đây là vi phạm trực tiếp tiêu chí "Chính Xác".

| Ghost script | Chức năng cũ |
|-------------|-------------|
| `evaluate_canary_readiness.py` | Canary verdict |
| `generate_backend_brief.py` | Backend brief generator |
| `generate_ui_brief.py` | UI brief generator |
| `invoke_runtime_tool.py` | Runtime tool invocation |
| `record_canary_result.py` | Canary result recorder |
| `resolve_runtime_tool.py` | Runtime tool resolver |
| `run_workspace_canary.py` | Workspace canary runner |

Các scripts này bị xóa trong quá trình slim-down nhưng **tooling.md chưa cập nhật**.

**Khuyến nghị:** Xóa toàn bộ sections reference các ghost scripts khỏi `tooling.md`.

---

## Vấn đề 3: tooling.md — 775 dòng, file cồng kềnh nhất

> [!IMPORTANT]
> `references/tooling.md` = **775 dòng, 24.6KB** — file lớn nhất trong references, gấp 3x `smoke-tests.md` (492 dòng).

Nội dung bao gồm:
- Documentation cho **~25 tools** với ví dụ PowerShell commands
- Nhiều sections reference tools không tồn tại (ghost scripts ở trên)
- Overlap với `kernel-tooling.md` (cùng cover help/next, run, session, bump, rollback)

Đây là **contradiction kiến trúc**: SKILL.md được thu gọn về pointer-based, nhưng `tooling.md` vẫn là prose monolith.

**Khuyến nghị:**
1. Xóa sections cho ghost scripts (-200 dòng)
2. Merge nội dung trùng lặp với `kernel-tooling.md`
3. Mục tiêu: ≤300 dòng, hoặc tách thành files nhỏ hơn

---

## Vấn đề 4: References thừa cho features không còn tồn tại

Một số reference files mô tả features đã bị xóa hoặc không bao giờ được implement:

| File | Dòng | Vấn đề |
|------|------|--------|
| `companion-skill-contract.md` | 237 | Domain skills đã bị xóa. Companion contract vẫn tham chiếu workspace-local layer, router docs — **toàn bộ hệ thống này đã retire** |
| `canary-rollout.md` | 152 | Tham chiếu `evaluate_canary_readiness.py`, `record_canary_result.py`, `run_workspace_canary.py` — **toàn bộ ghost scripts** |
| `companion-routing-smoke-tests.md` | 87 | Smoke tests cho companion routing — **companions đã retire** |
| `extension-presets.md` | 48 | Vẫn nói "Allowed Surface For 1.14.x" — **stale versioning** |
| `frontend-stack-profiles.md` | 51 | Frontend stack profiles khi domains vẫn tồn tại — **domains đã xóa** |
| `architecture-layers.md` | 126 | Kiến trúc nhiều lớp — có thể đã stale |

**Khuyến nghị:** Di chuyển `companion-skill-contract.md`, `canary-rollout.md`, `companion-routing-smoke-tests.md` vào archive. Cập nhật hoặc xóa `extension-presets.md` và `frontend-stack-profiles.md`.

---

## Vấn đề 5: forge-core/scripts — 67 files, 12,700 dòng

> [!WARNING]
> Đây là vùng **cồng kềnh nhất** của repo. 67 Python scripts với 11 file >300 dòng.

### Top 5 files lớn nhất

| File | Dòng | Chức năng |
|------|------|-----------|
| `workflow_state_support.py` | **660** | Workflow state persistence |
| `help_next_support.py` | **590** | Help/next intelligence |
| `workflow_state_summary.py` | **564** | Workflow state summary |
| `route_preview.py` | **458** | Route preview engine |
| `track_execution_progress.py` | **428** | Execution progress tracker |

### Nhóm scripts có thể consolidate

**Compat layer (4 files, ~540 dòng)** — legacy migration code:
```
compat.py, compat_paths.py, compat_serialize.py, compat_translation.py
```
→ Hỏi: Solo dev cần compat layer cho gì? Nếu chỉ dùng v2.1.1, có thể xóa.

**Smoke matrix (5 files, ~724 dòng)**:
```
run_smoke_matrix.py, smoke_matrix_cases.py, smoke_matrix_runtime.py,
smoke_matrix_suites.py, smoke_matrix_validators.py, smoke_matrix_validators_tail.py
```
→ 6 files cho 1 smoke runner — cồng kềnh cho mục đích.

**Response contract (4 files, ~470 dòng)**:
```
response_contract.py, response_contract_evidence.py,
response_contract_locale.py, response_contract_text.py
```
→ Có thể merge thành 1-2 files.

**Workflow state (2 files, 1,224 dòng)**:
```
workflow_state_support.py (660), workflow_state_summary.py (564)
```
→ Hai file chiếm gần 10% tổng codebase. Cần review tính cần thiết.

**Route * (6 files, ~1,555 dòng)**:
```
route_analysis.py, route_delegation.py, route_execution_advice.py,
route_local_companions.py, route_preview.py, route_process_requirements.py,
route_risk.py, route_stage_contract.py
```
→ 8 files cho routing. `route_local_companions.py` reference companion layer đã retire.

**Khuyến nghị:**
1. Xóa `route_local_companions.py` (companion layer retired)
2. Audit compat layer — xóa nếu không cần backward compat
3. Merge response_contract_* thành 1 file
4. Evaluate: có thực sự cần workflow_state_summary + workflow_state_support tách riêng?

---

## Vấn đề 6: .install-backups phình to

`.install-backups/` chứa **hàng trăm files** từ mỗi lần install bundle. Không tracked bởi git nhưng nằm trong working directory.

**Khuyến nghị:** Thêm vào `.gitignore` (nếu chưa có) và clean up định kỳ.

---

## Vấn đề 7: orchestrator-registry.json 33KB monolith

`data/orchestrator-registry.json` = **33KB, ~1,300 dòng** JSON. Đây là single source of truth cho toàn bộ:
- 7 intents + chains
- Session modes
- Operator surface (8 actions + 3 session modes)
- Complexity hints
- Solo profiles
- Quality profiles
- Execution pipelines
- Lane model policy
- Evidence contract
- Skill selection contract
- Host capabilities
- Rationalization patterns

**Vấn đề Mở Rộng:** Thêm 1 operator action = edit file 33KB. Risk merge conflict cao.

**Khuyến nghị cho Dễ Mở Rộng:** Không cần tách ngay, nhưng nên đánh dấu sections rõ ràng hoặc cân nhắc tách thành files nhỏ hơn khi >50KB.

---

## Tổng hợp khuyến nghị

### Làm ngay (effort thấp, impact cao)

| # | Hành động | Giảm |
|---|-----------|------|
| 1 | Archive 14 docs lỗi thời | -91KB docs |
| 2 | Xóa ghost script sections từ tooling.md | -200 dòng, fix chính xác |
| 3 | Archive companion/canary references | -5 files, ~500 dòng |
| 4 | Xóa `route_local_companions.py` | -108 dòng dead code |

### Làm sớm (effort trung bình)

| # | Hành động | Giảm |
|---|-----------|------|
| 5 | Thu gọn tooling.md ≤300 dòng | -475 dòng |
| 6 | Audit + xóa compat layer | -540 dòng nếu không cần |
| 7 | Merge response_contract_* | -3 files |

### Cân nhắc sau (effort cao)

| # | Hành động | Lý do |
|---|-----------|-------|
| 8 | Consolidate workflow_state_* | 1,224 dòng, nhưng là core logic |
| 9 | Tách orchestrator-registry.json | Chỉ cần khi >50KB |
| 10 | Giảm số scripts forge-core | Cần audit từng file |

---

## Scorecard hiện tại

| Tiêu chí | Điểm | Lý do |
|----------|------|-------|
| **Nhanh** | 8/10 | Chain ngắn, bootstrap nhanh, nhưng 67 scripts là overhead khi AI phải discover |
| **Gọn** | 6/10 | Docs lỗi thời, ghost scripts, references stale, .install-backups |
| **Chính Xác** | 7/10 | 7 ghost scripts trong tooling.md = tham chiếu sai |
| **Chặt Chẽ** | 9/10 | Verification contract, evidence gates vẫn solid |
| **Dễ Bảo Trì** | 6/10 | 67 scripts, tooling.md 775 dòng, compat layer legacy |
| **Dễ Mở Rộng** | 7/10 | 33KB registry monolith, nhưng chấp nhận được ở scale hiện tại |

> [!TIP]
> Nếu thực hiện nhóm "Làm ngay" (4 tasks), scorecard sẽ cải thiện:
> - Gọn: 6→8
> - Chính Xác: 7→9
> - Dễ Bảo Trì: 6→7

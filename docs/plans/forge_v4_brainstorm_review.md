# Đánh giá: Forge Refactor V4 Brainstorm

Date: 2026-04-12
Status: historical feedback

> Đánh giá theo 5 trục: Chính xác, Cấu trúc, Ưu tiên, Rủi ro, Khả thi solo dev.

---

## Verdict tổng quát: 8.5/10

Đây là một brainstorm **chất lượng cao**, có kỷ luật tư duy rõ ràng. Điểm mạnh nhất là **khả năng tự kiềm chế** — doc biết nói "không" ở đúng chỗ. Có 3 điểm cần bổ sung nhưng không có điểm nào sai hướng.

---

## 1. Độ chính xác của claims — 9/10

### ✅ Đúng — đã cross-check với repo

| Claim | Thực tế repo |
|-------|-------------|
| 14 docs dated ở `docs/` root | ✅ Chính xác, đúng 14 files, ~91KB |
| `tooling.md` ~774 dòng, reference ghost scripts | ✅ 775 dòng, 7 ghost scripts (canary, brief, runtime-tool) |
| `kernel-tooling.md` ~79 dòng, là current entrypoint | ✅ 80 dòng, đúng vai trò |
| `forge-browse` + `forge-design` vẫn là packages | ✅ Cả hai vẫn ở `packages/`, không trong shipped matrix |
| State hotspot: workflow_state_support 660, help_next_support 590... | ✅ Số dòng chính xác ±2 |
| Route hotspot: route_preview 458, route_delegation 400 | ✅ Chính xác |

### ✅ Đúng — anti-finding quan trọng nhất

| Anti-finding | Xác minh |
|-------------|---------|
| `route_local_companions.py` **không phải dead code** | ✅ **Đúng** — `route_preview.py` line 47 import trực tiếp `from route_local_companions import infer_local_companions, resolve_workspace_router` |
| Compat layer **đang trên đường đi preference pipeline** | ✅ **Đúng** — `common.py` → `compat.py` → `compat_paths/serialize/translation.py`, `preferences_store.py` → `compat.py`, `smoke_matrix_validators.py` → `common.py` |
| `.install-backups/` đã gitignore | ✅ Đúng |

> [!TIP]
> **Đây là điểm mạnh nhất của doc.** Audit trước đó (trong conversation 8dd7904c) đã nhầm `route_local_companions.py` là dead code và compat layer là removable. Brainstorm này sửa đúng 2 lỗi đó.

### ⚠️ Thiếu sót nhỏ

- Doc chưa đề cập `reference-map.md` (252 dòng) cũng là file lớn trong references system — nó nằm trên reading path nhưng chưa được audit stale content.
- Doc không đề cập `smoke-tests.md` (492 dòng) và `smoke-test-checklist.md` (160 dòng) — hai files này chỉ ship trong Codex bundle, nhưng vẫn nặng đáng kể trong source core.

---

## 2. Chất lượng cấu trúc — 9/10

### Điểm mạnh

| Yếu tố | Đánh giá |
|---------|---------|
| Thesis rõ ràng | ✅ "source repo phải trông như product line kernel-only" — ngắn, actionable |
| Anti-findings trước proposals | ✅ Tránh bẫy "audit nói xóa → xóa ngay" |
| "Why this matters for solo dev" mỗi workstream | ✅ Anchor trực tiếp vào user persona |
| Rủi ro + guardrails tách riêng | ✅ Không trộn vào proposals |
| Target state sau V4 | ✅ Testable, không vague |

### Cải tiến nhỏ

- **Thiếu verification plan cụ thể** cho mỗi tranche. Mỗi tranche có "Proof of value" nhưng chưa có "Verification command" cụ thể (ví dụ: `python scripts/verify_repo.py --profile fast` sau tranche 1). Với Forge — framework bắt verification bằng evidence — brainstorm nên tự apply nguyên tắc đó cho chính mình.

---

## 3. Thứ tự ưu tiên tranches — 8/10

### ✅ Đúng hướng

Thứ tự **docs → packages → state engine → routing → registry** là đúng theo ROI:

```
Tranche 1 (docs/refs)    → effort thấp,  impact cao cho "Gọn" + "Chính Xác"
Tranche 2 (archive pkgs) → effort thấp,  impact cao cho "Gọn"
Tranche 3 (state engine) → effort cao,   impact cao cho "Bảo Trì"
Tranche 4 (routing)      → effort cao,   impact trung bình
Tranche 5 (registry)     → effort cao,   impact thấp hiện tại
```

Logic "surface trước, internals sau, registry sau cùng" là sound.

### ⚠️ Tranche 2 cần cẩn trọng hơn doc nói

Doc nói "archive forge-browse + forge-design" nhưng chưa đề cập:

1. **Tests vẫn reference hai packages này:**
   - `tests/test_install_bundle_browse.py`
   - `tests/test_install_bundle_design.py`
   - `tests/release_repo_test_companion_install.py`
   - `tests/test_runtime_tool_registration.py`

2. **`build_release.py` và `package_matrix.py`** — cần check xem build pipeline có skip retired packages không hay vẫn compile chúng.

3. **`tooling.md`** references runtime tool resolver/invoker cho browse/design — đã là ghost scripts, nhưng nếu tranche 1 chưa clean hết thì tranche 2 archive packages sẽ tạo thêm broken refs.

**Khuyến nghị:** Tranche 1 và 2 nên merge thành **1 tranche thống nhất** — clean docs + ghost refs + archive packages cùng lúc, vì chúng liên quan chặt chẽ. Làm riêng sẽ tạo intermediate state với broken refs.

---

## 4. Rủi ro bị bỏ sót — 7/10

Doc liệt kê 3 risks + 5 guardrails, tất cả đều hợp lệ. Tuy nhiên **thiếu 3 risks thực tế:**

### Risk bị bỏ sót #1: Shipped bundle regression

> [!WARNING]
> Tranche 3 (state decomposition) và Tranche 4 (routing simplification) thay đổi files nằm **trực tiếp trong shipped bundle path** theo `package-matrix.json`:
> - `scripts/help_next_support.py` — trong required_bundle_paths
> - `scripts/common.py` — trong required_bundle_paths
> - `scripts/run_guidance_support.py` — trong required_bundle_paths
>
> Refactor các files này mà không chạy full install+verify sẽ ship bundle bị broke.

**Guardrail cần thêm:** Mỗi tranche 3/4 phải kết thúc bằng `python scripts/build_release.py --format json` + `python scripts/verify_bundle.py` cho cả 3 bundles.

### Risk bị bỏ sót #2: Overlay SKILL desync

`generate_overlay_skills.py` compose overlay `SKILL.md` từ core `SKILL.md` + adapter `SKILL.delta.md`. Nếu tranche nào thay đổi core SKILL hoặc reference structure mà **quên chạy** `--apply`, shipped overlays sẽ drift.

### Risk bị bỏ sót #3: Test count regression

Doc không nói rõ: sau khi archive `forge-browse` + `forge-design`, bao nhiêu tests sẽ bị ảnh hưởng? Em đếm ít nhất **4 test files** cần update hoặc archive cùng. Nếu `verify_repo.py` chạy full test suite, archive packages mà không update tests = test failures ngay lập tức.

---

## 5. Khả thi cho solo dev — 9/10

### ✅ Điểm mạnh

| Factor | Đánh giá |
|--------|---------|
| Scope bounded | ✅ Không phải rewrite, là maintainability tranche |
| Incremental safety | ✅ 5 tranches có thể dừng sau bất kỳ tranche nào |
| Không mở feature surface mới | ✅ Contraction only |
| Registry split deferred | ✅ Tránh premature modularization |
| Compat layer protected | ✅ Không xóa mù |

### Timeline estimate cho solo dev

| Tranche | Effort ước tính | Risk |
|---------|----------------|------|
| 1 (docs + refs) | 2-3h | Thấp |
| 2 (archive packages) | 2-4h | Trung bình — cần update tests |
| 3 (state decomposition) | 1-2 ngày | Cao — core logic |
| 4 (routing simplification) | 1 ngày | Trung bình |
| 5 (registry governance) | 1h (chỉ đặt policy) | Thấp |

**Tổng: ~3-4 ngày** nếu chỉ tranche 1+2, ~1 tuần nếu full V4.

---

## Tổng hợp đánh giá

| Trục | Điểm | Ghi chú |
|------|------|---------|
| Chính xác claims | 9/10 | Anti-findings sửa đúng lỗi audit trước. Thiếu sót nhỏ ở reference-map và smoke-tests |
| Cấu trúc doc | 9/10 | Thesis → anti-findings → proposals → risks → guardrails. Thiếu verification commands |
| Thứ tự ưu tiên | 8/10 | Đúng hướng. Tranche 1 + 2 nên merge. Tranche 2 cần cẩn trọng test impact |
| Rủi ro coverage | 7/10 | 3 risks bị bỏ sót: bundle regression, overlay desync, test count regression |
| Khả thi solo dev | 9/10 | Scope bounded, incremental, contraction-only |
| **Tổng** | **8.5/10** | |

---

## 3 khuyến nghị bổ sung

1. **Merge tranche 1 + 2** thành 1 tranche thống nhất để tránh intermediate broken refs state

2. **Thêm guardrail:** mỗi tranche phải kết thúc bằng:
   ```powershell
   python scripts/verify_repo.py --profile fast
   python scripts/build_release.py --format json
   python scripts/generate_overlay_skills.py --check
   ```

3. **Bổ sung test impact assessment** cho tranche 2: liệt kê cụ thể test files cần archive/update khi archive `forge-browse` + `forge-design`

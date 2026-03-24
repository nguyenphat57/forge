# Changelog

## 0.6.0 - 2026-03-24

- Thêm Codex host takeover cho `forge-codex` qua `AGENTS.global.md` và `install_bundle.py --activate-codex`, đồng thời backup rồi retire `~/.codex/awf-codex` và các skill legacy `awf-*`.
- Bổ sung Wave C artifacts còn thiếu cho `forge-codex`: session workflow riêng cho Codex, smoke references, registry override, và release/install verification cho host activation path.
- Chuẩn hóa lại narrative của Forge theo hướng natural-language first cho Codex và giữ `SESSION` của `forge-codex` nhất quán với registry, wrapper, docs, và dist output.


## 0.5.1 - 2026-03-24

- Chuẩn hóa lại prose tiếng Việt có dấu trên toàn bộ source Markdown của `forge-core`, `forge-antigravity`, và `forge-codex`.
- Dọn các residue lỗi dấu kiểu `kh?ng/???c` trong docs, workflow wrappers, plan, và release references để source repo sạch hơn.
- Rebuild `dist/` từ source đã chuẩn hóa và verify lại toàn bộ repo để bảo đảm bundle phát hành bám đúng nội dung mới.

## 0.5.0 - 2026-03-24

- Thêm Wave C cho `forge-codex` với thin wrappers cho `help`, `next`, `run`, `bump`, `rollback`, `customize`, và `init`.
- Cập nhật `AGENTS.example.md` và adapter docs để Codex giữ natural-language first, slash chỉ là alias optional, và không duplicate orchestration rules của Forge.
- Bổ sung `codex-operator-surface.md` và release tests để build/install giữ nguyên Codex overlay sau mỗi lần release.

## 0.4.0 - 2026-03-24

- Thêm Wave B cho `forge-antigravity` với operator wrappers cho `help`, `next`, `run`, `bump`, `rollback`, `customize`, `init`, và session handover flows.
- Mở rộng `forge-core` với preference persistence qua `write_preferences.py`, thêm `pace` và `feedback_style`, và workspace bootstrap reusable qua `initialize_workspace.py`.
- Hardening `install_bundle.py` theo hướng sync in-place để rollout an toàn trên Windows ngay cả khi thư mục runtime đang bị host lock.
- Tăng verify coverage cho release/install và bổ sung regression, smoke, và overlay checks cho Wave B.

## 0.3.0 - 2026-03-24

- Thêm Wave A / P1.1 với error translator host-neutral và nối trực tiếp vào `run` để biến lỗi kỹ thuật thành guidance dễ đọc và xử lý.
- Thêm Wave A / P1.2 với bump workflow dùng chung qua `prepare_bump.py`, cập nhật `VERSION`, changelog, và release checklist theo một contract duy nhất.
- Thêm Wave A / P1.3 với rollback guidance engine qua `resolve_rollback.py`, phân loại deploy/config/migration/code-change và đề xuất bước xử lý an toàn.
- Nâng full regression, smoke matrix, và adapter wiring để Antigravity runtime và Codex runtime cùng kế thừa trọn bộ Wave A từ core.

## 0.2.0 - 2026-03-24

- Thêm Wave A / P0.1 với preferences engine host-neutral cho `technical_level`, `detail_level`, `autonomy_level`, và `personality`.
- Thêm Wave A / P0.2 với help-next navigator repo-first dùng chung cho `forge-antigravity` và `forge-codex`.
- Thêm Wave A / P0.3 với run-guidance engine để chạy lệnh thật, detect ready-signal, và route tiếp sang `test`, `debug`, hoặc `deploy`.
- Mở rộng regression, smoke matrix, và adapter wiring để cả Antigravity runtime lẫn Codex runtime đều kế thừa cùng contract của core.

## 0.1.0 - 2026-03-24

- Tách Forge thành monorepo `forge-core + forge-antigravity + forge-codex`.
- Thêm release pipeline chuẩn với `build_release.py`, `verify_repo.py`, và `install_bundle.py`.
- Chuẩn hóa `forge-core` theo hướng host-neutral, giữ host-specific entrypoints trong adapter overlays.
- Thêm test cấp monorepo cho build/install/version flow và release documentation.

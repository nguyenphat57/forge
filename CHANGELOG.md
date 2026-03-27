# Changelog

## 0.11.0 - 2026-03-27

- Tách hoàn toàn locale routing và output contract khỏi `forge-core`, giữ core EN-only và chuyển ownership sang adapter overlays.
- Thêm locale pack tiếng Việt và output-contract profiles cho `forge-antigravity` và `forge-codex`, kèm regression tests adapter-level và release checks tương ứng.
- Chuẩn hóa personalization/docs/test fixtures sang English-first ở core, đồng thời bổ sung verify để dist bundles vẫn pass với bundle-aware contracts.


## 0.10.0 - 2026-03-27

- Tách logic preferences trong `forge-core` khỏi `common.py` sang các module chuyên biệt như `preferences.py`, `compat.py`, `style_maps.py`, `skill_routing.py`, `text_utils.py`, và `error_translation.py`, đồng thời giữ `common.py` như shim re-export để không làm vỡ entrypoints hiện có.
- Đơn giản hóa persistence preferences theo split-file adapter-global state với canonical fields ở `state/preferences.json`, extras ở `state/extra_preferences.json`, giữ nguyên `output_contract`, và chỉ migrate legacy single-file state trên write/apply flows.
- Rút `forge-antigravity` compat config về read/migration-only, cập nhật docs/workflows/contracts của `forge-core`, `forge-codex`, và `forge-antigravity` cho semantics mới, và mở rộng regression/release verification để khóa split-file behavior từ source bundle tới dist bundle.


## 0.9.0 - 2026-03-26

- Đồng bộ test, docs, và release verification cho split-file preferences sau refactor v0.8.0.
- Cập nhật regression tests để khóa behavior canonical + extras persistence trên cả source bundle lẫn dist bundle.
- Clean up residual doc drift giữa `forge-core`, `forge-antigravity`, và `forge-codex` sau đợt thêm `output_contract`.


## 0.8.0 - 2026-03-26

- Thêm `output_contract` trong `forge-core` để suy ra policy hiển thị từ workspace extras như `language`, `orthography`, `tone_detail`, và `custom_rules`.
- Bổ sung template `extra preferences` trong tài liệu personalization để user tự thiết lập ngôn ngữ nhanh qua `.brain/preferences.json`.
- Cập nhật flow `customize` của `forge-codex` và `forge-antigravity` để request về ngôn ngữ được trả lời ngắn, trỏ thẳng tới template extras thay vì giải thích dài về canonical preferences.
- Thêm helper PowerShell `enable_windows_utf8.ps1` cho `forge-codex` để giảm lỗi vỡ dấu tiếng Việt trên Windows.


## 0.7.2 - 2026-03-25

- Sửa contract `session` của `forge-core` để restore flow nạp `.brain/preferences.json` qua `resolve_preferences.py` trước khi tóm tắt context.
- Cập nhật `forge-codex` session override để recap/next step bám theo response preferences của workspace thay vì bỏ qua personalization.
- Thêm regression test ở `forge-core` và release repo để khóa yêu cầu preferences restore cho source bundle lẫn dist bundle của `forge-codex` và `forge-antigravity`.


## 0.7.1 - 2026-03-24

- Đồng bộ contract `/bump` của `forge-antigravity` và `forge-codex` theo `forge-core`, để cả hai host đều dùng wording và guardrail semver mới.
- Thêm regression test ở release repo để chặn việc wrapper/skill của adapter lệch contract bump của core trong các lần cập nhật sau.
- Rebuild và tái cài đặt bundle host từ commit sạch để manifest, version, và nội dung cài đặt của `.codex` và `.gemini` khớp nhau.

## 0.7.0 - 2026-03-24

- Thêm host-aware delegation cho Forge, gồm routing `parallel-split`/`independent-reviewer`, workflow `dispatch-subagents`, và wiring Codex để bật delegation runtime khi host hỗ trợ subagent thật.
- Nâng cấp flow `bump` để có thể tự suy luận semver từ git diff theo workspace, trả thêm lý do và độ tự tin, đồng thời nhận đúng thay đổi capability trong cấu trúc monorepo.
- Đồng bộ lại contract, docs, smoke tests, và release verification giữa `forge-core` với `forge-codex` để natural-language bump vẫn giữ guardrail release rõ ràng.


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

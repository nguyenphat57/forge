# Changelog

## 1.3.0 - 2026-03-28

- Absorb the planned gstack-inspired improvements into Forge: generated host artifacts with freshness gates, unified workflow state, hardened packaging manifests, runtime actuators, and design runtime tooling.
- Add real runtime verification for `forge-browse` and `forge-design`, including live Playwright smoke, installed bundle integration smoke, and persisted brief to capture evidence flows.
- Expand release and contract coverage so Codex host wrappers are generated from canonical sources, package matrix metadata stays authoritative, and `verify_repo.py` remains the single repo gate before promotion.


## 1.2.0 - 2026-03-28

- Sửa độ ổn định của `forge-codex` release bundle verification, gồm xử lý đúng materialized bundle layout trong `support.py` và tránh import lệch `support` trong suite dist.
- Chuẩn hóa prose agent-facing cho `forge-antigravity` trên `SKILL.md`, `GEMINI.global.md`, operator wrappers, và operator-surface reference để đạt mức native-clear hơn mà không đổi workflow semantics.
- Cập nhật smoke contract cho `prepare_bump.py` để case auto-preview không có git context chấp nhận `inferred_from = no-git-context`, đồng thời giữ full release verification xanh sau bump.


## 1.1.0 - 2026-03-27

- Nâng độ native-clear cho `forge-core` và `forge-codex` trên các workflow, reference, operator wrapper, và host docs để Codex đọc routing/gate/proof rõ hơn và ít ambiguity hơn.
- Sửa adapter locale/runtime contract cho `forge-codex`, gồm locale pack tiếng Việt UTF-8 chuẩn, bundle-aware loading qua `FORGE_BUNDLE_ROOT`, và support shim để overlay tests chạy đúng cả khi chạy riêng lẫn khi chạy chung với `forge-core`.
- Mở rộng regression coverage và giữ release evidence xanh sau thay đổi, đồng thời bump version theo semver `minor` vì repo có thêm capability mới ở lớp adapter/runtime support.


## 1.0.0 - 2026-03-27

- Hoàn tất đợt refactor agent-health trên toàn repo: tách các script và test hotspot thành module nhỏ theo chức năng, giữ các entrypoint ổn định, và đưa toàn bộ source Python ngoài `dist/` cùng `.install-backups/` về dưới ngưỡng 300 dòng mỗi file.
- Chuẩn hóa release/runtime contracts bằng cách materialize overlay registry khi build, siết verify pipeline với secret scan và release hardening coverage, đồng thời giữ nguyên các flow cài bundle, preferences, help-next, route preview, smoke matrix, và workspace canary sau khi tách lớp.
- Giảm nhiễu khi agent đọc workspace bằng `.ignore`, bổ sung báo cáo remediation/review, và chốt full verification cho source bundle lẫn dist bundle trước khi phát hành.


## 0.14.0 - 2026-03-27

- Mở rộng bootstrap host-level cho `forge-codex` và `forge-antigravity`, thêm global templates rõ state root, hai file preferences tách riêng, resolver tuyệt đối, và activation flow để render đúng `AGENTS.md` với `GEMINI.md`.
- Thêm self-healing cho extra preferences khi gặp mojibake có thể phục hồi an toàn, đồng thời siết `response_contract` để bắt sai `tone_detail` như trường hợp phải gọi `Sếp`, xưng `Em`.
- Tăng release/install regression coverage để khóa contract bootstrap preferences, host activation, và release overlays trên cả source bundle lẫn dist bundle trước khi phát hành.


## 0.13.0 - 2026-03-27

- Khôi phục response personalization tự động ở đầu mỗi thread mới cho `forge-codex` và `forge-antigravity`, bao gồm bootstrap instructions trong host entrypoints và prompt mặc định của Antigravity.
- Bổ sung bundle-native dev state fallback qua build metadata để `forge-core`, `forge-codex`, và `forge-antigravity` tự tìm đúng adapter-global state root ngay cả khi chưa có install manifest.
- Mở rộng release regression tests để khóa behavior bootstrap preferences và state-root resolution trên cả overlay source lẫn dist bundles trước khi phát hành.


## 0.12.0 - 2026-03-27

- Tăng độ native tiếng Việt cho `forge-codex` bằng cách làm sạch `locale/vi` về UTF-8 chuẩn, thêm regression cho prompt Việt tự nhiên hơn, và chặn lại lỗi mojibake ở asset bundle.
- Bổ sung response-contract validator cùng smoke/tests để `forge-codex` bám chặt hơn vào contract output tiếng Việt và evidence response.
- Siết adapter boundary để shared core không nhúng trực tiếp assumption của `.codex`, đồng thời giữ các tối ưu host-specific ở đúng lớp `forge-codex`.


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

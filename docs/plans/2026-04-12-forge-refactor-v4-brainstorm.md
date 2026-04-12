# Brainstorm: Forge Refactor V4

Date: 2026-04-12
Status: historical brainstorm — chưa duyệt
Inputs:
- `docs/audits/forge_audit_211.md`
- `docs/release/package-matrix.json`
- `packages/forge-core/references/target-state.md`
- `packages/forge-core/references/reference-map.md`
- `packages/forge-core/references/tooling.md`
- `packages/forge-core/references/kernel-tooling.md`

## Vấn đề

Forge 2.1.1 đã lean hơn đáng kể ở shipped surface: current product line chỉ còn `forge-core`, `forge-codex`, và `forge-antigravity`. Tuy vậy, current source repo vẫn chưa thật sự đạt trạng thái tốt nhất cho:

- `Nhanh`: solo maintainer vẫn phải discover quá nhiều docs và support modules trước khi chạm đúng entrypoint.
- `Gọn`: source repo còn historical baggage, stale references, và package không còn khớp với shipped story.
- `Chính Xác`: một số current references vẫn mô tả script hoặc surface đã bị retire.
- `Chặt Chẽ`: verification discipline mạnh, nhưng engine nội bộ đang phải gánh nhiều lớp support hơn mức lý tưởng.
- `Dễ Bảo Trì`: state engine, routing engine, và docs spine còn quá nặng ở một số hotspot.
- `Dễ Mở Rộng`: một số monolith vẫn đủ lớn để tăng merge-conflict pressure và làm extension trở nên tốn công hơn mức cần thiết.

Thesis của V4 là: Forge phải làm source repo trông và vận hành giống product line kernel-only hiện tại. Điều đó nghĩa là ít current surface hơn, ít docs current hơn, ít dead historical baggage hơn, và lõi state/routing dễ bảo trì hơn mà không weaken verification discipline.

## Hiện trạng đã xác minh

Các finding dưới đây đã được đối chiếu với repo hiện tại, không bê nguyên wording từ audit lỗi encoding:

- Có `14` file dated ở `docs/` root chưa được archive, dù repo đã có `docs/archive/`.
- `packages/forge-core/references/tooling.md` vẫn còn reference tới ghost scripts không còn tồn tại trong repo, gồm runtime-tool, canary, và brief-generator paths đã bị retire.
- `tooling.md` hiện là prose monolith quá lớn so với current docs spine. File này khoảng `774` dòng, trong khi `kernel-tooling.md` chỉ khoảng `79` dòng và đã là current entrypoint cho tooling surface kernel-only.
- `reference-map.md` hiện khoảng `164` dòng và vẫn nằm trên current reading path. File này nên tiếp tục là index, nhưng không nên phình thành nơi chứa prose dài thay cho các references chuyên biệt.
- `smoke-tests.md` khoảng `491` dòng và `smoke-test-checklist.md` khoảng `215` dòng. Đây chưa phải first-cut problem như `tooling.md`, nhưng chúng là deep references nặng cần được rà khi slim docs spine.
- Source repo vẫn còn `packages/forge-browse` và `packages/forge-design`, dù shipped product line hiện tại là kernel-only theo `docs/release/package-matrix.json`.
- Cụm state/operator là hotspot lớn:
  - `workflow_state_support.py`: khoảng `660` dòng
  - `help_next_support.py`: khoảng `590` dòng
  - `workflow_state_summary.py`: khoảng `564` dòng
  - `session_context.py`: khoảng `417` dòng
- Cụm routing cũng còn nặng:
  - `route_preview.py`: khoảng `458` dòng
  - `route_delegation.py`: khoảng `400` dòng
- `data/orchestrator-registry.json` vẫn là monolith lớn và là nơi cần theo dõi cho expansion cost, nhưng chưa phải first cut tốt nhất của V4.

Tóm lại, Forge 2.1.1 đã lean ở bên ngoài, nhưng current source repo vẫn còn medium-heavy ở docs surface, state engine, routing engine, và historical package baggage.

## Những gì không nên kết luận quá tay

V4 không được bắt đầu bằng những xóa bỏ chưa có audit usage. Ba anti-finding sau phải được ghi rõ để tránh cleanup sai:

- Không gọi `route_local_companions.py` là dead code. File này vẫn đang được `route_preview.py` import và dùng cho workspace-local augmentation.
- Không gọi compat layer là removable ngay. `compat.py`, `compat_paths.py`, `compat_serialize.py`, và `compat_translation.py` vẫn đang nằm trên đường đi của preference pipeline hiện tại.
- `.install-backups/` đã được ignore trong `.gitignore`. Đây là housekeeping issue và retention issue, không phải repo-contract bug.

Nguyên tắc của V4 là: chỉ aggressive ở current surface và stale baggage; không aggressive mù ở các layer compatibility hoặc augmentation chưa audit usage thật.

## Direction đề xuất cho V4

Strategic direction của V4:

- `Aggressive contraction of current source surface`
- `Archive historical baggage out of current paths`
- `Decompose heavy state/routing internals without weakening verification discipline`

V4 không phải rewrite-from-scratch. V4 là maintainability tranche mạnh tay, nhưng vẫn phải giữ nguyên các non-negotiables của Forge: proof before claims, packet/workflow-state continuity, và kernel-only shipped contract.

Thứ tự ưu tiên của V4 phải rõ ràng:

1. source/docs cleanup trước
2. engine decomposition sau
3. registry modularization sau cùng

Lý do của thứ tự này là ROI. Nếu source repo current story còn không khớp với product story, thì refactor engine trước sẽ chỉ làm lõi đẹp hơn trong khi maintainer vẫn phải đi qua một current surface rối và dư.

## Các workstream của V4

### A. Historical Docs Contraction

Archive `14` docs dated ở `docs/` root vào historical path phù hợp, để current docs chỉ còn `docs/current/`, `docs/release/`, và các references còn giá trị thực cho maintainer hiện tại. Đồng thời, mọi pointer từ current docs sang những file historical này phải bị cắt hoặc đổi sang archive narrative rõ ràng.

Why this matters for solo dev: ít “đường nhầm” hơn khi chỉ muốn biết repo hiện tại đang hoạt động theo contract nào.

### B. Reference Spine Slimdown

Rút mạnh hoặc split `packages/forge-core/references/tooling.md`, xóa ghost-script sections, và đưa current tooling reading order về hai entrypoint chính là `kernel-tooling.md` và `reference-map.md`. `reference-map.md` phải giữ vai trò index thay vì tiếp tục tích lũy prose. `smoke-tests.md` và `smoke-test-checklist.md` cần được giữ như deep references có chủ đích, không để chúng vô tình trở thành current entrypoints cạnh tranh. Các reference stale cho companion, canary, runtime-tool, extension/version cũ phải bị archive hoặc loại khỏi current reading path.

Why this matters for solo dev: giảm prose discovery cost và tăng xác suất đọc đúng file current ngay từ lần đầu.

### C. Source/Product Alignment

Archive `forge-browse` và `forge-design` khỏi current repo path hoặc chuyển chúng vào historical subtree rõ ràng, thay vì tiếp tục để chúng sống như package ngang hàng trong current source repo. Source repo current story phải khớp với package matrix kernel-only: thứ không còn thuộc shipped contract thì không nên nằm trên maintainer path như thể nó vẫn là current product line.

Why this matters for solo dev: loại bỏ sự lệch giữa “Forge đang ship cái gì” và “repo đang trông như ship cái gì”.

### D. State Engine Decomposition

Tách cụm `workflow-state` thành các lớp rõ trách nhiệm hơn:

- state load/store
- summary/read-model
- operator decision layer cho `help`, `next`, `save`, `resume`

Mục tiêu không phải đổi behavior lớn, mà giảm coupling và làm debug `help/next/save/resume` dễ hơn. V4 nên giữ logic state-driven, nhưng bớt tình trạng nhiều quyết định business logic nằm chồng trong các support modules lớn.

Why this matters for solo dev: operator layer là thứ maintainer chạm hằng ngày; nếu nó khó đọc, cost mệt mỏi tích lũy rất nhanh.

### E. Routing Engine Simplification

Giữ `route_preview.py` là facade deterministic, nhưng audit lại route helpers để giảm over-fragmentation và retire những phần hiện chỉ còn giá trị lịch sử hơn là giá trị runtime. V4 không nên đụng các phần có risk compatibility nếu chưa có usage audit, nhưng cần làm route engine đọc được hơn và ít “support module hopping” hơn.

Why this matters for solo dev: cùng một mức correctness, nhưng ít support modules hơn sẽ làm route reasoning nhanh và dễ bảo trì hơn.

### F. Registry Governance Later

Không tách `orchestrator-registry.json` ngay trong tranche đầu của V4. Thay vào đó, V4 chỉ cần đặt governance rõ: khi file vượt ngưỡng size hoặc merge-conflict pressure tăng đủ mức, registry mới được tách. Nếu chưa có pressure đủ lớn, việc tách sớm chỉ chuyển complexity từ một monolith sang nhiều file mà chưa chắc giảm cost thật.

Why this matters for solo dev: tránh mở thêm refactor surface không mang lại lợi ích tức thời cho vận hành hằng ngày.

## Target State sau V4

Sau V4, current source repo nên đạt trạng thái sau:

- current source repo không còn package lịch sử hoặc retired package nằm trên maintainer path như thể chúng còn là product surface hiện tại
- current docs spine chỉ còn vài entrypoint rõ ràng, với `reference-map.md` và `kernel-tooling.md` là cổng vào chính cho maintainer
- operator state engine dễ hiểu hơn, để debug `help/next/save/resume` không còn đòi hỏi đi xuyên qua nhiều file lớn đan nhau
- routing vẫn giữ được độ chặt và độ deterministic, nhưng ít support modules hơn và ít branch “lịch sử” hơn
- release-facing story, source story, và maintainer story khớp nhau

Target state này phục vụ trực tiếp 6 tiêu chí ban đầu:

- `Nhanh`: ít discovery cost hơn
- `Gọn`: ít current surface hơn
- `Chính Xác`: ít stale refs hơn
- `Chặt Chẽ`: verification discipline vẫn giữ nguyên
- `Dễ Bảo Trì`: hotspot ít đan nhau hơn
- `Dễ Mở Rộng`: current boundaries rõ hơn trước khi mở rộng tiếp

## Các tranche đề xuất

### Tranche 1: docs/archive + ghost refs + current docs spine + archive legacy runtime packages

Làm sạch current docs surface trước:

- archive 14 docs dated ở `docs/` root
- xóa ghost refs khỏi `tooling.md`
- slim current reading order về `reference-map.md` + `kernel-tooling.md`
- archive `forge-browse` + `forge-design` khỏi current repo path hoặc chuyển chúng sang historical subtree rõ ràng trong cùng tranche, để tránh intermediate state nửa current nửa historical
- update hoặc archive đồng bộ các test đang trỏ trực tiếp tới surface browse/design:
  - `tests/test_install_bundle_browse.py`
  - `tests/test_install_bundle_design.py`
  - `tests/release_repo_test_companion_install.py`
  - `tests/test_runtime_tool_registration.py`

Proof of value:

- fewer current entrypoints
- fewer misleading references
- current docs path khớp hơn với kernel-only story
- source tree khớp package matrix hơn
- maintainer path không còn package runtime retired
- product story và source story khớp nhau hơn

Verification tối thiểu:

- `python scripts/verify_repo.py --profile fast`
- `python scripts/generate_overlay_skills.py --check`
- `python scripts/build_release.py --format json`
- `python dist/forge-core/scripts/verify_bundle.py --format json`
- `python dist/forge-codex/scripts/verify_bundle.py --format json`
- `python dist/forge-antigravity/scripts/verify_bundle.py --format json`

### Tranche 2: decompose state engine

Tách lớp state/operator decision mà không thay shipped behavior.

Proof of value:

- hotspot files nhỏ hơn
- debug `help/next/save/resume` đi ít tầng hơn
- unchanged verification discipline

Verification tối thiểu:

- `python scripts/verify_repo.py --profile fast`
- `python scripts/generate_overlay_skills.py --check`
- `python scripts/build_release.py --format json`
- `python dist/forge-core/scripts/verify_bundle.py --format json`
- `python dist/forge-codex/scripts/verify_bundle.py --format json`
- `python dist/forge-antigravity/scripts/verify_bundle.py --format json`

### Tranche 3: simplify routing engine

Rà và gom route helpers, giữ facade deterministic nhưng giảm over-fragmentation.

Proof of value:

- lower line counts ở routing hotspot
- fewer cross-file jumps khi audit route decisions
- unchanged route-preview contract

Verification tối thiểu:

- `python scripts/verify_repo.py --profile fast`
- `python scripts/generate_overlay_skills.py --check`
- `python scripts/build_release.py --format json`
- `python dist/forge-core/scripts/verify_bundle.py --format json`
- `python dist/forge-codex/scripts/verify_bundle.py --format json`
- `python dist/forge-antigravity/scripts/verify_bundle.py --format json`

### Tranche 4: reconsider registry split only if still needed

Chỉ mở registry split nếu sau 3 tranche đầu file vẫn là bottleneck thật.

Proof of value:

- tránh premature modularization
- chỉ trả cost modularization khi payoff đã rõ

Verification tối thiểu:

- `python scripts/verify_repo.py --profile fast`
- `python scripts/generate_overlay_skills.py --check`
- `python scripts/build_release.py --format json`

## Rủi ro và guardrails

Các risk thật của V4:

- cleanup quá mạnh có thể làm mất historical context hữu ích cho maintainer tương lai
- decomposition state/routing có thể làm drift behavior nếu cắt theo “đẹp cấu trúc” thay vì theo runtime responsibility
- archive package legacy nhưng docs/tests còn trỏ về path cũ sẽ tạo broken references và broken assumptions
- tranche 2 và 3 chạm các file đang nằm trực tiếp trên shipped bundle path; nếu refactor đúng cấu trúc nhưng sai integration, Forge có thể ship bundle bị regress
- thay đổi docs spine hoặc core references mà quên `generate_overlay_skills.py --check` có thể tạo desync giữa core `SKILL.md`, overlay generated skill, và dist output
- archive `forge-browse` + `forge-design` mà không update test suite đồng bộ sẽ tạo test-count regression và verify failures ngay ở tranche đầu

Guardrails bắt buộc:

- không weaken verification contract
- không silently change shipped bundle contract
- không xóa compat/augmentation layers nếu chưa audit usage
- mọi cleanup current docs phải giữ một current reading order rõ ràng
- mọi archive move phải để lại trail hoặc archive path đủ rõ để historical evidence vẫn truy được
- mọi tranche chạm shipped bundle path phải kết thúc bằng `build_release.py` cộng với dist `verify_bundle.py` cho cả 3 bundle hiện hành
- mọi tranche chạm docs spine hoặc core/overlay skill surface phải chạy `python scripts/generate_overlay_skills.py --check`
- archive package legacy không được land nếu chưa update hoặc archive đồng thời các tests browse/design liên quan

## Kết luận

V4 nên là một refactor tranche để giảm cồng kềnh và dư thừa, không phải feature expansion. Ưu tiên lớn nhất của V4 là `current source surface honesty`: source repo phải nói cùng một câu chuyện với shipped kernel-only product line. Ưu tiên tiếp theo là `state/routing maintainability`: lõi điều phối và continuity phải bớt nặng mà không mất độ chặt.

Nếu làm đúng, V4 sẽ không chỉ làm Forge trông gọn hơn. Nó sẽ làm Forge vận hành gần hơn đáng kể với đích mà repo đang theo đuổi: `Nhanh, Gọn, Chính Xác, Chặt Chẽ, Dễ Bảo Trì, Dễ Mở Rộng`.

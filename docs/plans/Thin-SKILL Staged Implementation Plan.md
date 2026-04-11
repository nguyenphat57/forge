# Thin-SKILL Staged Implementation Plan

Date: 2026-04-11
Status: implemented

## Summary
- Triển khai theo 2 pha trong cùng initiative:
  - `Phase 1 / C2`: giảm phình ngay bằng `thin core + compact overwrite adapter`.
  - `Phase 2 / C1`: chốt target state bằng `thin core + delta-only adapter + generated merged adapter SKILL`.
- Không đổi public CLI hay install command surface. Bundle ship ra vẫn có `SKILL.md` ở root như hiện tại.
- Dùng `dedicated composer` chỉ cho `SKILL.md`, không dùng generic template engine và không nhúng merge markers vào core doc.

## Key Changes

### Phase 1: Thin Core + Compact Overwrite
- Refactor `packages/forge-core/SKILL.md` thành bootstrap contract thật sự, chỉ giữ:
  - shared behavioral rules
  - compact routing/matrix đủ để agent nhớ
  - verification contract
  - skill laws
  - reference-map pointer
- Xóa khỏi core `SKILL.md` các phần lookup/inventory dài:
  - `Bundle Layout`
  - `Intent Detection`
  - `Complexity Assessment`
  - `Global Resilience`
  - `Error Translation` table
  - tooling inventory chi tiết
- Refactor adapter `overlay/SKILL.md` theo mô hình compact overwrite:
  - giữ host-specific sections
  - chỉ copy lại compact shared rules thật sự cần visible trong adapter bundle
  - không giữ lại các bảng lookup dài hoặc inventory tree
- Chuẩn hóa heading model của core để Phase 2 có thể compose theo section name cố định, không cần marker:
  - `Bootstrap Rules`
  - `Routing Contract`
  - `Verification Contract`
  - `Skill Laws`
  - `Reference Map`
- Cập nhật references để mọi pointer tooling/current đều đi qua `kernel-tooling.md`, không mở current source cạnh tranh.

### Phase 2: Generated Merged Adapter SKILL
- Thêm helper mới kiểu `scripts/skill_bundle_composer.py` để assemble `SKILL.md` cho adapter bundle.
- Chuyển adapter source-of-truth từ self-contained overlay skill sang delta source rõ nghĩa:
  - `packages/forge-codex/overlay/SKILL.delta.md`
  - `packages/forge-antigravity/overlay/SKILL.delta.md`
- Composer dùng fixed section import list từ core, không merge markdown tổng quát:
  - đọc frontmatter + host sections từ adapter delta
  - import shared sections từ core theo heading whitelist
  - append host-specific activation announcement ở cuối
- `build_release.py` gọi composer khi build adapter bundle, thay vì copy `overlay/SKILL.md` trực tiếp vào dist.
- Các helper staging/overlay test support cũng dùng composer để stage bundle root đúng như dist output.
- Sau Phase 2, adapter source không còn là self-contained `SKILL.md`; dist bundle vẫn ship `SKILL.md` self-contained.

### Final Contract And Budgets
- Hard budgets được khóa bằng test:
  - cuối Phase 1:
    - core `SKILL.md` `<= 240` lines
    - mỗi adapter compact overwrite `SKILL.md` `<= 220` lines
  - cuối Phase 2:
    - core `SKILL.md` `<= 200` lines
    - mỗi adapter `SKILL.delta.md` `<= 120` lines
    - mỗi dist adapter `SKILL.md` `<= 240` lines
- Không cho reintroduce các section removed vào thin source files trừ khi có decision doc mới.

## Interfaces And Contract Changes
- Public runtime contract:
  - không đổi tên file shipped; dist vẫn có `SKILL.md`
  - không đổi `build_release.py` CLI hay install surface
- Source repo contract:
  - Phase 1: adapter source vẫn là `overlay/SKILL.md`, nhưng compact
  - Phase 2: adapter source chuyển sang `overlay/SKILL.delta.md`; `overlay/SKILL.md` không còn là source-of-truth
- Build contract:
  - thêm dedicated `SKILL` composer, chỉ phục vụ bundle assembly cho adapter skills
  - không giới thiệu generic markdown merge framework
- Docs contract:
  - package READMEs và source-repo references phải nói rõ distinction giữa source delta artifact và merged dist `SKILL.md`

## Test Plan
- Source-contract tests:
  - assert core thin `SKILL.md` còn đủ heading bootstrap bắt buộc
  - assert removed lookup sections không quay lại
  - assert reference pointers dùng `kernel-tooling.md`
- Anti-dup tests:
  - Phase 1: chỉ cho phép adapter chứa whitelist compact shared block
  - Phase 2: adapter delta không được copy lại shared section bodies từ core
- Budget tests:
  - fail build nếu vượt line budgets đã chốt cho từng phase
- Build/output tests:
  - `build_release` vẫn tạo `dist/*/SKILL.md`
  - dist adapter `SKILL.md` phải chứa cả shared bootstrap và host-specific sections
  - source delta file không bị ship nguyên xi thành dist `SKILL.md`
- Regression tests cần cập nhật:
  - overlay/release tests đang đọc trực tiếp `overlay/SKILL.md`
  - staging helper tests cho Codex/Antigravity
  - contract tests cho bootstrap visibility và generated output shape
- Acceptance proof:
  - targeted unittest cho source contracts + overlay/build contracts
  - `python scripts/build_release.py --format json`
  - `python scripts/verify_repo.py --format json`

## Assumptions
- Chọn hướng staged trong cùng initiative: lấy maintenance win ngay ở Phase 1, rồi hoàn tất kiến trúc sạch hơn ở Phase 2.
- Chọn `dedicated composer` là mechanism cho C1; không dùng merge markers và không xây generic template engine.
- Budget tests là hard gate, không phải soft reporting.
- Nếu Phase 1 cho thấy core/adapters vẫn vượt budget dù đã bỏ đúng sections, implementer được phép rút thêm prose diễn giải nhưng không được rút các guardrails bootstrap đã khóa trong plan này.

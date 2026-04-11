# Brainstorm: Thin SKILL.md

Date: 2026-04-11
Status: historical brainstorm

## Vấn đề

SKILL.md phình to theo thời gian. Mỗi feature mới đều thêm prose, table, hoặc listing vào SKILL.md thay vì cập nhật registry hoặc references.

Hiện trạng:

| File | Size | Lines |
|------|------|-------|
| forge-core/SKILL.md | 22.3 KB | 408 |
| forge-antigravity/overlay/SKILL.md | 27.0 KB | 486 |
| forge-codex/overlay/SKILL.md | 24.5 KB | ~450 |

Agent đọc 1 file adapter SKILL.md đã merge core (~25-27 KB, ~7,000 tokens) trước khi làm bất cứ gì. Context window bị chiếm ngay từ đầu.

## Nguyên nhân gốc

### Triple duplication

3 file SKILL.md chia sẻ ~80% nội dung. Các section sau giống hệt hoặc gần hệt giữa core, antigravity, và codex:

- Intent Detection table — giống hệt, đã có trong `orchestrator-registry.json`
- Complexity Assessment table — giống hệt, đã có trong registry
- Skill Composition Matrix — giống hệt, đã có trong registry chains
- How to load skills — giống hệt
- Skill Registry table — near-identical
- Verification Strategy — giống hệt
- Golden Rules — giống hệt
- Error Translation table — giống hệt, đã có trong `references/error-translation.md`
- Global Resilience — giống hệt
- Solo Profile contract — giống hệt
- Executable Tooling listing — mostly same, adapter thêm vài dòng
- Bundle Layout tree — mỗi adapter copy lại + sửa nhẹ

### Registry đã chứa data

`orchestrator-registry.json` (33 KB) chứa intent keywords, chains, complexity thresholds, brainstorm gate, spec-review gate, stage statuses, profiles, operator surface actions — tất cả giống hệt các tables trong SKILL.md.

### References đã chứa prose

- `references/error-translation.md` + `scripts/translate_error.py` → Error Translation table
- `references/tooling.md` (24 KB) → Executable Tooling listing
- `references/execution-delivery.md` → Verification strategy prose
- `references/reference-map.md` → index toàn bộ references

Kết luận: ~60-65% nội dung SKILL.md là lookup data hoặc prose đã tồn tại ở nơi khác.

## Giải pháp đề xuất: Thin-SKILL Contract-Only

SKILL.md chỉ chứa decision contract — agent đọc SKILL.md để biết nguyên tắc và cách ra quyết định, không phải để tra bảng. Mọi lookup data sống trong registry, mọi instructional prose sống trong references.

### Nội dung giữ lại trong SKILL.md

| Section | Lý do giữ | Size ước tính |
|---------|----------|--------------|
| Golden Rules | Behavioral guardrail — agent cần nhớ liên tục | 7 dòng |
| Iron Laws per skill | Behavioral guardrail — 1 dòng/skill, enforcement | ~20 dòng |
| Verification Strategy | Behavioral — agent hay skip nếu không thấy | 8 dòng |
| Skill Composition Matrix | Core routing decision — giữ compact | ~10 dòng |
| Skill loading procedure | Decision logic, không phải data | 14 dòng |
| Host Protocol Bridge | Host-specific, không duplicate | ~15 dòng |
| Operator Surface table | Host-specific, không duplicate | ~10 dòng |
| Independence Rule | Behavioral | 4 dòng |
| Response Personalization | Host-specific pointer + key rules | ~5 dòng |
| References pointer | Entry point cho lazy-load | 5 dòng |

### Nội dung chuyển ra ngoài

| Section | Chuyển đến | Lý do |
|---------|-----------|-------|
| Intent Detection table | `data/orchestrator-registry.json` | Lookup data, đã có trong registry |
| Complexity Assessment table | `data/orchestrator-registry.json` | Lookup data, đã có trong registry |
| Error Translation table | `references/error-translation.md` | Lookup data, đã có trong reference |
| Bundle Layout tree | Xóa — observable từ filesystem | Pure enumeration, không chứa decision |
| Executable Tooling listing | `references/tooling.md` | Detailed listing, đã có trong reference |
| Global Resilience prose | `references/execution-delivery.md` | Instructional prose, rarely referenced |
| Detailed personalization rules | `references/personalization.md` | Instructional prose |

### Kết quả ước tính

| Metric | Trước | Sau |
|--------|-------|-----|
| Adapter SKILL.md size | ~27 KB | ~8 KB |
| Context cost | ~7,000 tokens | ~2,000 tokens |
| Giảm | | **~70%** |

## Ưu điểm

### Context window cost giảm mạnh

~27 KB → ~8 KB = tiết kiệm ~5,000 tokens mỗi conversation cho actual work. Với conversation dài, accumulated cost rất đáng kể.

### Single source of truth

Sửa Intent table phải sửa 3 nơi (core SKILL, AG overlay, Codex overlay) + registry → chỉ sửa registry. SKILL.md không chứa data nên không cần sync. Giảm triệt để "docs drift" — vấn đề Forge đã gặp nhiều lần.

### Forge grow mà SKILL.md không phình

Thêm workflow mới → update registry + tạo workflow file, SKILL.md chỉ thêm 1 dòng Iron Law. Thêm operator action → update registry, SKILL.md không đổi. Đây là gain dài hạn quan trọng nhất vì SKILL.md phình chính vì mỗi feature mới đều copy thêm prose.

### Adapter overlay đơn giản hơn

Overlay SKILL.md chỉ chứa host-specific contract (~2-3 KB), merge với core thin-SKILL (~6 KB) = ~8 KB. Codex wrapper dedup (V2 Phase 3 pending) tự nhiên được giải quyết.

## Nhược điểm

### Agent phải follow pointers

Khi SKILL.md nói "See registry for intent keywords", agent phải tự mở file đó. Agent hay suy luận thay vì tra cứu khi pointer yêu cầu thêm 1 bước đọc file. Rủi ro cụ thể: agent route sai intent vì không mở registry mà dựa vào memory.

Mitigation: giữ Skill Composition Matrix inline vì đây là quyết định routing quan trọng nhất, chỉ delegate lookup data mà agent không cần mỗi conversation.

### Smoke test cần viết lại

Smoke matrix validators verify rằng SKILL.md chứa các section cụ thể (Intent Detection, Complexity...). Xóa sections đó thì tests FAIL, phải rewrite test expectations. Không khó nhưng là effort thật.

### Hai bước đọc thay vì một

Agent đọc SKILL.md → cần detail → mở reference/registry → mới bắt đầu. Latency tăng nhẹ ở bước routing ban đầu. Nhưng thực tế agent hiếm khi cần tra Intent table — routing dựa vào pattern matching tự nhiên.

### Risk hành vi drift nếu thin quá

Golden Rules + Iron Laws là behavioral guardrails — nếu bỏ khỏi SKILL.md, agent sẽ không enforce. Verification Strategy prose ngắn nhưng critical — bỏ ra ngoài thì agent hay skip verification.

Ranh giới: nội dung agent cần nhớ liên tục (rules, laws, strategy) → giữ inline. Nội dung agent chỉ cần tra khi cần (tables, lists, paths) → delegate.

### Khó measure chất lượng routing

Sau khi slim, làm sao biết agent vẫn route đúng? Smoke matrix chỉ test deterministic script `route_preview.py`, không test agent behavior thật.

Mitigation: chạy vài conversation thử trước/sau, so sánh routing quality qua Skill selection header.

## Ranh giới quyết định

| Inline (agent cần nhớ liên tục) | Delegate (agent tra khi cần) |
|--------------------------------|------------------------------|
| Golden Rules | Intent keyword table |
| Iron Laws per skill | Complexity threshold table |
| Verification Strategy | Error Translation table |
| Skill loading procedure | Bundle Layout tree |
| Host Protocol Bridge | Executable Tooling listing |
| Operator Surface table | Global Resilience prose |
| Skill Composition Matrix | Detailed personalization rules |

## Các giải pháp thay thế đã cân nhắc

### Approach A: Trim duplicates only (conservative)

Giữ structure, chỉ xóa sections giống hệt registry. Kết quả: ~18 KB (giảm 33%). Ít risk nhưng vẫn lớn, không giải quyết duplication giữa core/adapter, không scale.

### Approach B: Adapter inherits, core shrinks (moderate)

Core SKILL.md chỉ chứa contract, adapter chỉ chứa host diff + pointer. Kết quả: shipped ~14 KB (giảm 50%). Giải quyết duplication nhưng cần test overlay merge behavior.

### Approach D: Pure pointer (radical)

SKILL.md chỉ còn 20-30 dòng: frontmatter + golden rules + pointer. Kết quả: ~2-3 KB. Quá radical — agent mất context chính, behavioral drift risk cao, Golden Rules + Iron Laws cần inline.

## Kết luận

Approach C (Thin-SKILL Contract-Only) cân bằng tốt nhất giữa giảm size (~70%), giữ behavioral safety (inline rules + laws), và scale dài hạn (thêm feature không phình file). Rủi ro chính (agent không follow pointer) được mitigation bằng cách giữ Composition Matrix inline — quyết định routing quan trọng nhất không bị delegate.

# Forge Error Translation

> Dung khi can bien stderr/raw error thanh mot tom tat de doc hon, nhung van giu du context ky thuat de debug tiep.

## Muc tieu

- match cac error pattern pho bien mot cach deterministic
- redact secret, token, va duong dan nhay cam truoc khi show lai
- tra ve `human_message` + `suggested_action` de `run`, `debug`, `build`, va `test` co the reuse

## Canonical Script

```powershell
python scripts/translate_error.py --error-text "Module not found: payments.service"
python scripts/translate_error.py --input-file C:\path\to\stderr.txt --format json
```

## Output Contract

- `status`: `PASS` neu match duoc pattern da biet, `WARN` neu fallback generic
- `translation.category`
- `translation.human_message`
- `translation.suggested_action`
- `translation.error_excerpt` sau khi redact

## Current Categories

- `module`
- `database`
- `runtime`
- `network`
- `timeout`
- `test`
- `build`
- `git`
- `deploy`
- `generic`

## Boundary

- Core chi lo translation deterministic va sanitation co ban.
- Adapter co the doi cach present cho user, nhung khong duoc fork pattern database hay category semantics.
- Neu can mot pattern moi, them vao core thay vi patch rieng trong tung host.

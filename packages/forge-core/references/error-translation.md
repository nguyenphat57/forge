# Forge Error Translation

> Dùng khi cần biến stderr/raw error thành một tóm tắt dễ đọc hơn, nhưng vẫn giữ đủ context kỹ thuật để debug tiếp.

## Mục tiêu

- match các error pattern phổ biến một cách deterministic
- redact secret, token, và đường dẫn nhạy cảm trước khi show lại
- trả về `human_message` + `suggested_action` để `run`, `debug`, `build`, và `test` có thể reuse

## Canonical Script

```powershell
python scripts/translate_error.py --error-text "Module not found: payments.service"
python scripts/translate_error.py --input-file C:\path\to\stderr.txt --format json
```

## Output Contract

- `status`: `PASS` nếu match được pattern đã biết, `WARN` nếu fallback generic
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

- Core chỉ lo translation deterministic và sanitation cơ bản.
- Adapter có thể đổi cách present cho user, nhưng không được fork pattern database hay category semantics.
- Nếu cần một pattern mới, thêm vào core thay vì patch riêng trong từng host.

# Forge Run Guidance

> Dùng khi cần một lớp `run` host-neutral: thực thi command thật, tóm tắt signal chính, và route sang workflow tiếp theo thay vì chỉ dump terminal.

## Mục tiêu

- chạy command thật trong workspace user chỉ định
- capture output chính, timeout, và ready-signal
- classify command thành `build`, `serve`, `deploy`, hoặc `generic`
- gợi ý workflow tiếp theo phù hợp: `test`, `debug`, hoặc `deploy`

## Canonical Script

```powershell
python scripts/run_with_guidance.py --workspace C:\path\to\workspace --timeout-ms 20000 -- npm run dev
python scripts/run_with_guidance.py --workspace C:\path\to\workspace --format json -- python -m pytest tests/unit
```

## Input Contract

- `--workspace`: root mà command sẽ chạy trong đó
- `--timeout-ms`: timeout budget
- command phải được truyền sau `--`

## Output Contract

Script trả về:

- `status`: `PASS` hoặc `FAIL`
- `state`: `completed`, `running`, `failed`, hoặc `timed-out`
- `command_kind`: `build`, `serve`, `deploy`, `generic`
- `suggested_workflow`
- `recommended_action`
- `stdout_excerpt` / `stderr_excerpt`
- `evidence`
- `readiness_detected`

## Routing Semantics

- `build` thành công -> `test`
- `serve` có ready-signal và còn sống sau timeout -> `test`
- `deploy` thành công -> `deploy` để tiếp tục post-deploy verification
- command fail hoặc timeout không có ready-signal -> `debug`

## Persisted Artifacts

Nếu dùng `--persist`, artifact mặc định nằm ở:

```text
.forge-artifacts/run-reports/
```

## Adapter Boundary

- Core chỉ lo command execution + deterministic guidance.
- Adapter có thể thêm slash wrapper, natural-language wrapper, hay host UX riêng.
- Adapter không được đổi meaning của `state`, `command_kind`, hay `suggested_workflow`.

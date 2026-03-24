# Forge Run Guidance

> Dung khi can mot lop `run` host-neutral: thuc thi command that, tom tat signal chinh, va route sang workflow tiep theo thay vi chi dump terminal.

## Muc tieu

- chay command that trong workspace user chi dinh
- capture output chinh, timeout, va ready-signal
- classify command thanh `build`, `serve`, `deploy`, hoac `generic`
- goi y workflow tiep theo phu hop: `test`, `debug`, hoac `deploy`

## Canonical Script

```powershell
python scripts/run_with_guidance.py --workspace C:\path\to\workspace --timeout-ms 20000 -- npm run dev
python scripts/run_with_guidance.py --workspace C:\path\to\workspace --format json -- python -m pytest tests/unit
```

## Input Contract

- `--workspace`: root ma command se chay trong do
- `--timeout-ms`: timeout budget
- command phai duoc truyen sau `--`

## Output Contract

Script tra ve:

- `status`: `PASS` hoac `FAIL`
- `state`: `completed`, `running`, `failed`, hoac `timed-out`
- `command_kind`: `build`, `serve`, `deploy`, `generic`
- `suggested_workflow`
- `recommended_action`
- `stdout_excerpt` / `stderr_excerpt`
- `evidence`
- `readiness_detected`

## Routing Semantics

- `build` thanh cong -> `test`
- `serve` co ready-signal va con song sau timeout -> `test`
- `deploy` thanh cong -> `deploy` de tiep tuc post-deploy verification
- command fail hoac timeout khong co ready-signal -> `debug`

## Persisted Artifacts

Neu dung `--persist`, artifact mac dinh nam o:

```text
.forge-artifacts/run-reports/
```

## Adapter Boundary

- Core chi lo command execution + deterministic guidance.
- Adapter co the them slash wrapper, natural-language wrapper, hay host UX rieng.
- Adapter khong duoc doi meaning cua `state`, `command_kind`, hay `suggested_workflow`.

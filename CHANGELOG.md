# Changelog

## 0.3.0 - 2026-03-24

- Them Wave A / P1.1 voi error translator host-neutral va noi truc tiep vao `run` de bien loi ky thuat thanh guidance de doc va xu ly.
- Them Wave A / P1.2 voi bump workflow dung chung qua `prepare_bump.py`, cap nhat `VERSION`, changelog, va release checklist theo mot contract duy nhat.
- Them Wave A / P1.3 voi rollback guidance engine qua `resolve_rollback.py`, phan loai deploy/config/migration/code-change va de xuat buoc xu ly an toan.
- Nang full regression, smoke matrix, va adapter wiring de Antigravity runtime va Codex runtime cung ke thua tron bo Wave A tu core.


## 0.2.0 - 2026-03-24

- Them Wave A / P0.1 voi preferences engine host-neutral cho `technical_level`, `detail_level`, `autonomy_level`, va `personality`.
- Them Wave A / P0.2 voi help-next navigator repo-first dung chung cho `forge-antigravity` va `forge-codex`.
- Them Wave A / P0.3 voi run-guidance engine de chay lenh that, detect ready-signal, va route tiep sang `test`, `debug`, hoac `deploy`.
- Mo rong regression, smoke matrix, va adapter wiring de ca Antigravity runtime lan Codex runtime deu ke thua cung contract cua core.

## 0.1.0 - 2026-03-24

- Tách Forge thành monorepo `forge-core + forge-antigravity + forge-codex`.
- Thêm release pipeline chuẩn với `build_release.py`, `verify_repo.py`, và `install_bundle.py`.
- Chuẩn hóa `forge-core` theo hướng host-neutral, giữ host-specific entrypoints trong adapter overlays.
- Thêm test cấp monorepo cho build/install/version flow và release documentation.

# Changelog

## 0.5.0 - 2026-03-24

- Them Wave C cho `forge-codex` voi thin wrappers cho `help`, `next`, `run`, `bump`, `rollback`, `customize`, va `init`.
- Cap nhat `AGENTS.example.md` va adapter docs de Codex giu natural-language first, slash chi la alias optional, va khong duplicate orchestration rules cua Forge.
- Bo sung `codex-operator-surface.md` va release tests de build/install giu nguyen Codex overlay sau moi lan release.


## 0.4.0 - 2026-03-24

- Them Wave B cho `forge-antigravity` voi operator wrappers cho `help`, `next`, `run`, `bump`, `rollback`, `customize`, `init`, va session handover flows.
- Mo rong `forge-core` voi preference persistence qua `write_preferences.py`, them `pace` va `feedback_style`, va workspace bootstrap reusable qua `initialize_workspace.py`.
- Hardening `install_bundle.py` theo huong sync in-place de rollout an toan tren Windows ngay ca khi thu muc runtime dang bi host lock.
- Tang verify coverage cho release/install va bo sung regression, smoke, va overlay checks cho Wave B.


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

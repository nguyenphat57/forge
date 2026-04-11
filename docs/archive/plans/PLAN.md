Status: implemented

# Giảm tải Forge operator surface theo hướng UX-first

## Tóm tắt

- Chuẩn hóa source-repo operator surface quanh repo-root `scripts/`.
- Giữ `packages/forge-core/scripts/*` là engine-internal implementation surface.
- Dùng registry hiện có để điều khiển primary-vs-compat alias posture cho Codex và Antigravity.
- Tập trung vào UX, docs, generated artifacts, và discoverability; không thay topology dist/install/runtime.

## Public interfaces và source of truth

- Canonical source-repo operator surface:
  - `python scripts/resolve_help_next.py --workspace <workspace> --mode help`
  - `python scripts/resolve_help_next.py --workspace <workspace> --mode next`
  - `python scripts/run_with_guidance.py --workspace <workspace> --timeout-ms 20000 -- <command>`
  - `python scripts/session_context.py resume --workspace <workspace> --format json`
  - `python scripts/session_context.py save --workspace <workspace> --format json`
  - `python scripts/session_context.py save --workspace <workspace> --write-handover --format json`
  - `python scripts/prepare_bump.py --workspace <workspace> <version|major|minor|patch>`
  - `python scripts/resolve_rollback.py --workspace <workspace> --scope <scope>`
  - `python scripts/resolve_preferences.py --workspace <workspace> --format json`
  - `python scripts/write_preferences.py`
  - `python scripts/initialize_workspace.py --workspace <workspace>`
- `delegate` vẫn là workflow-only surface và tiếp tục route qua `workflows/execution/dispatch-subagents.md`.
- `packages/forge-core/data/orchestrator-registry.json` là machine-readable source of truth; overlays chỉ bổ sung host-specific alias posture.

## Thay đổi chính

- Thêm `operator_surface.actions` và `operator_surface.session_modes` vào registry với metadata cho repo entrypoint, core engine entrypoint, workflow, host visibility, primary aliases, compatibility aliases, natural-language examples, deprecation line, và status.
- Dùng registry đó để render:
  - generated `AGENTS.global.md`
  - generated `GEMINI.global.md`
  - generated Codex operator surface reference
  - generated Antigravity operator surface reference
- Chuẩn hóa vocabulary core/session sang `resume`, `save context`, `handover`; slash aliases legacy chỉ còn là compatibility surface ở Antigravity.
- Mở rộng workspace-local `AGENTS.md` để Codex source repo entrypoint đầy đủ cho `resume/save/handover/help/next/run/bump/rollback/customize/init`.
- Cập nhật `map_codebase` để phát hiện repo-root operator entrypoints và AGENTS-declared operator surface như entrypoints hợp lệ.
- Tách docs/install thành hai happy paths rõ ràng:
  - source repo operator flow
  - installed runtime flow

## Verification

- Registry contract tests cho operator surface metadata và deprecation posture.
- Generated-host-artifact tests cho registry-driven operator surface docs.
- Source-repo wrapper tests cho local `AGENTS.md` và root scripts.
- Bundle overlay tests cho Codex primary surface và Antigravity compatibility surface.
- `map_codebase` tests cho discoverability của repo-root operator entrypoints.

## Kết quả mong muốn

- Codex giữ surface gọn, tự nhiên, không quảng bá `/recap` hoặc `/save-brain`.
- Antigravity vẫn tương thích với `/recap`, `/save-brain`, `/handover`, nhưng các alias này luôn bị hạ xuống compatibility-only surface và có deprecation warning.
- Forge source repo tự mô tả đúng operator entrypoints thay vì rơi về `Entrypoints: (none)`.

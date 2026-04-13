# Forge Core 9.3+ Closure Plan

## Summary
- Mục tiêu: đưa `forge-core` tiến rõ ràng tới `9.3+` bằng cách làm nó `lean, closed, maintenance-only`, không phải bằng cách thêm product surface mới.
- Cách làm: triển khai theo `3 tranche` landable độc lập, với hướng chính là tách rõ `repo operator surface` khỏi `host public surface`, sau đó khóa chúng bằng generation + drift tests.
- Non-goals: không thêm workflow mới, không đổi stage order, không đổi routing semantics, không mở thêm bundle line, không đổi host capabilities.

## Public Contracts And Interface Changes
- Giữ `scripts/repo_operator.py <action>` là repo entrypoint duy nhất.
- Thu gọn public repo surface của `repo_operator.py` còn: `resume`, `save`, `handover`, `help`, `next`, `bootstrap`, `run`, `bump`, `rollback`, `customize`, `init`.
- Demote `capture-continuity` khỏi public repo surface: bỏ action này khỏi `scripts/repo_operator.py` và khỏi `docs/current/operator-surface.md`; giữ `packages/forge-core/scripts/capture_continuity.py` như internal engine tool.
- Giữ `bootstrap` là repo-only maintenance action; không đưa nó vào host public surfaces.
- Giữ host public surface như contract cross-host riêng: `help`, `next`, `run`, `delegate`, `bump`, `rollback`, `customize`, `init`, cùng session modes `restore`, `save`, `handover`.

## Implementation Changes
### Tranche 1 - Surface Split And Closure
- Tách machine-readable contract trong `packages/forge-core/data/orchestrator-registry.json` thành hai phần rõ ràng: `repo_operator_surface` và `host_operator_surface`.
- Dùng cùng một schema metadata cho cả hai phần để renderer và tests không phải giữ hai logic khác nhau.
- `repo_operator_surface` phải model đúng những gì `scripts/repo_operator.py` hỗ trợ; `host_operator_surface` phải model đúng những gì Codex và Antigravity public ra cho người dùng.
- Xóa `capture-continuity` khỏi `scripts/repo_operator.py`, usage text, và current repo-operator doc; không để compat alias.
- Giữ `bootstrap` chỉ ở `repo_operator_surface` và `AGENTS.md`; không để nó xuất hiện trong Codex hay Antigravity operator references.

### Tranche 2 - Generated Surface Unification
- Chuyển `docs/current/operator-surface.md` thành artifact được render từ `repo_operator_surface` cộng với một preamble ngắn cố định; không hand-maintain danh sách action nữa.
- Giữ Codex và Antigravity operator references chỉ đọc từ `host_operator_surface`; mọi action/session enumeration trong generated host references phải đi qua `scripts/operator_surface_support.py`.
- Mở rộng manifest/generation pass hiện có để cùng kiểm tra `docs/current/operator-surface.md` với host artifacts; không tạo generator mới.
- Chuẩn hóa renderer trong `scripts/operator_surface_support.py` để một reader chung sinh ra cả repo doc và host docs, thay vì mỗi surface tự kể lại cùng contract theo cách riêng.

### Tranche 3 - Maintenance Gates
- Thêm drift tests fail-fast khi có action/session/workflow/stage/bundle mới mà chưa được khai báo ở contract chính và chưa cập nhật current docs hoặc release package matrix tương ứng.
- Thêm invariant tests:
- repo-only actions không được xuất hiện trong host public surfaces
- host-only actions không được xuất hiện trong repo dispatcher surface
- current repo operator doc không được reintroduce direct core-script guidance ngoài `repo_operator.py`
- Giữ `docs/current/` ở spine hiện tại; không mọc thêm live-current surfaces ngoài boundary đã chốt trừ khi reopen rule được cập nhật rõ trong target-state.

## Test Plan
- `python scripts/generate_host_artifacts.py --check --format json`
- `python -m unittest discover -s tests -p test_generated_host_artifacts.py -v`
- `python -m unittest discover -s tests -p test_operator_surface_registry.py -v`
- `python -m unittest discover -s tests -p test_repo_operator_script_shims.py -v`
- `python -m unittest discover -s tests -p release_repo_test_overlays.py -v`
- `python -m unittest discover -s tests -p test_contracts.py -v` from `packages/forge-core`
- `python scripts/verify_repo.py --profile fast`

## Acceptance Scenarios
- `docs/current/operator-surface.md` liệt kê `bootstrap`, nhưng không liệt kê `delegate` hoặc `capture-continuity`.
- Codex và Antigravity operator-surface references liệt kê `delegate`, nhưng không liệt kê `bootstrap` hoặc `capture-continuity`.
- `scripts/repo_operator.py` reject `capture-continuity` như unknown action sau khi demote.
- `AGENTS.md` vẫn trỏ đúng các repo actions qua `scripts/repo_operator.py`, bao gồm `bootstrap`.
- Generation check và fast verification đều xanh sau khi split contract.

## Assumptions
- Điểm `9.3+` được nâng bằng closure, coherence, và maintenance discipline, không phải bằng breadth.
- Chấp nhận một thay đổi public nhỏ ở repo surface là bỏ `capture-continuity` khỏi `repo_operator.py`.
- `bootstrap` vẫn đáng giữ như repo-only maintenance utility trong giai đoạn hiện tại vì workflow-state vẫn còn bootstrap path từ sidecars cũ.
- Không thay đổi semantics của chains, packet contract, workflow-state vocabulary, hay shipped three-bundle line.

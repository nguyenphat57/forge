from __future__ import annotations

from typing import Iterable

from common import slugify


REQUIRED_PACKET_FIELDS = (
    "packet_id",
    "depends_on_packets",
    "owned_files_or_write_scope",
    "write_scope_conflicts",
    "merge_target",
    "merge_strategy",
    "completion_gate",
    "verification_to_rerun",
)
SAFE_COMPLETION_GATES = {"review-ready", "merge-ready"}
BLOCKED_COMPLETION_GATES = {"blocked"}
ACTIVE_PACKET_STATUSES = {"active", "running"}
PASSING_RUN_REPORT_STATES = {"completed", "running"}


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _normalize_scope_token(value: object) -> str:
    text = str(value).strip().replace("\\", "/")
    while "//" in text:
        text = text.replace("//", "/")
    return text.rstrip("/").casefold()


def _scope_overlaps(left: str, right: str) -> bool:
    if not left or not right:
        return False
    return left == right or left.startswith(f"{right}/") or right.startswith(f"{left}/")


def _packet_scopes(packet: dict) -> list[str]:
    return [_normalize_scope_token(item) for item in packet["owned_files_or_write_scope"]]


def _packet_conflicts(left: dict, right: dict) -> bool:
    left_scopes = _packet_scopes(left)
    right_scopes = _packet_scopes(right)
    return any(_scope_overlaps(left_scope, right_scope) for left_scope in left_scopes for right_scope in right_scopes)


def _normalize_packet(raw_packet: dict) -> dict:
    if not isinstance(raw_packet, dict):
        raise ValueError("Wave packets must be JSON objects.")
    missing = [field for field in REQUIRED_PACKET_FIELDS if field not in raw_packet]
    if missing:
        raise ValueError(f"Wave packet '{raw_packet.get('packet_id', '(unknown)')}' is missing required fields: {', '.join(missing)}.")
    packet_id = raw_packet.get("packet_id")
    if not isinstance(packet_id, str) or not packet_id.strip():
        raise ValueError("Wave packets require a non-empty packet_id.")
    owned_scope = _string_list(raw_packet.get("owned_files_or_write_scope"))
    if not owned_scope:
        raise ValueError(f"Wave packet '{packet_id}' requires owned_files_or_write_scope.")
    verification_to_rerun = _string_list(raw_packet.get("verification_to_rerun"))
    if not verification_to_rerun:
        raise ValueError(f"Wave packet '{packet_id}' requires verification_to_rerun.")
    merge_strategy = raw_packet.get("merge_strategy")
    if not isinstance(merge_strategy, str) or not merge_strategy.strip():
        raise ValueError(f"Wave packet '{packet_id}' requires merge_strategy.")
    completion_gate = raw_packet.get("completion_gate")
    if not isinstance(completion_gate, str) or not completion_gate.strip():
        raise ValueError(f"Wave packet '{packet_id}' requires completion_gate.")
    return {
        "packet_id": packet_id.strip(),
        "goal": raw_packet.get("goal", packet_id.strip()),
        "depends_on_packets": sorted(set(_string_list(raw_packet.get("depends_on_packets")))),
        "owned_files_or_write_scope": owned_scope,
        "write_scope_conflicts": _string_list(raw_packet.get("write_scope_conflicts")),
        "overlap_risk_status": raw_packet.get("overlap_risk_status", "none"),
        "merge_target": raw_packet.get("merge_target"),
        "merge_strategy": merge_strategy.strip(),
        "completion_gate": completion_gate.strip(),
        "verification_to_rerun": verification_to_rerun,
    }


def _validate_dependencies(packets: dict[str, dict]) -> None:
    missing: list[str] = []
    for packet in packets.values():
        for dependency in packet["depends_on_packets"]:
            if dependency not in packets:
                missing.append(f"{packet['packet_id']} -> {dependency}")
    if missing:
        raise ValueError(f"Wave packet graph has missing dependency: {sorted(missing)[0]}.")

    states: dict[str, int] = {}
    stack: list[str] = []

    def visit(packet_id: str) -> None:
        state = states.get(packet_id, 0)
        if state == 1:
            cycle = " -> ".join([*stack, packet_id])
            raise ValueError(f"Wave packet graph has cycle: {cycle}.")
        if state == 2:
            return
        states[packet_id] = 1
        stack.append(packet_id)
        for dependency in packets[packet_id]["depends_on_packets"]:
            visit(dependency)
        stack.pop()
        states[packet_id] = 2

    for packet_id in sorted(packets):
        visit(packet_id)


def _maximum_non_overlapping_subset(packet_ids: Iterable[str], packets: dict[str, dict]) -> list[str]:
    ordered = sorted(set(packet_ids))
    conflicts = {
        packet_id: {
            other_id
            for other_id in ordered
            if other_id != packet_id and _packet_conflicts(packets[packet_id], packets[other_id])
        }
        for packet_id in ordered
    }
    best: list[str] = []

    def search(index: int, current: list[str]) -> None:
        nonlocal best
        if index >= len(ordered):
            if len(current) > len(best) or (len(current) == len(best) and current < best):
                best = list(current)
            return
        remaining = len(ordered) - index
        if len(current) + remaining < len(best):
            return
        candidate = ordered[index]
        if not conflicts[candidate].intersection(current):
            current.append(candidate)
            search(index + 1, current)
            current.pop()
        search(index + 1, current)

    search(0, [])
    return best


def _build_waves(packets: dict[str, dict]) -> list[list[str]]:
    remaining = set(packets)
    completed_dependencies: set[str] = set()
    waves: list[list[str]] = []
    while remaining:
        ready = sorted(
            packet_id
            for packet_id in remaining
            if set(packets[packet_id]["depends_on_packets"]).issubset(completed_dependencies)
        )
        if not ready:
            unresolved = ", ".join(sorted(remaining))
            raise ValueError(f"Wave packet graph could not resolve a ready set for: {unresolved}.")
        wave = _maximum_non_overlapping_subset(ready, packets)
        if not wave:
            raise ValueError("Wave packet graph could not build a non-overlapping ready wave.")
        waves.append(wave)
        remaining.difference_update(wave)
        completed_dependencies.update(wave)
    return waves


def _blocked_by_packet_contract(packet: dict) -> bool:
    return packet["completion_gate"] in BLOCKED_COMPLETION_GATES or bool(packet["write_scope_conflicts"]) or packet.get("overlap_risk_status") == "blocked"


def _status_from_progress(packet: dict, progress: dict | None, existing: dict | None) -> dict:
    existing = existing if isinstance(existing, dict) else {}
    if _blocked_by_packet_contract(packet):
        return {
            "status": "blocked",
            "completion_gate": "blocked",
            "reason": "packet-contract-blocked",
        }
    if isinstance(progress, dict):
        completion_gate = progress.get("completion_gate")
        if not isinstance(completion_gate, str) or not completion_gate.strip():
            completion_state = progress.get("completion_state")
            if completion_state == "ready-for-merge":
                completion_gate = "merge-ready"
            elif completion_state == "ready-for-review":
                completion_gate = "review-ready"
            elif completion_state == "blocked-by-residual-risk":
                completion_gate = "blocked"
            else:
                completion_gate = "incomplete"
        if completion_gate in SAFE_COMPLETION_GATES:
            return {
                "status": "completed",
                "completion_gate": completion_gate,
                "reason": "persisted-safe-gate",
            }
        if (
            progress.get("status") == "blocked"
            or progress.get("completion_state") == "blocked-by-residual-risk"
            or completion_gate in BLOCKED_COMPLETION_GATES
            or progress.get("overlap_risk_status") == "blocked"
            or _string_list(progress.get("write_scope_conflicts"))
        ):
            return {
                "status": "blocked",
                "completion_gate": "blocked",
                "reason": "persisted-blocker",
            }
        if progress.get("status") in ACTIVE_PACKET_STATUSES:
            return {
                "status": "running",
                "completion_gate": completion_gate,
                "reason": "persisted-active-progress",
            }
    existing_status = existing.get("status")
    if existing_status in {"completed", "blocked", "running"}:
        return {
            "status": existing_status,
            "completion_gate": existing.get("completion_gate", packet["completion_gate"]),
            "reason": existing.get("reason", "persisted-wave-state"),
        }
    if packet["completion_gate"] in SAFE_COMPLETION_GATES:
        return {
            "status": "completed",
            "completion_gate": packet["completion_gate"],
            "reason": "packet-contract-safe-gate",
        }
    return {
        "status": "pending",
        "completion_gate": packet["completion_gate"],
        "reason": "waiting-for-wave",
    }


def _common_field(packet_ids: Iterable[str], packets: dict[str, dict], field: str) -> object:
    values = {packets[packet_id].get(field) for packet_id in packet_ids}
    values.discard(None)
    if len(values) == 1:
        return next(iter(values))
    return None


def _shared_verification(packet_ids: Iterable[str], packets: dict[str, dict]) -> list[str]:
    verification: list[str] = []
    for packet_id in packet_ids:
        for command in packets[packet_id]["verification_to_rerun"]:
            if command not in verification:
                verification.append(command)
    return verification


def _latest_progress_mtime(packet_ids: Iterable[str], progress_by_packet: dict[str, dict]) -> float:
    latest = 0.0
    for packet_id in packet_ids:
        progress = progress_by_packet.get(packet_id)
        if not isinstance(progress, dict):
            continue
        artifact_mtime = progress.get("_artifact_mtime")
        if isinstance(artifact_mtime, (int, float)) and float(artifact_mtime) > latest:
            latest = float(artifact_mtime)
    return latest


def _wave_verification_state(
    packet_ids: Iterable[str],
    packets: dict[str, dict],
    packet_statuses: dict[str, dict],
    progress_by_packet: dict[str, dict],
    run_reports_by_command: dict[str, dict],
) -> dict:
    commands = _shared_verification(packet_ids, packets)
    if not commands:
        return {
            "status": "not-needed",
            "commands": [],
            "pending_commands": [],
            "satisfied_commands": [],
        }

    if not all(packet_statuses[packet_id]["status"] == "completed" for packet_id in packet_ids):
        return {
            "status": "not-ready",
            "commands": commands,
            "pending_commands": [],
            "satisfied_commands": [],
        }

    cutoff_mtime = _latest_progress_mtime(packet_ids, progress_by_packet)
    pending_commands: list[str] = []
    satisfied_commands: list[str] = []
    for command in commands:
        report = run_reports_by_command.get(command)
        if not isinstance(report, dict):
            pending_commands.append(command)
            continue
        if report.get("status") != "PASS" or report.get("state") not in PASSING_RUN_REPORT_STATES:
            pending_commands.append(command)
            continue
        report_mtime = report.get("_artifact_mtime")
        if isinstance(report_mtime, (int, float)) and float(report_mtime) < cutoff_mtime:
            pending_commands.append(command)
            continue
        satisfied_commands.append(command)
    return {
        "status": "satisfied" if not pending_commands else "pending",
        "commands": commands,
        "pending_commands": pending_commands,
        "satisfied_commands": satisfied_commands,
    }


def _recompute_wave_state(
    plan: dict,
    progress_by_packet: dict[str, dict] | None,
    run_reports_by_command: dict[str, dict] | None = None,
) -> dict:
    packets = {packet_id: _normalize_packet(packet) for packet_id, packet in dict(plan.get("packets", {})).items()}
    wave_ids = [list(wave.get("packet_ids", [])) for wave in plan.get("waves", [])]
    existing_statuses = plan.get("packet_statuses", {})
    latest_progress = progress_by_packet if isinstance(progress_by_packet, dict) else {}
    latest_runs = run_reports_by_command if isinstance(run_reports_by_command, dict) else {}
    packet_statuses: dict[str, dict] = {}
    for wave_index, packet_ids in enumerate(wave_ids):
        for packet_id in packet_ids:
            packet_status = _status_from_progress(packets[packet_id], latest_progress.get(packet_id), existing_statuses.get(packet_id))
            packet_status["wave_index"] = wave_index
            packet_statuses[packet_id] = packet_status

    completed_packets = sorted(packet_id for packet_id, status in packet_statuses.items() if status["status"] == "completed")
    blocked_packets = sorted(packet_id for packet_id, status in packet_statuses.items() if status["status"] == "blocked")
    current_wave: int | None = None
    ready_packets: list[str] = []
    running_packets: list[str] = []
    current_wave_ids: list[str] = []
    current_wave_blocked_packets: list[str] = []
    shared_verification: list[str] = []
    shared_verification_pending: list[str] = []
    shared_verification_satisfied: list[str] = []
    shared_verification_status = "not-needed"
    wave_verification_statuses: list[dict] = []

    for wave_index, packet_ids in enumerate(wave_ids):
        verification_state = _wave_verification_state(
            packet_ids,
            packets,
            packet_statuses,
            latest_progress,
            latest_runs,
        )
        wave_verification_statuses.append(
            {
                "wave_index": wave_index,
                "status": verification_state["status"],
                "commands": list(verification_state["commands"]),
                "pending_commands": list(verification_state["pending_commands"]),
                "satisfied_commands": list(verification_state["satisfied_commands"]),
            }
        )
        if all(packet_statuses[packet_id]["status"] == "completed" for packet_id in packet_ids):
            if verification_state["status"] == "pending":
                current_wave = wave_index
                current_wave_ids = list(packet_ids)
                shared_verification = list(verification_state["commands"])
                shared_verification_pending = list(verification_state["pending_commands"])
                shared_verification_satisfied = list(verification_state["satisfied_commands"])
                shared_verification_status = verification_state["status"]
                break
            continue
        current_wave = wave_index
        current_wave_ids = list(packet_ids)
        current_wave_blocked_packets = sorted(packet_id for packet_id in packet_ids if packet_statuses[packet_id]["status"] == "blocked")
        running_packets = sorted(packet_id for packet_id in packet_ids if packet_statuses[packet_id]["status"] == "running")
        ready_packets = sorted(packet_id for packet_id in packet_ids if packet_statuses[packet_id]["status"] == "pending")
        shared_verification = list(verification_state["commands"])
        shared_verification_pending = list(verification_state["pending_commands"])
        shared_verification_satisfied = list(verification_state["satisfied_commands"])
        shared_verification_status = verification_state["status"]
        if current_wave_blocked_packets:
            ready_packets = []
            running_packets = []
        for packet_id in ready_packets:
            packet_statuses[packet_id]["status"] = "ready"
            packet_statuses[packet_id]["reason"] = "ready-in-current-wave"
        break

    if current_wave is None and wave_ids:
        current_wave_ids = list(wave_ids[-1])

    merge_target = _common_field(sorted(packets), packets, "merge_target")
    merge_strategy = _common_field(sorted(packets), packets, "merge_strategy") or "none"
    next_ready_wave = {"wave_index": current_wave, "packet_ids": ready_packets} if ready_packets and current_wave is not None else None

    updated = dict(plan)
    updated.update(
        {
            "status": "blocked" if blocked_packets and not ready_packets and not running_packets else "completed" if current_wave is None else "active",
            "packets": packets,
            "packet_statuses": packet_statuses,
            "current_wave": current_wave,
            "wave_count": len(wave_ids),
            "ready_packets": ready_packets,
            "running_packets": running_packets,
            "completed_packets": completed_packets,
            "blocked_packets": blocked_packets,
            "current_wave_blocked_packets": current_wave_blocked_packets,
            "next_ready_wave": next_ready_wave,
            "merge_target": merge_target,
            "merge_strategy": merge_strategy,
            "next_merge_point": merge_target or (f"wave-{current_wave + 1}" if current_wave is not None else None),
            "shared_verification": shared_verification,
            "shared_verification_pending": shared_verification_pending,
            "shared_verification_satisfied": shared_verification_satisfied,
            "shared_verification_status": shared_verification_status,
            "wave_verification_statuses": wave_verification_statuses,
        }
    )
    return updated


def plan_wave_execution(raw_packets: list[dict], *, project: str) -> dict:
    packets: dict[str, dict] = {}
    for raw_packet in raw_packets:
        packet = _normalize_packet(raw_packet)
        if packet["packet_id"] in packets:
            raise ValueError(f"Duplicate wave packet_id: {packet['packet_id']}.")
        packets[packet["packet_id"]] = packet
    if not packets:
        raise ValueError("Wave execution requires at least one packet.")
    _validate_dependencies(packets)
    waves = [{"wave_index": index, "packet_ids": packet_ids} for index, packet_ids in enumerate(_build_waves(packets))]
    plan = {
        "wave_plan_id": f"wave-{slugify(project)}",
        "project": project,
        "packets": packets,
        "waves": waves,
        "packet_statuses": {},
    }
    return _recompute_wave_state(plan, {}, {})


def advance_wave_execution(
    plan: dict,
    progress_by_packet: dict[str, dict] | None,
    run_reports_by_command: dict[str, dict] | None = None,
) -> dict:
    return _recompute_wave_state(plan, progress_by_packet, run_reports_by_command)

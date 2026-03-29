from __future__ import annotations

from pathlib import Path

from companion_operator_context import collect_operator_context
from companion_invoke import invoke_companion_capability
from companion_matching import match_companions
from companion_registry import find_companion_record, load_companion_registry, resolve_companion_registry_path


def collect_companion_checks(workspace: Path) -> tuple[list[dict], list[dict], dict]:
    registry_path = resolve_companion_registry_path()
    registry = load_companion_registry(registry_path)
    checks = [
        {
            "id": "companion-registry",
            "label": "Companion registry",
            "category": "companion",
            "status": "PASS",
            "detail": str(registry_path),
            "remediation": "",
        }
    ]
    summaries: list[dict] = []
    matches = match_companions(workspace=workspace)
    operator_context = {item["id"]: item for item in collect_operator_context(matches, workspace)}
    for match in matches:
        enrichment = invoke_companion_capability(match, "doctor_checks", workspace)
        if enrichment is not None:
            checks.extend(enrichment.get("checks", []))
        record = find_companion_record(registry, match["package"])
        root = Path(str(match["root"]))
        installed = isinstance(record, dict)
        local_available = root.exists()
        checks.append(
            {
                "id": f"companion-{match['id']}",
                "label": f"Matched companion {match['id']}",
                "category": "companion",
                "status": "PASS" if installed or local_available else "WARN",
                "detail": str(record.get("target")) if installed else (str(root) if local_available else "Matched but not installed or registered."),
                "remediation": "" if installed or local_available else f"Install and register `{match['package']}` for the active host state.",
            }
        )
        summaries.append(
            {
                "id": match["id"],
                "package": match["package"],
                "strength": match["strength"],
                "features": match["features"],
                "reasons": match["reasons"],
                "registered": installed,
                "registered_target": record.get("target") if installed else None,
                "local_root": str(root) if local_available else None,
                "operator_profile": operator_context.get(match["id"], {}).get("profile"),
                "verification_pack": operator_context.get(match["id"], {}).get("verification_pack"),
                "verification_steps": operator_context.get(match["id"], {}).get("verification_steps", []),
            }
        )
    companions = registry.get("companions")
    registered = list(companions.values()) if isinstance(companions, dict) else []
    return checks, summaries, {"path": str(registry_path), "registered_companions": registered}

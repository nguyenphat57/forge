from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT_DIR / "docs" / "architecture" / "host-artifacts-manifest.json"


def _resolve_repo_path(path_text: str, field: str, name: str) -> tuple[Path, str]:
    relative = Path(path_text)
    if relative.is_absolute():
        raise ValueError(f"Generated host artifact {name} has absolute {field} path: {path_text}")
    resolved = (ROOT_DIR / relative).resolve()
    try:
        resolved.relative_to(ROOT_DIR.resolve())
    except ValueError as exc:
        raise ValueError(f"Generated host artifact {name} escapes repo root via {field}: {path_text}") from exc
    return resolved, relative.as_posix()


def _load_manifest_entries() -> list[dict]:
    payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError(f"Generated host artifact manifest must define a non-empty artifacts list: {MANIFEST_PATH}")
    return artifacts


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _bundle_output_relative(spec: dict) -> str:
    output_parts = Path(spec["output"]).parts
    return Path(*output_parts[3:]).as_posix()


def _resolve_record_output_path(spec: dict, output_root: Path | None) -> Path:
    if output_root is None:
        return spec["output_path"]
    return output_root / _bundle_output_relative(spec)


def generated_host_artifact_specs() -> list[dict]:
    specs: list[dict] = []
    seen_names: set[str] = set()
    seen_outputs: set[str] = set()
    for index, item in enumerate(_load_manifest_entries()):
        if not isinstance(item, dict):
            raise ValueError(f"Generated host artifact manifest entry #{index} must be an object")
        name = item.get("name")
        bundle = item.get("bundle")
        source = item.get("source")
        output = item.get("output")
        if not all(isinstance(value, str) and value.strip() for value in (name, bundle, source, output)):
            raise ValueError(f"Generated host artifact manifest entry #{index} is missing name, bundle, source, or output")
        if name in seen_names:
            raise ValueError(f"Duplicate generated host artifact name: {name}")
        source_path, source_rel = _resolve_repo_path(source, "source", name)
        output_path, output_rel = _resolve_repo_path(output, "output", name)
        if not source_path.exists():
            raise FileNotFoundError(f"Missing canonical source for generated host artifact {name}: {source_rel}")
        output_parts = Path(output_rel).parts
        if len(output_parts) < 4 or output_parts[:3] != ("packages", bundle, "overlay"):
            raise ValueError(f"Generated host artifact {name} output must live under packages/{bundle}/overlay: {output_rel}")
        if output_rel in seen_outputs:
            raise ValueError(f"Duplicate generated host artifact output path: {output_rel}")
        seen_names.add(name)
        seen_outputs.add(output_rel)
        specs.append(
            {
                "name": name,
                "bundle": bundle,
                "source": source_rel,
                "output": output_rel,
                "source_path": source_path,
                "output_path": output_path,
            }
        )
    return specs


def generated_host_artifact_records(
    bundle_names: set[str] | None = None,
    *,
    output_root: Path | None = None,
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for spec in generated_host_artifact_specs():
        if bundle_names and spec["bundle"] not in bundle_names:
            continue
        source_text = spec["source_path"].read_text(encoding="utf-8")
        output_path = _resolve_record_output_path(spec, output_root)
        output_text = output_path.read_text(encoding="utf-8") if output_path.exists() else None
        records.append(
            {
                "name": spec["name"],
                "bundle": spec["bundle"],
                "source": spec["source"],
                "output": spec["output"],
                "bundle_output": _bundle_output_relative(spec),
                "output_path": str(output_path),
                "output_exists": output_text is not None,
                "source_sha256": _sha256_text(source_text),
                "output_sha256": _sha256_text(output_text) if output_text is not None else None,
            }
        )
    return records


def generated_host_artifact_records_for_bundle(bundle_name: str, *, output_root: Path | None = None) -> list[dict[str, object]]:
    return generated_host_artifact_records({bundle_name}, output_root=output_root)

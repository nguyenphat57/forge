from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import sys
import textwrap
from argparse import Namespace
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT_DIR / "scripts"
FIXTURES_DIR = ROOT_DIR / "tests" / "fixtures"
WORKSPACES_DIR = FIXTURES_DIR / "workspaces"
FORGE_HOMES_DIR = FIXTURES_DIR / "forge-homes"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import common  # noqa: E402


REFERENCE_COMPANION_PACKAGE = "forge-nextjs-typescript-postgres"
REFERENCE_COMPANION_ID = "nextjs-typescript-postgres"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip("\n"), encoding="utf-8")


def build_route_args(
    prompt: str,
    *,
    repo_signals: list[str] | None = None,
    workspace_router: Path | None = None,
    changed_files: int | None = None,
    has_harness: str = "auto",
) -> Namespace:
    return Namespace(
        prompt=prompt,
        repo_signal=repo_signals or [],
        workspace_router=workspace_router,
        changed_files=changed_files,
        has_harness=has_harness,
        format="json",
        persist=False,
        output_dir=None,
    )


def load_json_fixture(name: str) -> list[dict]:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def workspace_fixture(name: str) -> Path:
    return WORKSPACES_DIR / name


def create_reference_companion_package(root: Path) -> Path:
    package_dir = (root / REFERENCE_COMPANION_PACKAGE).resolve()
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        package_dir / "companion.json",
        {
            "name": REFERENCE_COMPANION_PACKAGE,
            "kind": "companion",
            "distribution": "example",
            "capabilities_path": "data/companion-capabilities.json",
        },
    )
    _write_json(
        package_dir / "data" / "companion-capabilities.json",
        {
            "id": REFERENCE_COMPANION_ID,
            "package": REFERENCE_COMPANION_PACKAGE,
            "version": "0.1.0",
            "compatibility": {"forge_core_min": "1.0.0", "forge_core_max": "1.x"},
            "feature_rules": {
                "nextjs": {
                    "prompt_keywords_any": ["next.js", "nextjs", "next js"],
                    "package_dependencies_any": ["next"],
                    "file_markers_any": ["next.config.ts", "app/layout.tsx", "app/page.tsx"],
                    "repo_signals_any": ["next", "next.config.ts", "app/"],
                },
                "typescript": {
                    "package_dependencies_any": ["typescript"],
                    "package_dev_dependencies_any": ["typescript"],
                    "file_markers_any": ["tsconfig.json"],
                    "repo_signals_any": ["tsconfig.json", ".ts", ".tsx"],
                },
                "postgres": {
                    "package_dependencies_any": ["@prisma/client", "pg", "postgres"],
                    "package_dev_dependencies_any": ["prisma"],
                    "file_markers_any": ["prisma/schema.prisma"],
                    "repo_signals_any": ["postgres", "prisma", "schema.prisma"],
                },
            },
            "activation_any": ["nextjs"],
            "quality_bands": {"strong": ["nextjs", "typescript", "postgres"], "baseline": ["nextjs", "typescript"]},
            "init_presets": [
                {"id": "minimal-saas", "label": "Minimal SaaS", "script": "scripts/scaffold_preset.py"},
                {"id": "billing-saas", "label": "Billing SaaS", "script": "scripts/scaffold_preset.py"},
            ],
            "command_profiles": {"script": "scripts/resolve_commands.py"},
            "verification_packs": {"script": "scripts/resolve_commands.py"},
            "doctor_checks": {"script": "scripts/enrich_doctor.py"},
            "map_enrichers": {"script": "scripts/enrich_map_codebase.py"},
        },
    )
    _write_text(
        package_dir / "scripts" / "companion_common.py",
        """
        from __future__ import annotations

        import json
        from pathlib import Path


        def dependency_sets(workspace: Path) -> tuple[set[str], set[str]]:
            package_json = workspace / "package.json"
            if not package_json.exists():
                return set(), set()
            payload = json.loads(package_json.read_text(encoding="utf-8"))
            dependencies = payload.get("dependencies", {})
            dev_dependencies = payload.get("devDependencies", {})
            return (
                set(dependencies) if isinstance(dependencies, dict) else set(),
                set(dev_dependencies) if isinstance(dev_dependencies, dict) else set(),
            )


        def env_example_text(workspace: Path) -> str:
            env_example = workspace / ".env.example"
            return env_example.read_text(encoding="utf-8") if env_example.exists() else ""
        """,
    )
    _write_text(
        package_dir / "scripts" / "resolve_commands.py",
        """
        from __future__ import annotations

        import argparse
        import json
        from pathlib import Path


        def build_report() -> dict:
            return {
                "profile": "nextjs-prisma-app-router",
                "package_manager": "npm",
                "commands": {
                    "lint": "npm run lint",
                    "typecheck": "npm run typecheck",
                    "test": "npm test",
                    "build": "npm run build",
                },
                "verification_pack": {
                    "id": "nextjs-production-ready",
                    "steps": ["npm run lint", "npm run typecheck", "npm test", "npm run build"],
                },
            }


        def main() -> int:
            parser = argparse.ArgumentParser(description="Resolve command profiles for the reference test companion.")
            parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root")
            parser.add_argument("--format", choices=["text", "json"], default="json")
            parser.parse_args()
            print(json.dumps(build_report(), indent=2, ensure_ascii=False))
            return 0


        if __name__ == "__main__":
            raise SystemExit(main())
        """,
    )
    _write_text(
        package_dir / "scripts" / "enrich_doctor.py",
        """
        from __future__ import annotations

        import argparse
        import json
        from pathlib import Path

        from companion_common import dependency_sets


        def _check(identifier: str, label: str, status: str, detail: str) -> dict:
            return {
                "id": identifier,
                "label": label,
                "category": "companion",
                "status": status,
                "detail": detail,
                "remediation": "",
            }


        def build_report(workspace: Path) -> dict:
            dependencies, dev_dependencies = dependency_sets(workspace)
            postgres_ready = bool({"@prisma/client", "pg", "postgres"} & dependencies or {"prisma"} & dev_dependencies)
            checks = [
                _check(
                    "nextjs-package",
                    "Next.js package",
                    "PASS" if "next" in dependencies else "FAIL",
                    "Detected `next` dependency." if "next" in dependencies else "Missing `next` dependency.",
                ),
                _check(
                    "postgres-adapter",
                    "Postgres adapter",
                    "PASS" if postgres_ready else "WARN",
                    "Detected a Postgres-oriented adapter." if postgres_ready else "No Postgres adapter dependency detected yet.",
                ),
            ]
            return {"status": "PASS", "companion": "nextjs-typescript-postgres", "checks": checks}


        def main() -> int:
            parser = argparse.ArgumentParser(description="Emit doctor checks for the reference test companion.")
            parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root")
            parser.add_argument("--format", choices=["text", "json"], default="json")
            args = parser.parse_args()
            print(json.dumps(build_report(args.workspace.resolve()), indent=2, ensure_ascii=False))
            return 0


        if __name__ == "__main__":
            raise SystemExit(main())
        """,
    )
    _write_text(
        package_dir / "scripts" / "enrich_map_codebase.py",
        """
        from __future__ import annotations

        import argparse
        import json
        from pathlib import Path

        from companion_common import dependency_sets


        def build_report(workspace: Path) -> dict:
            dependencies, dev_dependencies = dependency_sets(workspace)
            has_prisma = bool({"@prisma/client"} & dependencies or {"prisma"} & dev_dependencies or (workspace / "prisma" / "schema.prisma").exists())
            enrichments = {
                "stack": {
                    "companion_family": "nextjs-typescript-postgres",
                    "render_surface": "web",
                    "database_adapters": ["prisma"] if has_prisma else [],
                    "frameworks": ["nextjs-app-router"] if (workspace / "app" / "layout.tsx").exists() else [],
                    "product_features": [],
                },
                "structure": {
                    "entrypoints": [
                        path
                        for path in ("app/layout.tsx", "app/page.tsx", "prisma/schema.prisma")
                        if (workspace / path).exists()
                    ],
                    "integrations": ["prisma"] if has_prisma else [],
                    "risks": [],
                    "open_questions": [],
                    "next_actions": [
                        "Verify lint, typecheck, test, and build before large Next.js changes.",
                        "Confirm schema ownership before editing database access paths.",
                    ],
                    "stack_notes": [],
                },
            }
            return {"status": "PASS", "companion": "nextjs-typescript-postgres", "enrichments": enrichments}


        def main() -> int:
            parser = argparse.ArgumentParser(description="Emit map-codebase enrichments for the reference test companion.")
            parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root")
            parser.add_argument("--format", choices=["text", "json"], default="json")
            args = parser.parse_args()
            print(json.dumps(build_report(args.workspace.resolve()), indent=2, ensure_ascii=False))
            return 0


        if __name__ == "__main__":
            raise SystemExit(main())
        """,
    )
    _write_text(
        package_dir / "scripts" / "scaffold_preset.py",
        """
        from __future__ import annotations

        import argparse
        import json
        from pathlib import Path


        def _package_json(project_name: str, preset: str) -> str:
            dependencies = {"next": "^15.0.0", "@prisma/client": "^6.0.0"}
            dev_dependencies = {"prisma": "^6.0.0", "typescript": "^5.0.0"}
            if preset == "billing-saas":
                dependencies["stripe"] = "^17.0.0"
            return json.dumps(
                {
                    "name": project_name.lower().replace(" ", "-"),
                    "private": True,
                    "dependencies": dependencies,
                    "devDependencies": dev_dependencies,
                },
                indent=2,
                ensure_ascii=False,
            ) + "\\n"


        def _plan_entries(workspace: Path, project_name: str, preset: str) -> list[tuple[Path, str]]:
            files = [
                (workspace / "package.json", _package_json(project_name, preset)),
                (workspace / "app" / "layout.tsx", "export default function RootLayout({ children }) { return children; }\\n"),
                (workspace / "app" / "page.tsx", f"export default function Page() {{ return <main>{project_name}</main>; }}\\n"),
                (workspace / "prisma" / "schema.prisma", "generator client { provider = \\"prisma-client-js\\" }\\n"),
                (workspace / ".env.example", "DATABASE_URL=postgres://localhost/forge\\n"),
            ]
            if preset == "billing-saas":
                files.extend(
                    [
                        (workspace / "app" / "(app)" / "billing" / "page.tsx", "export default function BillingPage() { return <main>Billing</main>; }\\n"),
                        (workspace / "app" / "api" / "webhooks" / "stripe" / "route.ts", "export async function POST() { return Response.json({ ok: true }); }\\n"),
                    ]
                )
            return files


        def build_report(workspace: Path, preset: str, project_name: str, apply: bool) -> dict:
            created_directories: list[str] = []
            created_files: list[str] = []
            reused_paths: list[str] = []
            for path, content in _plan_entries(workspace, project_name, preset):
                if path.exists():
                    reused_paths.append(str(path))
                    continue
                if apply:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(content, encoding="utf-8")
                parent = str(path.parent)
                if parent not in created_directories:
                    created_directories.append(parent)
                created_files.append(str(path))
            return {
                "status": "PASS",
                "preset": preset,
                "project_name": project_name,
                "created_directories": created_directories,
                "created_files": created_files,
                "reused_paths": reused_paths,
            }


        def main() -> int:
            parser = argparse.ArgumentParser(description="Scaffold the reference test companion preset.")
            parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace root")
            parser.add_argument("--preset", required=True)
            parser.add_argument("--project-name", default="Forge App")
            parser.add_argument("--apply", action="store_true")
            parser.add_argument("--format", choices=["text", "json"], default="json")
            args = parser.parse_args()
            report = build_report(args.workspace.resolve(), args.preset, args.project_name, args.apply)
            print(json.dumps(report, indent=2, ensure_ascii=False))
            return 0


        if __name__ == "__main__":
            raise SystemExit(main())
        """,
    )
    return package_dir


def resolve_reference_companion_package() -> Path:
    candidates = [ROOT_DIR.parent / "forge-nextjs-typescript-postgres"]
    if len(ROOT_DIR.parents) >= 2:
        candidates.append(ROOT_DIR.parents[1] / "packages" / "forge-nextjs-typescript-postgres")
    for candidate in candidates:
        if (candidate / "companion.json").exists():
            return candidate.resolve()
    return candidates[0].resolve()


@contextmanager
def reference_companion_environment(*, registered: bool = False):
    with TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        companion_root = create_reference_companion_package(temp_root / "companions")
        env: dict[str, str] = {}
        if registered:
            registry_path = temp_root / "state" / "companions.json"
            _write_json(
                registry_path,
                {
                    "version": 1,
                    "companions": {
                        REFERENCE_COMPANION_PACKAGE: {
                            "id": REFERENCE_COMPANION_ID,
                            "package": REFERENCE_COMPANION_PACKAGE,
                            "target": str(companion_root),
                            "version": "0.1.0",
                        }
                    },
                },
            )
            env["FORGE_COMPANIONS_PATH"] = str(registry_path)
        else:
            env["FORGE_COMPANION_PATHS"] = str(companion_root)
        yield companion_root, env


@contextmanager
def temporary_workspace(name: str = "workspace"):
    with TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir) / name
        workspace.mkdir(parents=True, exist_ok=True)
        yield workspace


@contextmanager
def copied_workspace_fixture(name: str, *, target_name: str = "workspace"):
    with TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir) / target_name
        shutil.copytree(workspace_fixture(name), workspace)
        yield workspace


def forge_home_fixture(name: str) -> Path:
    return FORGE_HOMES_DIR / name


def bundle_package_name() -> str:
    manifest_path = ROOT_DIR / "BUILD-MANIFEST.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        package_name = manifest.get("package")
        if isinstance(package_name, str) and package_name.strip():
            return package_name.strip()
    return ROOT_DIR.name


def is_core_bundle() -> bool:
    return bundle_package_name() == "forge-core"


def load_output_contract_profiles() -> dict | None:
    if not common.OUTPUT_CONTRACTS_PATH.exists():
        return None
    payload = json.loads(common.OUTPUT_CONTRACTS_PATH.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def expected_output_contract(extra: object) -> dict[str, object]:
    if not isinstance(extra, dict):
        return {}

    contract: dict[str, object] = {}
    profiles = load_output_contract_profiles()
    language_profile: dict[str, object] | None = None

    language = extra.get("language")
    if isinstance(language, str) and language.strip():
        normalized_language = common.normalize_choice_token(language)
        contract["language"] = normalized_language
        if isinstance(profiles, dict):
            languages = profiles.get("languages")
            if isinstance(languages, dict):
                profile = languages.get(normalized_language)
                if isinstance(profile, dict):
                    language_profile = profile
                    profile_contract = profile.get("contract")
                    if isinstance(profile_contract, dict):
                        contract.update(copy.deepcopy(profile_contract))

    orthography = extra.get("orthography")
    if isinstance(orthography, str) and orthography.strip():
        normalized_orthography = common.normalize_choice_token(orthography)
        contract["orthography"] = normalized_orthography
        if isinstance(profiles, dict):
            orthographies = profiles.get("orthographies")
            if isinstance(orthographies, dict):
                profile = orthographies.get(normalized_orthography)
                if isinstance(profile, dict):
                    contract.update(copy.deepcopy(profile))

    tone_detail = extra.get("tone_detail")
    if isinstance(tone_detail, str) and tone_detail.strip():
        contract["tone_detail"] = tone_detail.strip()

    custom_rules = extra.get("custom_rules")
    if isinstance(custom_rules, list):
        normalized_rules = [item.strip() for item in custom_rules if isinstance(item, str) and item.strip()]
        if normalized_rules:
            contract["custom_rules"] = normalized_rules

    if "orthography" not in contract and isinstance(language_profile, dict):
        default_orthography = language_profile.get("default_orthography")
        if isinstance(default_orthography, str) and default_orthography.strip():
            normalized_orthography = common.normalize_choice_token(default_orthography)
            contract["orthography"] = normalized_orthography
            if isinstance(profiles, dict):
                orthographies = profiles.get("orthographies")
                if isinstance(orthographies, dict):
                    profile = orthographies.get(normalized_orthography)
                    if isinstance(profile, dict):
                        contract.update(copy.deepcopy(profile))

    return contract


def run_python_script(
    script_name: str,
    *args: str,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(SCRIPTS_DIR / script_name), *args]
    merged_env = os.environ.copy()
    merged_env.setdefault("FORGE_HOME", str(forge_home_fixture("empty")))
    if env:
        merged_env.update(env)
    return subprocess.run(
        command,
        cwd=str(cwd or ROOT_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        env=merged_env,
    )

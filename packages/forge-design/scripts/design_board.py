from __future__ import annotations

import html
import json
import shutil
from pathlib import Path


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}


def slugify(value: str) -> str:
    cleaned = "".join(char.lower() if char.isalnum() else "-" for char in value.strip())
    compact = "-".join(part for part in cleaned.split("-") if part)
    return compact or "board"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def load_brief_bundle(brief_dir: Path, *, screen: str | None = None) -> dict[str, object]:
    brief_dir = brief_dir.expanduser().resolve()
    master_md = brief_dir / "MASTER.md"
    if not master_md.exists():
        raise FileNotFoundError(f"Missing MASTER.md in brief directory: {brief_dir}")

    master_json = brief_dir / "MASTER.json"
    metadata: dict[str, object] = {}
    if master_json.exists():
        payload = json.loads(master_json.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            metadata = payload

    override_path = None
    override_text = None
    if screen:
        candidate = brief_dir / "pages" / f"{slugify(screen)}.md"
        if candidate.exists():
            override_path = candidate
            override_text = _read_text(candidate)

    project_name = str(metadata.get("project_name") or brief_dir.parent.name)
    mode = str(metadata.get("mode") or brief_dir.name)
    return {
        "brief_dir": str(brief_dir),
        "project_name": project_name,
        "mode": mode,
        "stack": str(metadata.get("stack") or "unknown"),
        "platform": str(metadata.get("platform") or "unknown"),
        "screen": screen or metadata.get("screen") or "shared",
        "master_path": str(master_md),
        "master_text": _read_text(master_md),
        "override_path": str(override_path) if override_path else None,
        "override_text": override_text,
    }


def discover_evidence_files(*, evidence: list[str], evidence_dir: str | None = None) -> list[Path]:
    discovered: list[Path] = []
    seen: set[Path] = set()
    for raw_path in evidence:
        path = Path(raw_path).expanduser().resolve()
        if path.exists() and path.suffix.lower() in IMAGE_SUFFIXES and path not in seen:
            discovered.append(path)
            seen.add(path)
    if evidence_dir:
        root = Path(evidence_dir).expanduser().resolve()
        if root.exists():
            for path in sorted(root.rglob("*")):
                if not path.is_file() or path.suffix.lower() not in IMAGE_SUFFIXES or path in seen:
                    continue
                discovered.append(path)
                seen.add(path)
    return discovered


def _copy_assets(evidence_files: list[Path], assets_dir: Path) -> list[dict[str, str]]:
    assets_dir.mkdir(parents=True, exist_ok=True)
    copied: list[dict[str, str]] = []
    for index, source in enumerate(evidence_files, start=1):
        target_name = f"{index:02d}-{slugify(source.stem)}{source.suffix.lower()}"
        target = assets_dir / target_name
        shutil.copy2(source, target)
        copied.append(
            {
                "label": source.name,
                "source_path": str(source),
                "copied_path": str(target.resolve()),
                "relative_path": target_name,
            }
        )
    return copied


def render_board_html(bundle: dict[str, object], copied_assets: list[dict[str, str]], *, title: str | None = None) -> str:
    title_text = title or f"{bundle['project_name']} Design Board"
    badges = [
        f"Project: {bundle['project_name']}",
        f"Mode: {bundle['mode']}",
        f"Screen: {bundle['screen']}",
        f"Stack: {bundle['stack']}",
        f"Platform: {bundle['platform']}",
    ]
    asset_cards = "\n".join(
        (
            "<figure class='asset-card'>"
            f"<img src='{html.escape(asset['relative_path'])}' alt='{html.escape(asset['label'])}' />"
            f"<figcaption>{html.escape(asset['label'])}</figcaption>"
            "</figure>"
        )
        for asset in copied_assets
    ) or "<p class='empty'>No evidence assets were provided.</p>"
    override_block = ""
    if bundle.get("override_text"):
        override_block = (
            "<section class='panel'>"
            "<h2>Screen Override</h2>"
            f"<p class='meta'>{html.escape(str(bundle['override_path']))}</p>"
            f"<pre>{html.escape(str(bundle['override_text']))}</pre>"
            "</section>"
        )
    badge_html = "".join(f"<li>{html.escape(item)}</li>" for item in badges)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(title_text)}</title>
  <style>
    :root {{ color-scheme: light; --ink: #10212a; --muted: #61727d; --paper: #f7f3ea; --card: #fffdf8; --line: #d8d0c0; --accent: #ba5b3a; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: "Iowan Old Style", Georgia, serif; background: linear-gradient(180deg, #f2ead9 0%, var(--paper) 100%); color: var(--ink); }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 40px 24px 56px; }}
    h1, h2 {{ margin: 0 0 12px; line-height: 1.05; }}
    p, li, figcaption, pre {{ font-size: 15px; line-height: 1.6; }}
    .hero {{ display: grid; gap: 18px; margin-bottom: 28px; }}
    .hero h1 {{ font-size: clamp(40px, 6vw, 76px); letter-spacing: -0.03em; }}
    .meta-list {{ list-style: none; display: flex; flex-wrap: wrap; gap: 10px; padding: 0; margin: 0; }}
    .meta-list li {{ border: 1px solid var(--line); background: rgba(255,255,255,0.72); padding: 8px 12px; border-radius: 999px; color: var(--muted); }}
    .grid {{ display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 20px; }}
    .panel {{ border: 1px solid var(--line); border-radius: 24px; background: var(--card); padding: 22px; box-shadow: 0 18px 48px rgba(16, 33, 42, 0.06); }}
    .panel pre {{ margin: 0; white-space: pre-wrap; word-break: break-word; }}
    .meta {{ margin: 0 0 14px; color: var(--muted); }}
    .asset-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; }}
    .asset-card {{ margin: 0; border: 1px solid var(--line); border-radius: 18px; overflow: hidden; background: #fff; }}
    .asset-card img {{ display: block; width: 100%; height: 220px; object-fit: cover; background: #efe6d6; }}
    .asset-card figcaption {{ padding: 12px 14px 14px; color: var(--muted); }}
    .empty {{ color: var(--muted); }}
    @media (max-width: 900px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <h1>{html.escape(title_text)}</h1>
      <ul class="meta-list">{badge_html}</ul>
    </section>
    <section class="grid">
      <section class="panel">
        <h2>Master Brief</h2>
        <p class="meta">{html.escape(str(bundle['master_path']))}</p>
        <pre>{html.escape(str(bundle['master_text']))}</pre>
      </section>
      {override_block or "<section class='panel'><h2>Screen Override</h2><p class='empty'>No screen override selected.</p></section>"}
    </section>
    <section class="panel" style="margin-top: 20px;">
      <h2>Evidence Gallery</h2>
      <div class="asset-grid">{asset_cards}</div>
    </section>
  </main>
</body>
</html>
"""


def build_design_board(
    *,
    brief_dir: str,
    screen: str | None = None,
    evidence: list[str] | None = None,
    evidence_dir: str | None = None,
    output: str | None = None,
    title: str | None = None,
) -> dict[str, object]:
    evidence = evidence or []
    bundle = load_brief_bundle(Path(brief_dir), screen=screen)
    output_path = Path(output).expanduser().resolve() if output else Path(bundle["brief_dir"]) / f"{slugify(str(bundle['screen']))}-design-board.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    assets_dir = output_path.parent / f"{output_path.stem}-assets"
    evidence_files = discover_evidence_files(evidence=evidence, evidence_dir=evidence_dir)
    copied_assets = _copy_assets(evidence_files, assets_dir) if evidence_files else []
    html_text = render_board_html(bundle, copied_assets, title=title)
    output_path.write_text(html_text, encoding="utf-8")
    return {
        "status": "PASS",
        "brief_dir": bundle["brief_dir"],
        "screen": bundle["screen"],
        "output_path": str(output_path.resolve()),
        "assets_dir": str(assets_dir.resolve()),
        "asset_count": len(copied_assets),
        "assets": copied_assets,
    }

from __future__ import annotations

import html
import json
import re
from pathlib import Path


MODE_DIRS = ("frontend", "visualize")
REVIEW_PROMPTS = [
    "Which state is easiest to miss during implementation?",
    "Where does the hierarchy collapse first on smaller viewports?",
    "Which part still depends on guessing instead of explicit design intent?",
    "What should become a token or reusable pattern before coding starts?",
]


def slugify(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return text or "screen"


def resolve_master_json(source: Path) -> Path:
    source = source.expanduser().resolve()
    if source.is_file():
        if source.suffix.lower() != ".json":
            raise ValueError(f"forge-design expects MASTER.json or a persisted brief directory, got: {source}")
        return source
    if not source.is_dir():
        raise FileNotFoundError(f"Brief source does not exist: {source}")
    direct = source / "MASTER.json"
    if direct.exists():
        return direct
    candidates = [source / mode / "MASTER.json" for mode in MODE_DIRS if (source / mode / "MASTER.json").exists()]
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        raise ValueError(f"Ambiguous brief source {source}; point forge-design to a specific mode directory or MASTER.json.")
    raise FileNotFoundError(f"MASTER.json not found under persisted brief source: {source}")


def load_brief(source: Path) -> tuple[dict, Path]:
    master_json = resolve_master_json(source)
    payload = json.loads(master_json.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"MASTER.json must contain an object: {master_json}")
    return payload, master_json


def load_page_override(master_json: Path, screen: str | None) -> tuple[Path | None, str | None]:
    if screen is None:
        return None, None
    path = master_json.parent / "pages" / f"{slugify(screen)}.md"
    if not path.exists():
        return path, None
    return path, path.read_text(encoding="utf-8")


def _render_list(items: list[str]) -> str:
    return "".join(f"<li>{html.escape(item)}</li>" for item in items)


def _render_override(content: str | None) -> str:
    if not content:
        return "<p class='muted'>No page override was found for this screen.</p>"
    lines = content.strip().splitlines()
    rendered: list[str] = []
    for line in lines:
        if line.startswith("#"):
            rendered.append(f"<h3>{html.escape(line.lstrip('# ').strip())}</h3>")
        elif line.startswith("- "):
            if not rendered or not rendered[-1].startswith("<ul>"):
                rendered.append("<ul>")
            rendered.append(f"<li>{html.escape(line[2:].strip())}</li>")
        elif line.strip():
            if rendered and rendered[-1] == "</ul>":
                pass
            rendered.append(f"<p>{html.escape(line.strip())}</p>")
    html_parts: list[str] = []
    open_list = False
    for part in rendered:
        if part == "<ul>":
            if not open_list:
                html_parts.append(part)
                open_list = True
            continue
        if not part.startswith("<li>") and open_list:
            html_parts.append("</ul>")
            open_list = False
        html_parts.append(part)
    if open_list:
        html_parts.append("</ul>")
    return "".join(html_parts)


def render_packet_html(brief: dict, *, page_override: str | None) -> str:
    project = html.escape(str(brief.get("project_name") or "workspace"))
    mode = html.escape(str(brief.get("mode") or "visualize"))
    screen = html.escape(str(brief.get("screen") or "shared"))
    title = html.escape(str(brief.get("title") or "Design Packet"))
    summary = html.escape(str(brief.get("summary") or ""))
    objective = html.escape(str(brief.get("objective") or ""))
    stack = html.escape(str(brief.get("stack") or "generic-web"))
    platform = html.escape(str(brief.get("platform") or "web"))
    sections = [str(item) for item in brief.get("sections") or []]
    focus = [str(item) for item in brief.get("stack_focus") or []]
    platform_notes = [str(item) for item in brief.get("platform_notes") or []]
    anti_patterns = [str(item) for item in brief.get("anti_patterns") or []]
    deliverables = [str(item) for item in brief.get("deliverables") or []]
    notes = [str(item) for item in brief.get("notes") or []]
    watchouts = [str(item) for item in brief.get("stack_watchouts") or []]
    prompts = REVIEW_PROMPTS
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} | {project}</title>
  <style>
    :root {{ --ink:#13222f; --sand:#f3ede2; --paper:#fffdf7; --accent:#c75c2a; --accent-soft:#f5d7c8; --teal:#285b63; --line:#d8cfc1; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:Georgia, 'Times New Roman', serif; color:var(--ink); background:linear-gradient(180deg, #efe6d9 0%, #f9f5ee 38%, #ffffff 100%); }}
    main {{ max-width:1180px; margin:0 auto; padding:40px 24px 64px; }}
    .hero {{ background:radial-gradient(circle at top left, var(--accent-soft), transparent 48%), var(--paper); border:1px solid var(--line); border-radius:28px; padding:28px; box-shadow:0 18px 48px rgba(19,34,47,.08); }}
    .eyebrow {{ text-transform:uppercase; letter-spacing:.12em; font-size:.76rem; color:var(--teal); margin:0 0 12px; }}
    h1 {{ margin:0 0 10px; font-size:clamp(2rem, 4vw, 3.4rem); line-height:1.05; }}
    .hero-grid, .cards {{ display:grid; gap:18px; }}
    .hero-grid {{ grid-template-columns:2fr 1fr; margin-top:24px; }}
    .cards {{ grid-template-columns:repeat(auto-fit, minmax(240px, 1fr)); margin-top:24px; }}
    .card {{ background:rgba(255,255,255,.82); border:1px solid var(--line); border-radius:22px; padding:20px; backdrop-filter: blur(6px); }}
    h2 {{ margin:0 0 12px; font-size:1.1rem; text-transform:uppercase; letter-spacing:.08em; color:var(--teal); }}
    h3 {{ margin:14px 0 8px; font-size:1rem; }}
    p {{ margin:0 0 10px; line-height:1.6; }}
    ul {{ margin:0; padding-left:18px; line-height:1.6; }}
    .meta {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(140px, 1fr)); gap:12px; }}
    .meta strong {{ display:block; font-size:.72rem; text-transform:uppercase; letter-spacing:.09em; color:var(--accent); margin-bottom:4px; }}
    .override {{ margin-top:24px; background:var(--ink); color:#f6efe2; border-radius:24px; padding:24px; }}
    .override h2 {{ color:#f6d7bf; }}
    .muted {{ color:#6f7a83; }}
    @media (max-width: 820px) {{ .hero-grid {{ grid-template-columns:1fr; }} main {{ padding:24px 16px 48px; }} }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <p class="eyebrow">{mode} design packet</p>
      <h1>{title}</h1>
      <p>{summary}</p>
      <div class="hero-grid">
        <div class="card">
          <h2>Objective</h2>
          <p>{objective}</p>
        </div>
        <div class="card meta">
          <div><strong>Project</strong>{project}</div>
          <div><strong>Screen</strong>{screen}</div>
          <div><strong>Stack</strong>{stack}</div>
          <div><strong>Platform</strong>{platform}</div>
        </div>
      </div>
      <div class="cards">
        <article class="card"><h2>Required Sections</h2><ul>{_render_list(sections)}</ul></article>
        <article class="card"><h2>Stack Focus</h2><ul>{_render_list(focus)}</ul></article>
        <article class="card"><h2>Platform Notes</h2><ul>{_render_list(platform_notes)}</ul></article>
        <article class="card"><h2>Anti-Patterns</h2><ul>{_render_list(anti_patterns)}</ul></article>
        <article class="card"><h2>Stack Watchouts</h2><ul>{_render_list(watchouts)}</ul></article>
        <article class="card"><h2>Expected Deliverables</h2><ul>{_render_list(deliverables)}</ul></article>
        <article class="card"><h2>Notes</h2><ul>{_render_list(notes or ['(none)'])}</ul></article>
        <article class="card"><h2>Review Prompts</h2><ul>{_render_list(prompts)}</ul></article>
      </div>
    </section>
    <section class="override">
      <h2>Page Override</h2>
      {_render_override(page_override)}
    </section>
  </main>
</body>
</html>
"""


def write_packet(output_path: Path, html_text: str) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_text, encoding="utf-8")
    return output_path

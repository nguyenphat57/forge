from __future__ import annotations


def build_focus_content(report: dict, focus: str) -> str:
    stack = report["stack"]
    structure = report["structure"]
    lines = [
        f"# Focus: {focus}",
        "",
        f"- Project: {report['project_name']}",
        f"- Languages: {', '.join(stack['languages']) or '(none)'}",
        f"- Frameworks: {', '.join(stack['frameworks']) or '(none)'}",
        f"- Entrypoints: {', '.join(structure['entrypoints']) or '(none)'}",
        f"- Integrations: {', '.join(structure['integrations']) or '(none)'}",
        "- Risks:",
    ]
    risks = structure["risks"] or ["No focus-specific risks detected from root markers."]
    for item in risks:
        lines.append(f"  - {item}")
    lines.append("- Open questions:")
    questions = structure["open_questions"] or ["No focus-specific open questions detected."]
    for item in questions:
        lines.append(f"  - {item}")
    return "\n".join(lines)

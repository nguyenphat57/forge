# Forge Design

`forge-design` is an optional stack-agnostic runtime tool that turns persisted Forge UI briefs into HTML design review packets.

## Goal

Make `frontend` and `visualize` artifacts easier to review, preview, and capture without pushing design rendering logic into `forge-core`.

This tool should stay useful whether the repo is on the core-only path or using an optional companion.
It is for design artifacts, not runtime QA.

## Canonical Surface

- `forge_design.py` is the canonical CLI.
- Input is a persisted Forge UI brief directory or `MASTER.json`.
- Output is an HTML packet stored explicitly or under the bundle state root.
- `render-brief` is the primary brief-to-packet path.
- `board` is an optional evidence-gallery path for mockups and screenshots.
- When `forge-browse` is installed, the packet or board can be captured into deterministic review evidence.

## Boundary

- `forge-design` renders persisted design artifacts into reviewable packets.
- `forge-browse` executes browser QA and capture flows against running experiences.
- `forge-core` still owns routing, verification policy, and release-state decisions.

## MVP

- load persisted UI brief artifacts from `generate_ui_brief.py --persist`
- include screen override notes when `--screen` is provided
- render one standalone HTML packet with deliberate visual hierarchy
- optionally build an evidence-oriented design board from the same persisted brief
- record render events under the runtime-tool state root
- produce artifacts that can be previewed or captured by `forge-browse`
- support an env-gated live smoke that renders a packet and captures it through `forge-browse`

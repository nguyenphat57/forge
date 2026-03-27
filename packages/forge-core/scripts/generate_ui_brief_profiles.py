from __future__ import annotations

import argparse
from pathlib import Path


STACK_PROFILES = {
    "generic-web": {
        "focus": [
            "Preserve the existing design system and tokens before inventing new visual language.",
            "Define layout, states, and responsive behavior before coding.",
            "Prefer semantic structure and clear interaction cues.",
        ],
        "watchouts": [
            "Do not hide critical content behind sticky or fixed elements.",
            "Do not rely on color alone for status or affordance.",
        ],
    },
    "html-tailwind": {
        "focus": [
            "Keep class composition readable; extract repeated patterns instead of building class soup.",
            "Use design tokens or CSS variables behind Tailwind theme values where possible.",
            "Stabilize hover and focus states without layout shift.",
        ],
        "watchouts": [
            "Avoid arbitrary values everywhere when a token should exist.",
            "Avoid `transition-all` and overly transparent light-mode surfaces.",
        ],
    },
    "react-vite": {
        "focus": [
            "Keep component boundaries aligned with screen regions and state ownership.",
            "Model loading, empty, and error states explicitly in the UI brief.",
            "Prefer responsive layouts that degrade cleanly from tablet/desktop to mobile.",
        ],
        "watchouts": [
            "Do not hide expensive rerenders behind animation polish.",
            "Do not couple layout decisions to transient component state without reason.",
        ],
    },
    "nextjs": {
        "focus": [
            "Define server/client boundaries before detailing component behavior.",
            "Account for loading and streaming placeholders in the visual plan.",
            "Treat image, typography, and route transitions as part of the UX contract.",
        ],
        "watchouts": [
            "Do not design interactions that depend on client-only state without fallback.",
            "Do not let hydration edge cases dictate visual complexity.",
        ],
    },
    "mobile-webview": {
        "focus": [
            "Design for touch first: large targets, stable reach zones, safe-area awareness.",
            "Plan keyboard, viewport resize, and background/resume behavior up front.",
            "Prefer simple motion and resilient layouts under constrained device performance.",
        ],
        "watchouts": [
            "Do not put key actions at edges that collide with gestures or safe areas.",
            "Do not assume desktop hover or precise pointer interaction exists.",
        ],
    },
}


PLATFORM_PROFILES = {
    "web": [
        "Primary breakpoints: 375px, 768px, 1024px, 1440px.",
        "Keyboard and focus behavior must stay usable.",
    ],
    "mobile": [
        "Touch targets should stay >= 44px.",
        "Account for safe areas, on-screen keyboard, and reduced motion.",
    ],
    "tablet": [
        "Optimize split layouts and thumb reach for landscape usage.",
        "Preserve information density without shrinking targets below touch comfort.",
    ],
    "cross-platform": [
        "Document what remains shared and what diverges by platform.",
        "Check navigation, spacing, and gesture assumptions separately by form factor.",
    ],
}


MODE_PROFILES = {
    "frontend": {
        "title": "Frontend Brief",
        "objective": "Translate UI requirements into an implementation-safe frontend plan before code.",
        "sections": [
            "Visual direction and design-system constraints",
            "Screens/components in scope",
            "State model: default, loading, empty, error, success",
            "Responsive behavior and layout rules",
            "Accessibility requirements",
            "Stack-specific implementation notes",
        ],
        "deliverables": [
            "Updated screen/component implementation",
            "Verification notes for responsive and accessibility checks",
        ],
        "anti_patterns": [
            "Introducing a new visual language without checking the existing design system",
            "Using emoji as UI icons",
            "Hover effects that shift layout or hide weak affordance",
            "Missing loading, empty, or error states",
            "Invisible borders or unreadable text in light mode",
        ],
    },
    "visualize": {
        "title": "Visual Brief",
        "objective": "Clarify interaction model and visual direction before any UI code or mockup handoff.",
        "sections": [
            "Product/screen goal and user task",
            "Visual direction, tone, and references",
            "Screen map and interaction flow",
            "Component/state matrix",
            "Responsive and platform considerations",
            "Accessibility and motion boundaries",
        ],
        "deliverables": [
            "Text wireframe or mockup guidance",
            "Design spec or handoff notes for implementation",
        ],
        "anti_patterns": [
            "Jumping into components before the interaction model is clear",
            "Designing only the happy path and ignoring system states",
            "Assuming desktop-only interaction for touch-heavy surfaces",
            "Using motion without considering reduced-motion and readability",
        ],
    },
}


def build_brief(args: argparse.Namespace) -> dict:
    profile = MODE_PROFILES[args.mode]
    stack_profile = STACK_PROFILES[args.stack]
    platform_notes = PLATFORM_PROFILES[args.platform]
    project_name = args.project_name or Path.cwd().name

    return {
        "mode": args.mode,
        "title": profile["title"],
        "project_name": project_name,
        "screen": args.screen,
        "summary": args.summary,
        "stack": args.stack,
        "platform": args.platform,
        "objective": profile["objective"],
        "sections": profile["sections"],
        "deliverables": profile["deliverables"],
        "stack_focus": stack_profile["focus"],
        "stack_watchouts": stack_profile["watchouts"],
        "platform_notes": platform_notes,
        "anti_patterns": profile["anti_patterns"],
        "notes": args.note,
    }

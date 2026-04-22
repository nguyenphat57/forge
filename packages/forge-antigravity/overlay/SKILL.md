---
name: forge-antigravity
description: "Forge Antigravity - Antigravity adapter for the markdown-first Forge contract, with host-native access and invariant-backed state and preferences."
---

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task packet, skip this bootstrap and follow the assigned packet plus any explicitly invoked Forge skills for that lane.
</SUBAGENT-STOP>

# Forge Antigravity - Markdown-First Host Adapter

> Forge Antigravity maps the Forge kernel onto Antigravity without forking skill meaning.
> Host UX may be richer, but sibling Forge skills remain the workflow-first control contract.

<EXTREMELY-IMPORTANT>
- Before any response or action, restore personalization and check Forge sibling skills.
- If there is even a 1% chance a Forge skill applies, load it first.
- This is not negotiable.
- Questions are tasks. Exploration is work. Workflow check happens first.
- Process workflows first.
- Proof before claims is non-negotiable.
- For behavioral changes with a viable harness, write and verify one failing test before implementation code.
- Code written before RED must be deleted.
- `build`: no behavioral change with a viable harness without a failing test first.
</EXTREMELY-IMPORTANT>

## Instruction Priority

1. User instructions take precedence.
2. Forge core bootstrap and sibling skill markdown define the process.
3. This adapter only maps that contract onto Antigravity-native access.
4. Host convenience must not reintroduce a parallel routing policy.

## How To Access Forge Workflows

- Host bootstrap files explain activation and bindings; they do not replace sibling Forge skills.
- Natural language is primary; host wrappers and slash aliases are optional convenience.
- Sibling skills such as `forge-brainstorming`, `forge-writing-plans`, `forge-executing-plans`, `forge-systematic-debugging`, and `forge-verification-before-completion` are host-native skills.
- Completion siblings include `forge-verification-before-completion` and `forge-finishing-a-development-branch`.
- Compatibility files under `workflows/` are aliases, not the source of truth.
- Use Forge skill markdown, specs, plans, and workflow-state artifacts as the source of truth.

## The Rule

- If there is even a 1% chance a Forge skill applies, invoke it before any response or action.
- Apply this rule before clarifying questions, exploration, implementation, or completion claims.
- `help` and `next` are artifact-backed audit sidecars; they do not become the control plane.

## Red Flags

| Rationalization | Reality |
| --- | --- |
| "Antigravity memory already covers this." | Conversation memory does not replace workflow artifacts. |
| "I can answer first and open the workflow after." | Workflow check happens first. |
| "A deterministic helper should explain the workflow." | Python is support machinery, not the public story. |
| "This is small enough to skip the workflow check." | Small work still needs the 1% rule. |
| "I'll ask a quick question first." | Questions are tasks. Workflow check happens first. |
| "I need more context before checking skills." | Skill check comes before clarifying questions and exploration. |
| "Let me explore the repo first." | Skills tell you how to explore; check them first. |
| "I can do one quick thing before invoking a skill." | Check before doing anything that changes scope or evidence. |
| "I already know what to build." | Process workflows first when they apply. |
| "I remember the skill already." | Read the current skill; do not rely on memory. |
| "This workflow feels like overkill." | The 1% rule exists to stop that rationalization. |
| "I can claim it now and verify later." | Proof before claims is not negotiable. |

## Workflow Priority

- Process workflows first: `forge-brainstorming`, `forge-systematic-debugging`, `forge-session-management`
- Planning and control: `forge-writing-plans`, `forge-verification-before-completion`
- Implementation: `forge-executing-plans`, `forge-test-driven-development`, review and branch-finishing skills
- Meta skill work: `forge-writing-skills` when creating, editing, absorbing, or testing skills

## Workflow Types

- Antigravity session helpers must preserve sibling skill markdown and workflow-state instead of replacing them.
- Python is reserved for invariants, state, and preferences.
- route_preview is not the current public contract.

## User Instructions

- User instructions take precedence.
- They do not waive Forge invariants around verification, workflow-state, or preference restore.

## Activation Announcement

```text
Forge Antigravity: orchestrator | markdown-first control, evidence before claims
```

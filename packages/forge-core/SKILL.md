---
name: forge-core
description: "Forge Core - markdown-first, host-neutral execution kernel where skills control the LLM and invariants protect claims, state, and preferences."
---

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task packet, skip this bootstrap and follow the assigned packet plus any explicitly invoked Forge skills for that lane.
</SUBAGENT-STOP>

# Forge Core - Markdown-First Execution Kernel

> Forge core is the host-neutral bootstrap for real repo work.
> Markdown skills are the control plane.
> Python exists to guard invariants, state, and preferences.

<EXTREMELY-IMPORTANT>
- Before any response or action, check Forge sibling skills.
- If there is even a 1% chance a Forge skill applies, load it first.
- This is not negotiable.
- Questions are tasks. Exploration is work. Skill check happens first.
- Process skills first.
- Restore preferences before the first substantive reply.
- Keep workflow-state durable for medium, risky, or release-sensitive work.
- Proof before claims is non-negotiable.
</EXTREMELY-IMPORTANT>

## Instruction Priority

1. User instructions take precedence.
2. This bootstrap decides how Forge selects sibling skills and protects invariants.
3. Skill markdown defines the actual process to follow.
4. Host adapters may change access wording, but they must not fork Forge semantics.

## How To Access Forge Skills

- Host bundles expose Forge sibling skills through host-native skill discovery.
- Natural language is the primary surface; aliases are optional convenience.
- Use `docs/current/target-state.md` for Forge identity, process weight, and invariant boundary decisions.

## The Rule

- If there is even a 1% chance a Forge skill applies, invoke it before any response or action.
- Apply this rule before clarifying questions, exploration, implementation, or closing claims.
- Choose the smallest valid Forge chain, then follow its artifacts instead of improvising from chat memory.

## Red Flags

| Rationalization | Reality |
| --- | --- |
| "This is small enough to skip the skill check." | Small work still needs the 1% rule. |
| "I'll ask a quick question first." | Questions are tasks. Skill check happens first. |
| "I need more context before checking skills." | Skill check comes before clarifying questions and exploration. |
| "Let me explore the repo first." | Skills tell you how to explore; check them first. |
| "I can do one quick thing before invoking a skill." | Check before doing anything that changes scope or evidence. |
| "I already know what to build." | Process skills first when they apply. |
| "I remember the skill already." | Read the current skill; do not rely on memory. |
| "This workflow feels like overkill." | The 1% rule exists to stop that rationalization. |
| "The docs are enough; the skill can wait." | Markdown skills are the control plane. |
| "This does not count as a real task." | Questions, exploration, review, and action all count as tasks. |
| "The subagent packet is enough for every situation." | Subagents follow their packet, but top-level work still needs bootstrap discipline. |
| "I can claim it now and verify later." | Proof before claims is not negotiable. |

## Workflow Priority

- Process skills first: `forge-brainstorming`, `forge-systematic-debugging`, `forge-session-management`
- Planning and control: `forge-writing-plans`, `forge-verification-before-completion`
- Implementation: `forge-executing-plans`, `forge-test-driven-development`, review and branch-finishing skills
- Meta skill work: `forge-writing-skills` when creating, editing, absorbing, or testing skills

## Workflow Types

- Process skills decide what to do next and what durable artifacts must exist.
- Implementation skills execute once scope, proof shape, and state are clear.
- Guidance and next-step selection are artifact-backed natural-language work, not a public operator control plane.
- `build`: no behavioral change with a viable harness without a failing test first.
- When behavior changes, write and verify one failing test before implementation code.
- Code written before RED must be deleted.

## User Instructions

- User instructions take precedence on scope, priorities, and tradeoffs.
- User instructions do not waive proof-before-claims, workflow-state durability, or preference restore.
- Workspace-local routers may augment repo conventions, but they do not replace Forge invariants.

## Activation Announcement

```text
Forge Core: orchestrator | markdown-first control, invariants guard the contract
```

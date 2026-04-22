---
name: review
type: compatibility-wrapper
canonical_skill: forge-requesting-code-review
---

# Review Compatibility Wrapper

Use host-native skill discovery to invoke the correct review skill.

Use `forge-requesting-code-review` when asking for or performing a review.

Use `forge-receiving-code-review` when handling user, reviewer, CI, or agent feedback.

Use `forge-finishing-a-development-branch` when review and verification are complete enough to decide merge, PR, keep, or discard.

Before any ready or merge claim, invoke `forge-verification-before-completion`.

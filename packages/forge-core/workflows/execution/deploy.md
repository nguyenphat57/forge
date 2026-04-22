---
name: deploy
type: compatibility-wrapper
canonical_skill: forge-verification-before-completion
---

# Deploy Compatibility Wrapper

Use host-native skill discovery to invoke `forge-verification-before-completion` before any deploy claim.

Deployment remains release-facing execution, but the canonical claim boundary is the verification skill.

Confirm target identity, config/secrets, build/test evidence, review/security disposition, rollback path, and post-deploy smoke readiness.

If branch integration is still undecided, use `forge-finishing-a-development-branch` before deploy.

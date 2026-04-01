# GitHub Public Switch Checklist

Date: 2026-03-30
Scope: Final operator checklist before changing the Forge repository from private to public on GitHub.

## Goal

Use this checklist immediately before flipping repository visibility so the public switch does not expose stale private-only data or leave the public repo without basic security and release settings.

## Pre-Switch Audit

- Confirm the public release snapshot is already pushed and tagged.
- Confirm the intended public tag is `v1.10.1`.
- Confirm the release body to publish is `docs/release/1.10.1-github-release-body.md`.
- Review repository secrets and variables under GitHub `Settings -> Secrets and variables`.
- Remove or rotate any secret that should not remain available after the repo becomes public.
- Review Actions workflow permissions under GitHub `Settings -> Actions -> General`.
- Confirm fork pull requests cannot access sensitive write-scoped credentials.
- Review saved Actions artifacts and logs for accidental secret disclosure or internal-only data.
- Review existing issues, pull requests, discussions, wiki pages, and project boards for private-only content.
- Review existing releases and draft releases for private-only notes or attachments.
- Review tags and commit history for anything that should not become public.
- Confirm the default branch is the branch the operator wants to present publicly.

## Security Settings

- Enable `Private vulnerability reporting` if available for the repository plan.
- Enable `Security advisories` if available.
- Confirm `SECURITY.md` is visible in the default branch.
- Confirm the public contact path in `SECURITY.md` is acceptable for inbound reports.
- Confirm branch protection on `main` matches the public collaboration policy the operator wants.

## Release Surface

- Create a GitHub Release from tag `v1.10.1`.
- Paste the contents of `docs/release/1.10.1-github-release-body.md`.
- Optionally attach bundled artifacts from `dist/` if the operator wants binary or bundle distribution through GitHub Releases.
- Confirm `README.md` is the landing page the operator wants public users to see first.
- Confirm `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and `SECURITY.md` all render correctly on GitHub.

## Visibility Switch

- Open GitHub `Settings -> General -> Danger Zone`.
- Change repository visibility from `Private` to `Public`.
- Re-read the GitHub warning carefully before confirming.
- Complete the visibility confirmation flow.

## Immediate Post-Switch Checks

- Open the public repo in a signed-out browser session.
- Confirm the repo home page, README, and release entry render correctly.
- Open the `Security` tab and confirm the expected reporting options are visible.
- Open the latest release and confirm the release notes, tag, and any uploaded artifacts are correct.
- Trigger or wait for the verify workflow and confirm the public Actions surface behaves as expected.
- Confirm cloned access works from the new public URL without private authentication.

## Stop Conditions

- Do not switch visibility if any secret, internal note, or private attachment is still present in history, issues, discussions, releases, or Actions logs.
- Do not switch visibility if the intended public release tag or release body is not finalized.
- Do not switch visibility if the operator still needs a stricter branch protection or contribution policy before opening inbound traffic.

# Security Policy

## Reporting

If Forge is hosted on a platform that supports private vulnerability reporting, use that channel first.
If no private channel is available yet, contact the maintainer through GitHub at `@nguyenphat57` (`https://github.com/nguyenphat57`) or open an issue with sanitized details only.
Do not post secrets, tokens, or full exploit instructions in public.

Include:

- affected package or workflow
- impact
- reproduction steps
- version or commit
- any mitigation already known
- preferred follow-up channel if a maintainer needs more detail

## Response Expectations

- A maintainer should acknowledge a clear report after triage.
- Fixes should land with verification evidence before any closure claim.
- Public advisories should avoid sharing active exploit details before a fix or mitigation exists.

## Scope

Report issues involving:

- secret handling
- install or activation flows
- runtime-tool execution boundaries
- host takeover or global entrypoint rewriting
- unsafe verification or release-path behavior

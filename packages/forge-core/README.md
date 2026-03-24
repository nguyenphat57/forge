# forge-core

Canonical Forge source package.

This package owns:

- registry
- routing and verification scripts
- shared workflows and references
- regression tests

Host adapters should overlay entry files and host metadata on top of this package, not fork its logic.

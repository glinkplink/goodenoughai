<!--
Complete every applicable section before requesting review. Keep this PR to one
reviewable contract. Documentation that explains changed behavior belongs here,
not in a follow-up documentation-only PR.
-->

## Contract and scope

- **Invariant this PR establishes or preserves:**
- **Affected boundaries (public inputs, construction helpers, persistence/hydration, outputs):**
- **Explicit non-goals / adjacent contracts excluded from this PR:**

## Documentation impact

- **Updated documents and why:**
- [ ] No documented behavior, scope, architecture, scoring, provenance, or assumption changed.

## Verification matrix

| Invariant / risk | Focused regression coverage | Command and final-head result |
|---|---|---|
| | | |

- [ ] I ran the relevant regression suite and recorded the exact command(s) above.
- [ ] I self-reviewed the final diff against the stated contract and non-goals.
- [ ] Where applicable, I tested direct construction, copy/clone helpers, unvalidated constructors, nested mutation, serialization, persistence, and hydration paths.

## Review and follow-ups

- **Codex review requested?** `No` by default. Set to `Yes` only if this PR matches a [high-impact Codex trigger](../docs/GIT_WORKFLOW.md#codex-review-high-impact-only); do not comment `@codex review` otherwise.
- **Self-review and verification completed on final head:**
- **In-scope findings fixed in this PR:**
- **Deferred, out-of-slice findings (issue/PR, owner, trigger, acceptance test, and merge gate):** `None`
- **Dependency / stack position (base PR and dependent PRs, if any):** `None`
- **Hard-cut disposition if review invalidates this slice:** preserve branch, close this PR without merging, and open replacement contract-scoped PRs.

- [ ] Every deferred finding is unreachable from behavior claimed by this PR.
- [ ] No current-slice P1 is deferred.

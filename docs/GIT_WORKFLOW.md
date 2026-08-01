> **Status:** Approved workflow guidance  
> **Authority:** Authoritative for branching, PRs, and direct-to-`main` work  
> **Last reviewed:** 2026-08-01  
> **Update when:** CI is added, `main` is protected, team size changes, or phase gates shift the default  
> **Related:** [AGENTS.md](../AGENTS.md), [PROJECT_STATE.md](PROJECT_STATE.md), [DECISION_LOG.md](DECISION_LOG.md), [ARCHITECTURE.md](ARCHITECTURE.md)

# Git workflow — branches, PRs, and direct commits to `main`

This repository is in **Phase 2** with a **solo maintainer**, **no CI gate yet**, and **no production deployment**. The default is therefore more permissive than a team project with protected `main` — but agents must still **classify each task** and **recommend** the right workflow before substantial work.

Human and agent contributors follow the same rules. See [DEC-0020](DECISION_LOG.md#dec-0020--tiered-git-workflow-main-vs-branchpr).

## Agent obligations (mandatory)

Coding agents (Cursor, Codex, GPT, Claude, etc.) must:

1. **Classify the planned change** using the decision rules below **before** non-trivial implementation or multi-file edits.
2. **State the recommended workflow** in the work plan: direct commits to `main`, or feature branch + pull request — with a one-line reason.
3. **Default to branch + PR** when any **Use branch + PR** rule matches, even if the user has not mentioned git workflow.
4. **Do not commit or push** unless the user explicitly requests it (repository user rule). Classification and recommendation still apply before work begins.
5. **Do not open a pull request** unless the user explicitly requests it (repository user rule). When branch + PR is recommended, say so and wait for approval before `gh pr create`.
6. **Re-evaluate** when scope grows during a task (e.g. a “small fix” touches migrations) — upgrade to branch + PR and say why.
7. **Use the PR readiness and review protocol** below for every PR. Do not substitute a sequence of bot-review-driven exploratory commits for local verification and a deliberate review checkpoint.

Trivial strictly bounded edits (per `AGENTS.md`) may land on `main` without a formal plan line if the change clearly matches **Push directly to `main`**.

## Quick decision

```text
START: What are you changing?

├─ Touches migrations, provenance, scoring, runner, adapters, artifact store,
│  corpus cases, public export, or benchmark batch semantics?
│     └─ YES → branch + PR (required)
│
├─ Multi-day, multi-file, or hard to revert?
│     └─ YES → branch + PR (required)
│
├─ Experimental — might be abandoned?
│     └─ YES → branch (PR when ready to merge)
│
├─ CI must pass before merge OR `main` is protected?
│     └─ YES → branch + PR (required)
│
├─ Second contributor involved OR external review needed?
│     └─ YES → branch + PR (required)
│
├─ Release / freeze milestone (Phase 3 RC, Phase 4 pilot, suite freeze)?
│     └─ YES → branch + PR (required)
│
├─ Trivial bounded edit (typo, approved decision log entry, changelog only)?
│     └─ YES → direct to `main` OK
│
└─ Otherwise: solo Phase 2 scaffold/docs with low blast radius
       └─ direct to `main` OK — prefer branch + PR if the diff will exceed ~300 lines
          or span more than one logical concern
```

## Push directly to `main`

Use when **all** of the following are true:

| Condition | Examples in this repo |
|-----------|-------------------------|
| Low blast radius | Doc typo, link fix, `CHANGELOG` entry, approved `DECISION_LOG` entry |
| Easy to revert | Single-file test or boundary tweak with no migration |
| No provenance or scoring impact | Comment-only or placeholder CLI help text |
| Short horizon | Completed in one session; no dependent follow-up PRs |
| Solo maintainer | No parallel branch from another person on the same subsystem |

**Typical Phase 2 direct-to-`main` work**

- Documentation reconciliation across `docs/` when behavior and scope are unchanged
- `PROJECT_STATE`, `roadmap`, or `index.md` updates after completed work
- Small fixes to unit tests that do not change persistence contracts
- Evidence README or script doc updates that do not change probe contracts

**Still require user approval to commit/push** — agents recommend `main`, implement locally, and commit only when asked.

## Use branch + pull request

Use when **any** of the following is true:

| Trigger | Why | Examples in this repo |
|---------|-----|------------------------|
| **Persistence contract** | Hard to revert; affects all future runs | New migration, `repository.py` idempotency or provenance rules |
| **Benchmark integrity** | Errors invalidate evidence or public claims | Scoring, parse rules, `batch_purpose`, planned-run identity |
| **Runner pipeline** | Large, cross-cutting slice | Artifact store, fake provider, adapter wiring, CLI execution paths |
| **Corpus / suite** | Freeze and review gates | New cases, schema changes, pilot or stable suite edits |
| **Public surface** | User-visible or export contract | Static site, public JSON schema, redaction |
| **Multi-day work** | Keeps `main` usable | “Implement artifact store” milestone |
| **Might abandon** | Branch deletes instead of cluttering history | Spikes and alternatives |
| **Review checkpoint** | Self-review or second pair of eyes | Milestone merge (“persistence hardening done”) |
| **CI or protection** | Policy enforces PR | *(not yet — revisit when added)* |
| **Multiple contributors** | Avoid merge conflicts and silent breaks | *(not yet — revisit when added)* |

**Branch naming** (when branching): `feat/<short-topic>`, `fix/<short-topic>`, `docs/<short-topic>`, `chore/<short-topic>`. One logical concern per branch.

**PR body must use [the repository PR template](../.github/PULL_REQUEST_TEMPLATE.md)** and include the declared contract, boundaries, explicit non-goals, documentation impact, verification matrix, exact test commands/results, and any strictly qualified deferrals.

## PR readiness and review protocol

This protocol keeps a PR a reviewable evidence package rather than a rolling refactor. It applies to human and agent authors, including solo work.

### Before implementation

Write the following in the PR description or task plan before changing behavior:

1. **Contract/invariant:** the precise property that must hold after the change.
2. **Boundaries:** the public inputs, construction helpers, persistence/hydration paths, and outputs that enforce or depend on that property.
3. **Explicit non-goals:** adjacent contracts deliberately excluded from this PR.
4. **Documentation impact:** each living/authoritative document that must change with the behavior, or `None — no documented behavior changed`.
5. **Verification matrix:** each invariant mapped to a focused regression test and the broader relevant test command.

If this analysis identifies multiple independently reviewable contracts, split them before opening the PR. Documentation that explains included behavior stays with that behavior; “code PR first, docs PR later” is not an acceptable split when behavior, architecture, scope, scoring, provenance, or assumptions change.

### Before requesting review

- Keep the PR draft while implementation is exploratory.
- Run the declared focused tests and the relevant regression suite; record exact commands and outcomes in the PR body.
- Self-review the final diff against the declared contract, non-goals, documentation impact, and verification matrix.
- For validation/immutability contracts, test each exposed bypass path: direct construction, copy/clone helpers, unvalidated constructors, nested mutation, serialization, persistence, and hydration as applicable.
- Update the relevant living documentation in the same PR and update the decision log/changelog when required by `AGENTS.md`.
- Mark the PR ready for merge after self-review and recorded verification. Request **Codex review only** when the PR matches the high-impact triggers in [Codex review (high-impact only)](#codex-review-high-impact-only). Do not comment `@codex review` on routine PRs. If an integration reviews every push anyway, do not push a separate commit for each comment; batch an intentional response when a review actually matters.

### Codex review (high-impact only)

Codex is an **optional second pass**, not a default merge gate. Routine contract-scoped PRs rely on self-review, the verification matrix, and user approval to merge.

**Request Codex review (`@codex review`) only when any of the following is true:**

| Trigger | Why Codex |
|---------|-----------|
| **Persistence semantics change** | New migration or altered repository rules that can corrupt or mis-hydrate batches, planned runs, or checksums |
| **Provenance or scoring integrity** | Changes to collected-response binding, parse/score contracts, `batch_purpose`, planned-run identity, or reproduction checksum meaning |
| **Runner / adapter / execution path** | First real adapter, runner execution, artifact write paths, or anything that can reach model APIs |
| **Public or export surface** | Public JSON schema, static site output, redaction, or anything user-visible outside the repo |
| **Corpus / suite freeze** | Pilot-locked or stable benchmark cases, prompts, thresholds, or scorer versions |
| **Hard-to-revert blast radius** | Multi-subsystem change, unclear invariant, or a slice where a silent integrity bug would invalidate benchmark evidence |

**Do not request Codex review for:**

- Documentation-only PRs with no behavior change
- Changelog, decision-log, or state reconciliation after approved work
- Single-contract Phase 2 slices that passed self-review and the declared verification matrix
- Test-only fixes that do not change contracts
- Follow-up PRs that address already-reviewed adjacent contracts unless the new diff reopens a high-impact trigger above

When Codex is **not** requested, stale automated review threads on earlier commits are not merge blockers. Treat passing self-review, tests, and the PR contract as sufficient unless the user explicitly asks for Codex or human review.

When Codex **is** requested, use one deliberate pass: batch fixes, re-run verification on the final head, and only then ask for a final re-review if still needed.

### Hard-cut rule for review churn

Stop patching and re-slice the work when any of the following occurs:

- A valid finding belongs to a contract explicitly listed as a non-goal.
- A second successive review-response update introduces another independently reviewable contract.
- The required fixes make the PR's declared invariant, boundaries, or verification matrix no longer an honest description of the diff.

Closing the PR preserves its branch, commits, and review history. It is the required recovery path for an incoherent review slice, not a failure to be hidden by more patches. Create replacement draft PRs in explicit dependency order, each with a fresh contract, non-goals, and verification matrix. A P1 may not merge unaddressed; it may be moved into the replacement PR that owns its contract.

### Triage review findings

| Finding type | Required disposition |
|---|---|
| Breaks the PR’s declared invariant, a claimed behavior, data integrity, provenance, scoring, or public contract | Fix and test before merge. A P1 in the current slice is never silently deferred. |
| Valid adjacent concern in a different contract | Keep the current PR scoped. Create a specifically titled follow-up with owner, trigger, acceptance test, and required merge gate before it can become reachable. |
| Incorrect or no longer applicable finding | Reply with evidence and resolve the thread when the platform permits. |
| Scope-changing finding | Stop the review loop and ask the user whether to re-scope the PR or take the follow-up path. Do not expand it by default. |

When the hard-cut rule applies, classify the existing PR as incoherent and close it without merging after preserving its branch. Do not make the next review-response commit first.

A deferred finding is allowed only when it cannot undermine behavior claimed by the PR. Its follow-up must state the exact affected path, trigger, owner, acceptance test, and the point by which it must land. For benchmark-integrity or provenance risk, also update the project risk/state documentation.

### Merge gate

Before merge, confirm all of the following:

- The final diff still matches one declared contract.
- Required documentation is included and internally consistent.
- The declared verification matrix passed on the final head.
- In-scope findings are fixed, tested, and responded to; stale/outdated threads are not treated as unresolved defects without checking current code.
- Each deferral meets the rule above and is not a substitute for fixing a current-slice P1.

## Phase-aware defaults

| Phase | Direct to `main` | Branch + PR |
|-------|------------------|-------------|
| **Phase 2** (current) | Docs, governance, small scaffold, non-contract tests | Migrations, repository, artifact store, runner slices, loaders |
| **Phase 3** (RC corpus/scoring) | Doc/state updates only | Corpus YAML, scorers, prompt templates, anything pilot-locked |
| **Phase 4** (diagnostic pilot) | — | **All** code and corpus changes that could affect pilot validity |
| **Phase 5+** (stable batch, site) | Trivial docs | Stable batch runs, publication export, static site features |
| **After CI added** | — | **All** code changes; docs may still go direct if trivial |

When Phase 4 pilot work begins, treat **branch + PR as mandatory** for any change that could alter scores, provenance, or case content until the investment gate in [DEC-0019](DECISION_LOG.md#dec-0019--pre-freeze-pilot-and-pre-launch-investment-gate) is recorded.

## Change-type routing table

| If you are… | Workflow |
|-------------|----------|
| Fixing a typo in one doc | Direct to `main` |
| Reconciling docs after approved work (no behavior change) | Direct to `main` |
| Adding DEC/CHANGELOG after approved decision | Direct to `main` |
| Adding a SQLite migration | Branch + PR |
| Changing `repository.py` or batch/planned-run rules | Branch + PR |
| Implementing artifact store, runner, or adapters | Branch + PR |
| Implementing scoring or parse logic | Branch + PR |
| Authoring or editing benchmark cases | Branch + PR |
| Adding or changing public JSON / static site | Branch + PR |
| Spike that might be discarded | Branch (PR if merging) |
| User says “commit to main” / “open a PR” | Follow explicit user instruction |

## What agents should say (template)

Before substantial work:

```text
Git workflow: [direct to main | branch + PR] — [one-line reason from rules above].
Commits/PR: [will wait for your request | user requested commit/PR].
```

Example:

```text
Git workflow: branch + PR — adds migration 0003 and changes planned-run provenance rules.
Commits/PR: will wait for your request.
```

## Future triggers (revisit this doc when)

- GitHub Actions or other CI runs on PRs → default to branch + PR for all code
- `main` branch protection enabled → branch + PR required for merges
- Second regular contributor → branch + PR for overlapping subsystems
- First production deploy → branch + PR for anything touching export or site

Record material changes in [DECISION_LOG.md](DECISION_LOG.md) and [CHANGELOG.md](CHANGELOG.md).

## Related documents

- [AGENTS.md](../AGENTS.md) — mandatory agent rules
- [PROJECT_STATE.md](PROJECT_STATE.md) — current phase and next actions
- [ARCHITECTURE.md](ARCHITECTURE.md) — components that warrant branch isolation
- [EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md) — run integrity during pilot phases

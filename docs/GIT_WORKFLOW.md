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

**PR body should include**: summary, test plan (`unittest` commands run), and whether docs/decision log were updated.

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

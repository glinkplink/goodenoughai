# GoodEnough.ai — Documentation index

Compact routing map. Read [`AGENTS.md`](AGENTS.md) first. The exhaustive on-demand catalog is [`DOCUMENTATION_ROUTER_REFERENCE.md`](DOCUMENTATION_ROUTER_REFERENCE.md).

## Core documents

| Document | Use it for |
|---|---|
| [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md) | Current phase, blockers, and next actions; load for non-trivial work |
| [`docs/MVP_SCOPE.md`](docs/MVP_SCOPE.md) | Binding MVP question, exclusions, and acceptance criteria |
| [`docs/MVP_MASTER_PLAN.md`](docs/MVP_MASTER_PLAN.md) | Cross-cutting direction and approved requirement crosswalk |
| [`roadmap.md`](roadmap.md) | Phase sequencing and delivery gates |
| [`docs/DECISION_LOG.md`](docs/DECISION_LOG.md) | Current approved decisions (DEC-0018 onward) |
| [`docs/DECISION_LOG_ARCHIVE.md`](docs/DECISION_LOG_ARCHIVE.md) | Full records for DEC-0001 through DEC-0017 |
| [`docs/GIT_WORKFLOW.md`](docs/GIT_WORKFLOW.md) | Branch/PR classification, review protocol, and Codex triggers |
| [`docs/CHANGELOG.md`](docs/CHANGELOG.md) | Shipped and significant technical changes |

## Quick task routing

| Task | Read |
|---|---|
| Bounded edit | `AGENTS.md` and the target file |
| Feature, benchmark, UI, or scope work | `MVP_SCOPE.md`, then the matching authority in the router reference |
| Cross-cutting work, phase planning, priority changes, or ambiguity | `MVP_MASTER_PLAN.md`, `roadmap.md`, `DECISION_LOG.md`, and the archive only when older rationale matters |
| Git workflow or PR review | `GIT_WORKFLOW.md` and the PR template |
| Full document inventory | `DOCUMENTATION_ROUTER_REFERENCE.md` |

## Source-of-truth reminder

```text
initialprompt.md     = original founding specification (historical)
docs/MVP_MASTER_PLAN.md = approved primary living MVP plan
roadmap.md           = current phased delivery plan (living)
docs/PROJECT_STATE.md = current operational handoff (living)
docs/MVP_SCOPE.md    = authoritative scope boundary
docs/DECISION_LOG.md = current approved decisions
index.md             = compact documentation router (this file)
AGENTS.md            = mandatory agent working rules
```

When `initialprompt.md` and living docs conflict, record the conflict in [`docs/RISKS_AND_ASSUMPTIONS.md`](docs/RISKS_AND_ASSUMPTIONS.md) or [`docs/DECISION_LOG.md`](docs/DECISION_LOG.md). Do not silently reconcile.

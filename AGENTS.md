# AGENTS.md — Repository instructions for coding agents

**GoodEnough.ai** helps automation builders choose inexpensive AI models for structured extraction, classification, and normalization — not universal intelligence rankings.

## Read policy

Load durable constraints first and detailed material only when the task needs it. Do not treat a documentation router or a historical plan as required reading for a trivial, strictly bounded edit.

1. **Any non-trivial planning or implementation:** read this file and [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md), then consult the **Quick task routing** section of [`index.md`](index.md) to select the authoritative documents for the task.
2. **Feature, benchmark, UI, or scope work:** read [`docs/MVP_SCOPE.md`](docs/MVP_SCOPE.md) and the relevant task specification named in `index.md` (for example, scoring, benchmark, architecture, protocol, or provenance).
3. **Cross-cutting work, phase planning, priority changes, or ambiguity:** also read [`docs/MVP_MASTER_PLAN.md`](docs/MVP_MASTER_PLAN.md), [`roadmap.md`](roadmap.md), and, when a prior choice matters or documents conflict, [`docs/DECISION_LOG.md`](docs/DECISION_LOG.md).
4. **Trivial, strictly bounded edits:** read this file and the file being changed; load additional documentation only if the edit could affect behavior, scope, policy, or a factual claim.
5. Treat [`initialprompt.md`](initialprompt.md) as the **original project brief and historical foundation** — use it for origin intent or ambiguity, not as the default current decision source.
6. Treat **living documentation** and the **approved decision log** as the current source of truth.

## Mandatory rules

- **Preserve the narrow MVP question and audience.** Do not broaden into universal benchmarking, creative writing, coding leaderboards, multimodal tests, community voting, or enterprise observability without an approved scope change.
- **Never mix exact API/local model results with opaque consumer-web assistant results.** See [`docs/BENCHMARK_SPEC.md`](docs/BENCHMARK_SPEC.md) and [`docs/PROVENANCE_AND_REPRODUCIBILITY.md`](docs/PROVENANCE_AND_REPRODUCIBILITY.md).
- **Record exact model identity:** provider surface, collection method, benchmark version, pricing date, hardware, and quantization where applicable.
- **Prefer deterministic scoring** for central MVP metrics. LLM-as-judge is secondary and non-authoritative.
- **Never hardcode changing model prices** as permanent facts. Store pricing snapshots with effective dates.
- **Never expose** API keys, credentials, private datasets, or secrets.
- **Update documentation** when implementation changes project behavior, scope, architecture, scoring, or assumptions.
- **Update [`index.md`](index.md)** whenever documentation is added, moved, renamed, deprecated, or removed.
- **Update [`roadmap.md`](roadmap.md) and [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md)** when milestones or current priorities change.
- **Add meaningful decisions** to [`docs/DECISION_LOG.md`](docs/DECISION_LOG.md).
- **Add user-visible or technically significant changes** to [`docs/CHANGELOG.md`](docs/CHANGELOG.md).
- **Run relevant tests and documentation-link validation** before completing implementation tasks.
- **Never claim** a command, model, price, benchmark result, or hardware capability was verified unless it actually was.
- **Stop and surface unresolved contradictions** instead of silently choosing an interpretation.
- **Classify git workflow before non-trivial work.** State whether the change should use direct commits to `main` or a feature branch + pull request, using [`docs/GIT_WORKFLOW.md`](docs/GIT_WORKFLOW.md). Default to branch + PR when the change touches migrations, provenance, scoring, runner/adapters, artifact store, corpus cases, or public export — or when work is multi-day or hard to revert. Do not commit or open a PR unless the user explicitly requests it; still recommend the workflow before starting.
- **Make one reviewable contract change per PR.** Define the invariant, affected write/read boundaries, explicit non-goals, documentation impact, and verification plan before implementation. Keep documentation that describes the changed behavior in the same PR; do not split it out merely to reduce diff size.
- **Do not turn review into a rolling refactor.** A finding that crosses into another contract belongs in a separately scoped follow-up unless the user explicitly approves re-scoping the current PR. A current-slice P1 must be fixed before merge. A genuinely out-of-slice finding may be deferred only with its trigger, owner, merge gate, and tracked follow-up recorded; it must not invalidate any behavior claimed by the current PR.
- **Hard-cut review churn.** If review exposes more than one independently reviewable contract, a finding outside the declared contract, or a second successive review-response expansion, stop patching that PR. Preserve the branch, close the PR without merging, and create replacement PRs with explicit dependency order. Do not treat closing a PR as data loss or a reason to keep an incoherent PR open.
- **Prove privileged/bypass paths.** When a contract relies on validation or immutability, add focused regression coverage for every public construction, mutation, persistence, and hydration path that could bypass it (including Pydantic construction/copy helpers where exposed).
- **Use one deliberate review pass.** Complete local verification and self-review before merge. Request **Codex review only** for extremely dangerous or high-impact PRs defined in [`docs/GIT_WORKFLOW.md`](docs/GIT_WORKFLOW.md#codex-review-high-impact-only). Do not comment `@codex review` on routine contract-scoped PRs. Batch any required feedback into one update where practical. Follow [`docs/GIT_WORKFLOW.md`](docs/GIT_WORKFLOW.md#pr-readiness-and-review-protocol) and use [the PR template](.github/PULL_REQUEST_TEMPLATE.md).

## Git workflow (summary)

Full rules: [`docs/GIT_WORKFLOW.md`](docs/GIT_WORKFLOW.md). Agents must recommend a workflow **before** non-trivial implementation.

| Push directly to `main` | Use branch + pull request |
|-------------------------|---------------------------|
| Trivial bounded edits; docs/changelog/decision log with no behavior change | Migrations, repository contracts, artifact store, runner, adapters |
| Single-session low-risk scaffold or test fixes | Scoring, parse logic, `batch_purpose`, planned-run identity |
| Phase 2 docs/state reconciliation | Corpus cases, pilot or stable suite edits |
| | Multi-day or multi-file work; experiments you might abandon |
| | Phase 4+ pilot-validity changes; CI or protected `main` when added |

Say explicitly: `Git workflow: [direct to main | branch + PR] — [reason].` Wait for user request before `git commit` or `gh pr create`.

## Source-of-truth hierarchy

When documents conflict, resolve in this order (higher wins):

1. Explicit current user instruction
2. This file (`AGENTS.md`) repository rules
3. Approved entries in [`docs/DECISION_LOG.md`](docs/DECISION_LOG.md)
4. [`docs/MVP_SCOPE.md`](docs/MVP_SCOPE.md)
5. [`docs/MVP_MASTER_PLAN.md`](docs/MVP_MASTER_PLAN.md)
6. [`roadmap.md`](roadmap.md) and [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md)
7. Task-specific technical specifications
8. Other supporting documentation
9. [`initialprompt.md`](initialprompt.md) as the original historical brief

A newer explicit approved decision may supersede older planning material.

## Core MVP question

> Which inexpensive AI model should an automation builder use for structured extraction, classification, and normalization?

## Key documents

| Document | Purpose |
|----------|---------|
| [`index.md`](index.md) | Documentation router — start here for task-specific docs |
| [`docs/MVP_MASTER_PLAN.md`](docs/MVP_MASTER_PLAN.md) | Primary living MVP plan and historical-requirement crosswalk |
| [`roadmap.md`](roadmap.md) | Phased delivery plan |
| [`initialprompt.md`](initialprompt.md) | Original founding specification (historical) |
| [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md) | Current operational handoff |
| [`docs/MVP_SCOPE.md`](docs/MVP_SCOPE.md) | Authoritative scope boundary |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System design and component boundaries |
| [`docs/BENCHMARK_SPEC.md`](docs/BENCHMARK_SPEC.md) | Benchmark purpose, corpus, and surface rules |
| [`docs/SCORING_AND_EVALUATION.md`](docs/SCORING_AND_EVALUATION.md) | Metrics, formulas, and verdict labels |
| [`docs/DECISION_LOG.md`](docs/DECISION_LOG.md) | Approved project decisions |
| [`docs/RISKS_AND_ASSUMPTIONS.md`](docs/RISKS_AND_ASSUMPTIONS.md) | Risk register and open assumptions |
| [`docs/GIT_WORKFLOW.md`](docs/GIT_WORKFLOW.md) | When to branch and open PRs vs commit directly to `main` |

## What not to do without approval

- Implement production application code when the task is documentation-only
- Install dependencies, scaffold infrastructure, or run paid API benchmarks unless explicitly requested
- Broaden MVP scope or add task families beyond the three defined in `MVP_SCOPE.md`
- Present planned features as completed
- Rename or move `initialprompt.md` or `roadmap.md` without compelling reason

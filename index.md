# GoodEnough.ai — Documentation index

Primary map for humans and coding agents. Read [`AGENTS.md`](AGENTS.md) before substantial work.

---

## Start here

| Document | Purpose | Authority | Read when | Update when |
|----------|---------|-----------|-----------|-------------|
| [AGENTS.md](AGENTS.md) | Mandatory cross-agent repository rules | **Authoritative** | Every agent session before planning or implementation | Agent rules, source-of-truth hierarchy, or mandatory workflows change |
| [docs/MVP_MASTER_PLAN.md](docs/MVP_MASTER_PLAN.md) | Primary living plan and historical-requirement crosswalk | **Living primary plan** | Planning any MVP work or checking the approved end-to-end path | Scope, architecture, gates, cost cap, or priorities change |
| [roadmap.md](roadmap.md) | Phased delivery plan from vision to validation launch | **Living** | Planning milestones, prioritization, or phase scope | Phase goals, deliverables, or timeline change |
| [docs/PROJECT_STATE.md](docs/PROJECT_STATE.md) | Compact current-state handoff for each session | **Living** | Start of every implementation session | Phase, blockers, next actions, or completed work change |
| [docs/MVP_SCOPE.md](docs/MVP_SCOPE.md) | Authoritative MVP scope boundary | **Authoritative** | Any feature, benchmark, or UI work | Scope expands, narrows, or acceptance criteria change |
| [docs/DECISION_LOG.md](docs/DECISION_LOG.md) | Record of approved project decisions | **Authoritative** | Resolving conflicts or checking past choices | A decision is proposed, approved, superseded, or rejected |
| [README.md](README.md) | Human-facing repository introduction | **Living** | Onboarding new contributors | Repository status or entry points change |

---

## Product and scope

| Document | Purpose | Authority | Read when | Update when |
|----------|---------|-----------|-----------|-------------|
| [docs/PRODUCT_BRIEF.md](docs/PRODUCT_BRIEF.md) | Strategic product definition, differentiation, non-goals | **Supporting** | Understanding why the product exists | Product thesis or positioning changes |
| [docs/MVP_SCOPE.md](docs/MVP_SCOPE.md) | Exact MVP question, in/out of scope, acceptance criteria | **Authoritative** | Scoping any work | *(see Start here)* |
| [docs/MONETIZATION_AND_VALIDATION.md](docs/MONETIZATION_AND_VALIDATION.md) | Revenue validation sequence and kill criteria | **Supporting** | Business validation or custom-benchmark offers | Monetization strategy or validation metrics change |

---

## Benchmark methodology

| Document | Purpose | Authority | Read when | Update when |
|----------|---------|-----------|-----------|-------------|
| [docs/BENCHMARK_SPEC.md](docs/BENCHMARK_SPEC.md) | Task taxonomy, corpus design, surface separation rules | **Authoritative** | Creating cases, running benchmarks, publishing results | Corpus design, task families, or comparison rules change |
| [docs/MODEL_LAUNCH_SET.md](docs/MODEL_LAUNCH_SET.md) | Initial candidate models and selection rubric | **Living** | Selecting or adding models to a batch | Models verified, substituted, or expanded |
| [docs/EXPERIMENT_PROTOCOL.md](docs/EXPERIMENT_PROTOCOL.md) | Controlled-run procedure and rerun policy | **Authoritative** | Executing or reviewing benchmark runs | Run procedure, repetition policy, or import rules change |
| [docs/SCORING_AND_EVALUATION.md](docs/SCORING_AND_EVALUATION.md) | Metrics, formulas, thresholds, verdict labels | **Authoritative** | Implementing scorers or interpreting results | Scoring logic, thresholds, or verdict definitions change |
| [docs/PROVENANCE_AND_REPRODUCIBILITY.md](docs/PROVENANCE_AND_REPRODUCIBILITY.md) | Required metadata and reproducibility limits | **Authoritative** | Storing runs, publishing evidence, auditing batches | Provenance fields or public/private rules change |

---

## Technical architecture

| Document | Purpose | Authority | Read when | Update when |
|----------|---------|-----------|-----------|-------------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System context, components, pipeline boundaries | **Living** | Designing or implementing any subsystem | Architecture choice approved or components added |
| [docs/DATA_MODEL.md](docs/DATA_MODEL.md) | Conceptual entities and relationships | **Supporting** | Database design, API design, or data flow | Entity definitions or versioning rules change |

---

## Execution and project state

| Document | Purpose | Authority | Read when | Update when |
|----------|---------|-----------|-----------|-------------|
| [docs/MVP_MASTER_PLAN.md](docs/MVP_MASTER_PLAN.md) | Approved end-to-end MVP plan and requirement crosswalk | **Living primary plan** | Starting any phase | MVP assumptions, gates, or immediate actions change |
| [docs/PROJECT_STATE.md](docs/PROJECT_STATE.md) | Current phase, blockers, next actions | **Living** | *(see Start here)* | *(see Start here)* |
| [roadmap.md](roadmap.md) | Phased implementation sequence | **Living** | *(see Start here)* | *(see Start here)* |

---

## Governance

| Document | Purpose | Authority | Read when | Update when |
|----------|---------|-----------|-----------|-------------|
| [docs/DECISION_LOG.md](docs/DECISION_LOG.md) | Approved decisions with rationale | **Authoritative** | *(see Start here)* | *(see Start here)* |
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | Repository and product change history | **Living** | Checking what changed recently | User-visible or significant technical changes ship |
| [docs/RISKS_AND_ASSUMPTIONS.md](docs/RISKS_AND_ASSUMPTIONS.md) | Risk register, assumptions, and factual unknowns | **Living** | Planning, prioritization, or before major bets | Risks identified, mitigated, or assumptions verified |

---

## Business validation

| Document | Purpose | Authority | Read when | Update when |
|----------|---------|-----------|-----------|-------------|
| [docs/MONETIZATION_AND_VALIDATION.md](docs/MONETIZATION_AND_VALIDATION.md) | Validation sequence, pricing hypotheses, kill criteria | **Supporting** | Launch planning or custom-benchmark sales | Validation results or offer structure change |

---

## Templates

| Document | Purpose | Authority | Read when | Update when |
|----------|---------|-----------|-----------|-------------|
| [docs/templates/BENCHMARK_CASE_TEMPLATE.yaml](docs/templates/BENCHMARK_CASE_TEMPLATE.yaml) | Standard benchmark case format | **Template** | Authoring new benchmark cases | Case schema or acceptance-rule format changes |
| [docs/templates/DECISION_RECORD_TEMPLATE.md](docs/templates/DECISION_RECORD_TEMPLATE.md) | Standard decision log entry | **Template** | Recording a new decision | Decision log format changes |
| [docs/templates/EXPERIMENT_REPORT_TEMPLATE.md](docs/templates/EXPERIMENT_REPORT_TEMPLATE.md) | Post-batch experiment report | **Template** | Completing a benchmark batch | Report sections or required fields change |
| [docs/templates/MODEL_PROFILE_TEMPLATE.md](docs/templates/MODEL_PROFILE_TEMPLATE.md) | Model identity and capability profile | **Template** | Onboarding a model to the launch set | Model profile fields change |

---

## Historical source material

| Document | Purpose | Authority | Read when | Update when |
|----------|---------|-----------|-----------|-------------|
| [initialprompt.md](initialprompt.md) | **Original founding specification** — comprehensive MVP master-plan prompt | **Historical** | Understanding origin intent, detailed constraints, or resolving ambiguities in newer docs | Do not update for current decisions; link from newer docs instead |

### Document relationship

```text
initialprompt.md     = original founding specification (historical)
docs/MVP_MASTER_PLAN.md = approved primary living MVP plan
roadmap.md           = current phased delivery plan (living)
docs/PROJECT_STATE.md = current operational handoff (living)
docs/MVP_SCOPE.md    = authoritative scope boundary
docs/DECISION_LOG.md = authoritative record of approved changes
index.md             = repository documentation router (this file)
AGENTS.md            = mandatory agent working rules
```

When `initialprompt.md` and living docs conflict, record the conflict in [`docs/RISKS_AND_ASSUMPTIONS.md`](docs/RISKS_AND_ASSUMPTIONS.md) or [`docs/DECISION_LOG.md`](docs/DECISION_LOG.md). Do not silently reconcile.

---

## Quick task routing

| If you are… | Read first |
|-------------|------------|
| Starting any agent session | `AGENTS.md` → `docs/PROJECT_STATE.md` → `docs/MVP_MASTER_PLAN.md` → `index.md` |
| Implementing the benchmark runner | `docs/ARCHITECTURE.md` → `docs/EXPERIMENT_PROTOCOL.md` → `docs/DATA_MODEL.md` |
| Authoring benchmark cases | `docs/BENCHMARK_SPEC.md` → `docs/templates/BENCHMARK_CASE_TEMPLATE.yaml` |
| Implementing scoring | `docs/SCORING_AND_EVALUATION.md` → `docs/BENCHMARK_SPEC.md` |
| Adding a model | `docs/MODEL_LAUNCH_SET.md` → `docs/PROVENANCE_AND_REPRODUCIBILITY.md` |
| Building public pages | `docs/MVP_SCOPE.md` → `docs/ARCHITECTURE.md` → `roadmap.md` Phase 6 |
| Proposing scope change | `docs/MVP_SCOPE.md` → `docs/DECISION_LOG.md` → `docs/RISKS_AND_ASSUMPTIONS.md` |

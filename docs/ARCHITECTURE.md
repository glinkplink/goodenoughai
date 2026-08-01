> **Status:** Approved for MVP  
> **Authority:** Living architecture specification  
> **Last reviewed:** 2026-07-31  
> **Update when:** Components, interfaces, persistence, or deployment choices change  
> **Related:** [MVP_MASTER_PLAN.md](MVP_MASTER_PLAN.md), [DATA_MODEL.md](DATA_MODEL.md), [EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md), [DECISION_LOG.md](DECISION_LOG.md)

# Architecture

## Approved architecture

The MVP is a **local-first modular monolith**:

| Component | Approved choice |
|-----------|-----------------|
| Benchmark runner | Python 3.10+ package and resumable CLI |
| Validation schemas | Pydantic plus JSON Schema |
| Local inference | Ollama on TheImp |
| Cloud inference | Direct provider adapters; OpenRouter as distinct fallback surface |
| Operational database | SQLite with tracked migrations |
| Raw artifacts | Immutable local filesystem objects with checksums |
| Publication boundary | Versioned, redacted, schema-validated public JSON |
| Public site | TypeScript Next.js static export |
| Default deployment | Cloudflare Pages |
| Intake | Configurable hosted form endpoint |
| Analytics | Privacy-safe events; provider selected at deployment time |

Supabase/PostgreSQL, authentication, payments, Redis, live routing, public APIs, subscriptions, and remote workers are deferred.

## System context

```text
                  benchmark operator
                          │
                          ▼
┌──────────────────────────────────────────────────────┐
│ Python CLI / modular benchmark package               │
│ cases · profiles · batches · adapters · scoring      │
└────────────┬──────────────────────┬──────────────────┘
             │                      │
             ▼                      ▼
      Ollama on TheImp       provider APIs / imports
      local_exact            api_exact / separate imports
             │                      │
             └──────────┬───────────┘
                        ▼
             immutable filesystem artifacts
                        │
                        ▼
                 SQLite repository
                        │
          parse → score → aggregate → simulate
                        │
                        ▼
             redacted versioned public JSON
                        │
                        ▼
             Next.js static export / CDN
```

The public website cannot query the operational SQLite database or private artifact tree. Publication is an explicit, validated export step.

## Options considered

| Option | Strengths | Costs / risks | Decision |
|--------|-----------|---------------|----------|
| Local-first: Python + SQLite + filesystem + public JSON + static Next.js | Lowest cost, easiest audit/reproduction, no service dependency, solo-maintainable | Manual publication; single-machine operation | **Approved** |
| Managed application: Python + Supabase/Postgres + storage + dynamic Next.js | Easier multi-user/backend growth | Auth/storage/schema/ops work before demand; recurring service dependency | Deferred until validation |
| Distributed workers: managed DB + Redis + remote workers | Continuous scale and isolation | Unnecessary services and cost for 1,350-run batch | Deferred |
| Serverless-only runner | Easy cloud deployment | Cannot credibly cover local inference on TheImp | Rejected for MVP |

## Core interfaces

### Adapter boundary

```python
class ModelAdapter(Protocol):
    async def run(self, request: BenchmarkRequest) -> BenchmarkResponse: ...
```

Adapters collect responses only. They contain no parsing, scoring, pricing, or verdict logic.

Initial adapters:

| Adapter | Surface treatment |
|---------|-------------------|
| `OllamaAdapter` | `local_exact` |
| `GeminiAdapter` | `api_exact` or separately profiled `cli_exact` |
| `OpenAIAdapter` | `api_exact` through Responses API |
| `DeepSeekAdapter` | Direct-provider `api_exact`; primary DeepSeek launch profile |
| `OpenRouterAdapter` | Distinct `api_exact` provider surface; fallback/extra profile only |
| `ManualImportAdapter` | `manual_import`; separate publication section |
| `AutoGeminiImportAdapter` | `manual_import` or `web_declared`; separate publication section |

### Artifact boundary

```python
class ArtifactStore(Protocol):
    def write_immutable(self, *, run_id: str, body: bytes) -> ArtifactRef: ...
    def verify(self, ref: ArtifactRef) -> bool: ...
```

The filesystem implementation writes original provider bytes before parsing, uses content checksums, rejects conflicting rewrites, and returns an opaque storage reference. Raw/private artifact directories are untracked.

### Repository boundary

```python
class Repository(Protocol):
    # suites, cases, profiles, batches, runs, parses, scores,
    # prices, reviews, exports, simulations
    ...
```

SQLite ships first behind a repository interface. Migrations are tracked; database files are not. SQL and domain boundaries avoid SQLite-specific behavior where a future PostgreSQL move would otherwise require redesign.

### CLI boundary

```text
goodenough-bench cases validate
goodenough-bench models probe
goodenough-bench batch run
goodenough-bench batch score
goodenough-bench batch export
goodenough-bench batch reproduce
goodenough-bench import
```

Commands are conceptual until Phase 2 implementation. Each command is resumable or read-only where appropriate and emits machine-readable status.

### Public JSON boundary

Each release directory contains schema-validated JSON for:

- Release metadata and checksums
- Task-family definitions
- Redacted model and provider profiles
- Aggregate scorecards and verdicts
- Evidence manifests and individual public run records
- Pricing snapshot references
- Routing simulations

The export is versioned and immutable. Any correction creates a new release version and changelog entry.

## Pipelines

### Case and suite freeze

Versioned YAML → schema validation → quota validation → two-pass human review check → suite manifest → checksum → freeze.

### Collection

Frozen case → prompt build/hash → adapter request → immutable raw write → SQLite run record. The artifact write precedes parse/scoring.

### Parsing and scoring

Raw bytes → strict JSON parse → schema validation → deterministic field/trust scoring → case pass → model/family aggregation → verdict.

Partial or repaired JSON fails parse scoring. Provider failures bypass model-quality scoring and remain in availability metrics.

### Simulation

Frozen primary scores + predeclared deterministic escalation triggers + escalation-model scores/prices → blended reliability, cost, and latency estimates.

### Publication

Frozen batch → provenance validation → redaction → public JSON schema validation → checksums → static site build → route/accessibility/link tests → deploy.

## Static site routes

| Route | Data |
|-------|------|
| `/` | Release summary and best-value highlights |
| `/benchmarks/[family]` | Per-family multidimensional scorecards |
| `/models/[slug]` | Exact surface identity, results, cost, limitations |
| `/compare` | Two-to-three model comparison within a family |
| `/runs/[run-id]` | Redacted evidence and score breakdown |
| `/methodology` | Cases, prompts, scoring, repetitions, caveats |
| `/custom-benchmark` | Hosted-form intake; no local persistence |

## Run orchestration defaults

- One model loaded/executed at a time
- Seeded case order, recorded in batch metadata
- Three separate repetition rounds rather than three adjacent calls per case
- One unscored warmup per local model
- Resume by planned-run identity; never duplicate a completed repetition
- Local scored timeout: 120 seconds; cloud timeout: 60 seconds
- Up to three retries for transient 429/5xx; retry attempts do not become repetitions

## Failure handling

| Failure | Behavior |
|---------|----------|
| Adapter timeout / exhausted transient retries | Record availability error; continue resumable batch |
| Authentication or identity mismatch | Stop that surface before paid/stable runs |
| Artifact write/checksum failure | Do not create a scoreable run; stop batch segment |
| Parse/schema failure | Retain raw; score applicable integrity failure |
| Scorer exception | Retain raw/parse; stop scoring step and resume after fix |
| SQLite unavailable/corrupt | Stop; no partial publication |
| Export redaction/schema failure | Block publication |
| TheImp hardware gate failure | Mark profile “Impractical on this hardware”; do not count as quality failure |

## Security and privacy boundaries

- Credentials enter through environment variables or an approved secret manager; never SQLite, raw evidence, logs, JSON exports, or git
- Redact auth headers, internal IDs/URLs, and private data before public export
- Public suite and private customer projects use separate roots and databases
- Public synthetic cases contain no customer data
- The public intake form accepts metadata only and no example-file upload
- Public case source text is limited to 64 KiB and an individual case YAML file to 256 KiB; import JSONL lines are limited to 1 MiB unless a versioned protocol change approves otherwise
- Qualified private projects use a separate transfer path; default total submitted examples are limited to 10 MiB, with lower provider/model limits enforced before calls
- Private inputs, raw outputs, and operational copies are deleted within 30 calendar days after final delivery or earlier withdrawal unless a written engagement sets a different period; deletion status is recorded
- No customer data enters the public suite without explicit written permission
- Source text is untrusted data and cannot override benchmark instructions
- Dataset and model-output licenses are reviewed before publication

## Tracked and untracked data

Tracked:

- Migrations, case YAML, schemas, prompt templates, model profiles, pricing snapshots, public JSON schemas, redacted release exports

Untracked:

- SQLite database files, raw artifacts, credentials, private customer inputs, transient logs, local model files

Repository ignore rules are a Phase 2 acceptance requirement.

## Future migration triggers

Reconsider managed Postgres/object storage only when one of these is true:

- More than one trusted operator needs concurrent writes
- Public releases require automated remote publication
- Artifact volume or backup requirements exceed safe local operation
- A paid private-project workflow requires authenticated access
- Remote benchmark workers are approved

Any migration requires a new approved decision and keeps the repository/artifact/public-JSON interfaces stable.

## Related documents

- [MVP_MASTER_PLAN.md](MVP_MASTER_PLAN.md)
- [DATA_MODEL.md](DATA_MODEL.md)
- [EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md)
- [PROVENANCE_AND_REPRODUCIBILITY.md](PROVENANCE_AND_REPRODUCIBILITY.md)
- [DECISION_LOG.md](DECISION_LOG.md)

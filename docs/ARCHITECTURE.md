> **Status:** Approved for MVP  
> **Authority:** Living architecture specification  
> **Last reviewed:** 2026-08-01
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
    def read_bytes(self, ref: ArtifactRef) -> bytes: ...
```

The filesystem implementation writes original provider bytes before invoking a parser, uses content checksums, atomically creates a write-once run object, rejects conflicting rewrites, verifies canonical storage references remain inside its root, and returns an opaque storage reference. Raw/private artifact directories are untracked.

### Repository boundary

```python
class Repository(Protocol):
    def create_batch(self, batch: BenchmarkBatch) -> BenchmarkBatch: ...
    def get_batch(self, batch_id: str) -> BenchmarkBatch | None: ...
    def create_planned_run(self, run: PlannedRun) -> PlannedRun: ...
    def get_planned_run(self, run_id: str) -> PlannedRun | None: ...
    def get_planned_run_by_identity(...) -> PlannedRun | None: ...
    def list_planned_runs_for_batch(self, batch_id: str) -> list[PlannedRun]: ...
```

SQLite ships first behind a repository interface. Migrations are tracked in `src/goodenough_bench/migrations/` with immutable version numbers and SHA-256 checksums; database files are not tracked. The current schema covers `schema_migrations`, `benchmark_batches` (including required `batch_purpose`), and `planned_runs`, including canonical JSON for local artifact and routed-provider identity added by `0003_model_route_provenance.sql`. Batch and planned-run creation are idempotent by primary key and stable planned-run identity (`batch_id + model_profile_id + case_id + rep_index`). Planned-run creation rejects `dataset_version`, `dataset_commit`, `runner_commit`, `prompt_version`, or `run_order_seed` values that disagree with the parent batch, and it rejects new rows with incomplete material profile provenance. Pre-0003 rows remain readable as legacy-incomplete planning records. Migration execution uses `sqlite3.complete_statement` parsing rather than naive semicolon splitting. SQL and domain boundaries avoid SQLite-specific behavior where a future PostgreSQL move would otherwise require redesign.

### Planning boundary

```python
class BatchPlanner(Protocol):
    def plan_batch(self, spec: BatchPlanSpec, *, persist_limit: int | None = None) -> BatchPlanResult: ...
```

`RepositoryBatchPlanner` expands explicit `BatchPlanSpec` inputs (a planned batch, unique non-empty case refs, unique non-empty model profiles, and a positive repetition count) into deterministic planned-run slots ordered by repetition round, model input order, and a portable hash-derived case permutation for each seed/round. Full SHA-256 `run_id` values derive from the planned-run identity. Planning is idempotent and resumable through the repository: re-running an identical spec returns existing runs; a test-only `persist_limit` simulates interruption after the first N plan slots; resume creates only missing runs. Conflicting inputs for an existing identity still raise `RepositoryConflictError`. A deterministic fake-provider harness (`FakeProviderBatchPlanner`) supports Phase 2 tests without adapters or paid calls.

### Profile and pricing loader boundary

```python
def load_pricing_snapshots(config_root: Path | None = None) -> PricingSnapshotCatalog: ...
def load_model_profiles(
    config_root: Path | None = None,
    *,
    pricing_catalog: PricingSnapshotCatalog | None = None,
) -> ModelProfileCatalog: ...
```

Tracked, importable JSON under `src/goodenough_bench/config/model_profiles/` and `src/goodenough_bench/config/pricing_snapshots/` loads through strict Pydantic documents (`ModelProfileDocument`, `PricingSnapshot`) with catalog-level duplicate-ID rejection, cross-reference validation between `api_exact` profiles and dated pricing snapshots, and canonical JSON plus SHA-256 catalog checksums. Shared lifecycle boundaries—not loader-only checks—bind source type to surface, provider, host, execution environment, and allowed identity confidence. Local profiles require immutable artifact digest/size/parameter identity and a configured context window. OpenRouter profiles require a pinned upstream provider/model identity with fallbacks disabled, preserving distinct direct and routed aggregates; their pricing snapshots must carry the identical route identity. MVP pricing currency is restricted to `USD`. Repository fixtures are synthetic placeholders only; they are not verified current provider prices or launch profiles. The packaged location follows the imported distribution, including non-default pip installation targets. Loaders read repository-controlled files only and make no provider API calls.

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

The Phase 2 package now exposes these command paths as help-visible placeholders. They return an explicit "not implemented" status and perform no benchmark work. Resumable/read-only behavior and machine-readable operational status remain requirements for their later implementations.

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

Versioned YAML → schema validation → quota validation → two-pass human review check → candidate manifest/checksum → 15-case adapter pilot → versioned defect correction and invalidated-review repetition → final suite manifest/checksum → freeze.

### Collection

Pilot-locked candidate case or frozen stable case → prompt build/hash → adapter request → immutable raw write → SQLite run record. The artifact write precedes parse/scoring, and `batch_purpose` remains explicit in batch provenance.

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

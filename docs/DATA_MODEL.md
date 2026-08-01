> **Status:** Approved conceptual model
> **Authority:** Supporting specification
> **Last reviewed:** 2026-08-01
> **Update when:** Entity definitions or versioning rules change
> **Related:** [ARCHITECTURE.md](ARCHITECTURE.md), [PROVENANCE_AND_REPRODUCIBILITY.md](PROVENANCE_AND_REPRODUCIBILITY.md), [BENCHMARK_SPEC.md](BENCHMARK_SPEC.md)

# Data model

Conceptual entities and relationships. SQLite with tracked migrations is approved for the MVP. The repository interface and portable SQL boundaries preserve a future PostgreSQL migration path without making PostgreSQL a current dependency.

## Entity relationship overview

```text
BenchmarkSuite ──< SuiteVersion ──< BenchmarkCase ──> OutputSchema
                      │
                      └──< BenchmarkBatch ──< Run ──< RawResponse
                                              ├── ParsedResponse
                                              ├── Score
                                              └── (links) PromptVersion
Model ──< ModelVersion ──> ProviderSurface
  └──> HardwareProfile (local) / PricingSnapshot (cloud)
TaskFamily ──< BenchmarkCase
Verdict = f(Scores, Model, TaskFamily, Batch)
EscalationSimulation ──> Batch + Models
HumanReview ──> Run | Case
PublicRelease ──> Batch + EvidenceManifest + PricingSnapshot
CustomBenchmarkProject (private) ──< private cases/runs
```

## Entities

### BenchmarkSuite

| | |
|-|-|
| **Purpose** | Named collection of benchmark content (e.g., "Automation MVP") |
| **Key fields** | `suite_id`, `name`, `description`, `task_families[]` |
| **Relationships** | Has many `SuiteVersion` |
| **Versioning** | Immutable versions via `SuiteVersion` |
| **Public/private** | Public suite for MVP; private suites for custom benchmarks |

### SuiteVersion

| | |
|-|-|
| **Purpose** | Frozen snapshot of cases for a reproducible batch |
| **Key fields** | `version` (semver), `suite_id`, `frozen_at`, `case_count`, `changelog` |
| **Relationships** | Belongs to `BenchmarkSuite`; has many `BenchmarkCase` refs |
| **Versioning** | Semver; patch = case fixes; minor = new cases; major = breaking schema |
| **Public/private** | Public when published |

### TaskFamily

| | |
|-|-|
| **Purpose** | Taxonomy bucket: extraction, classification, normalization |
| **Key fields** | `family_id`, `name`, `default_thresholds` |
| **Relationships** | Groups `BenchmarkCase`; scopes `Verdict` |
| **Versioning** | Stable enum for MVP |
| **Public/private** | Public |

### BenchmarkCase

| | |
|-|-|
| **Purpose** | Single test input + expected output + acceptance rules |
| **Key fields** | `case_id`, `version`, `family_id`, `difficulty`, `input`, `expected`, `acceptance_rules`, `forbidden_inventions`, `tags[]` |
| **Relationships** | Belongs to `SuiteVersion`; references `OutputSchema` |
| **Versioning** | Per-case semver |
| **Public/private** | Public in MVP corpus; private in custom projects |

### GroundTruthRecord

| | |
|-|-|
| **Purpose** | Expected output and reviewer sign-off |
| **Key fields** | `case_id`, `author`, `author_reviewed_at`, `reviewer`, `reviewed_at`, `outcome`, `notes` |
| **Relationships** | 1:1 with case version |
| **Versioning** | Tied to case version |
| **Public/private** | Public for public cases |

### OutputSchema

| | |
|-|-|
| **Purpose** | JSON Schema (subset) defining valid model output |
| **Key fields** | `schema_id`, `json_schema`, `critical_fields[]` |
| **Relationships** | Used by `BenchmarkCase` |
| **Versioning** | `schema_id` + version |
| **Public/private** | Public |

### Model

| | |
|-|-|
| **Purpose** | Logical model identity (e.g., "Qwen 3.5 9B") |
| **Key fields** | `model_id`, `canonical_name`, `family`, `local_or_cloud` |
| **Relationships** | Has many `ModelVersion`; linked from `Run` |
| **Versioning** | Model version when weights/API snapshot change |
| **Public/private** | Public |

### ModelVersion

| | |
|-|-|
| **Purpose** | Specific weights snapshot or API pin |
| **Key fields** | `model_version_id`, `exact_identifier`, `quantization`, `effective_from` |
| **Relationships** | Belongs to `Model` |
| **Versioning** | New row on identifier change |
| **Public/private** | Public |

### Provider

| | |
|-|-|
| **Purpose** | Organization operating API/runtime (OpenAI, Google, Ollama local) |
| **Key fields** | `provider_id`, `name` |
| **Relationships** | Has many `ProviderSurface` |
| **Versioning** | Stable |
| **Public/private** | Public |

### ProviderSurface

| | |
|-|-|
| **Purpose** | How the model is accessed (API, CLI, web, Ollama) |
| **Key fields** | `surface_id`, `source_type`, `provider_id`, `endpoint_type` |
| **Relationships** | Used by `Run`; defines adapter |
| **Versioning** | New surface if access method changes materially |
| **Public/private** | Public |

### HardwareProfile

| | |
|-|-|
| **Purpose** | Machine running local inference |
| **Key fields** | `profile_id`, `hostname`, `cpu`, `ram_gb`, `gpu`, `storage`, `os` |
| **Relationships** | Linked from local `Run` |
| **Versioning** | New profile on hardware change |
| **Public/private** | Public summary; no secrets |

### RuntimeProfile

| | |
|-|-|
| **Purpose** | Software stack (Ollama version, Python, adapter version) |
| **Key fields** | `runtime_id`, `ollama_version`, `runner_version` |
| **Relationships** | Linked from `Run` |
| **Versioning** | Per batch or commit |
| **Public/private** | Public |

### PromptVersion

| | |
|-|-|
| **Purpose** | System + user prompt templates for a suite |
| **Key fields** | `prompt_version_id`, `system_template`, `user_template`, `hash` |
| **Relationships** | Linked from `Run` |
| **Versioning** | Tied to suite version |
| **Public/private** | Public |

### BenchmarkBatch

| | |
|-|-|
| **Purpose** | Group of runs executed under one frozen configuration |
| **Key fields** | `batch_id`, `batch_purpose` (`diagnostic_pilot` or `stable_benchmark`), `suite_version_id` or candidate-manifest reference, `started_at`, `completed_at`, `status`, provenance fields |
| **Relationships** | Has many `Run`; one `PricingSnapshot` ref |
| **Versioning** | Immutable once frozen |
| **Public/private** | Public batches published; pilot batches may stay draft |

### Run

| | |
|-|-|
| **Purpose** | Single model × case × repetition attempt |
| **Key fields** | `run_id`, `batch_id`, `case_id`, `model_version_id`, `surface_id`, `rep_index`, `started_at`, `first_token_at`, `completed_at`, `latency_ms`, `error_type`, `retry_count`, `valid_for_scoring`, `prompt_hash`, token counts, pricing snapshot reference, cost |
| **Relationships** | Has one `RawResponse`, optional `ParsedResponse`, optional `Score` |
| **Versioning** | Immutable |
| **Public/private** | Matches batch |

### RawResponse

| | |
|-|-|
| **Purpose** | Immutable provider output metadata; bytes live in artifact storage |
| **Key fields** | `raw_id`, `run_id`, `checksum`, `byte_length`, `media_type`, `storage_ref`, `redaction_status` |
| **Relationships** | Belongs to `Run` |
| **Versioning** | Never modified |
| **Public/private** | Public with redaction |

### ParsedResponse

| | |
|-|-|
| **Purpose** | Structured parse outcome |
| **Key fields** | `parsed_id`, `run_id`, `json`, `parse_success`, `parse_errors[]` |
| **Relationships** | Belongs to `Run` |
| **Versioning** | Immutable; rescore creates new `Score` not new parse |
| **Public/private** | Public |

### Score

| | |
|-|-|
| **Purpose** | Deterministic evaluation result for a run |
| **Key fields** | `score_id`, `run_id`, `scorer_version`, metric map, `case_pass`, `failure_reasons[]` |
| **Relationships** | Belongs to `Run` |
| **Versioning** | New score on rescore with new `scorer_version` |
| **Public/private** | Public |

### Verdict

| | |
|-|-|
| **Purpose** | Summary label for model × task family |
| **Key fields** | `verdict_id`, `model_id`, `family_id`, `batch_id`, `label`, `pass_rate`, `cost_per_accepted`, `rationale` |
| **Relationships** | Aggregated from `Score` |
| **Versioning** | Per batch publish |
| **Public/private** | Public |

### PricingSnapshot

| | |
|-|-|
| **Purpose** | Dated provider pricing for cost calculations |
| **Key fields** | `snapshot_id`, `effective_date`, `provider`, `model_id`, `input_price`, `output_price`, `currency` (MVP: `USD` only), `source_url`, `inferred` |
| **Relationships** | Referenced by `Batch`, `Run` |
| **Versioning** | Append-only |
| **Public/private** | Public |

### EscalationSimulation

| | |
|-|-|
| **Purpose** | Offline routing economics result |
| **Key fields** | `simulation_id`, `batch_id`, `primary_model_id`, `escalation_model_id`, `triggers[]`, `escalation_rate`, `blended_cost`, `blended_pass_rate` |
| **Relationships** | Uses `Score` aggregates |
| **Versioning** | Per batch + trigger config version |
| **Public/private** | Public |

### HumanReview

| | |
|-|-|
| **Purpose** | Manual adjudication |
| **Key fields** | `review_id`, `target_type`, `target_id`, `reviewer`, `outcome`, `notes` |
| **Relationships** | Links to `Run`, `Case`, or `Batch` |
| **Versioning** | Append-only |
| **Public/private** | Public on public batches when score-affecting |

### PublicRelease

| | |
|-|-|
| **Purpose** | Immutable versioned public JSON export consumed by the static site |
| **Key fields** | `release_id`, `version`, `batch_id`, `schema_version`, `created_at`, `manifest_checksum`, `redaction_status` |
| **Relationships** | References one frozen batch and its evidence/pricing manifests |
| **Versioning** | Append-only; corrections create a new release version |
| **Public/private** | Public after validation |

### CustomBenchmarkProject

| | |
|-|-|
| **Purpose** | Paid private evaluation workspace |
| **Key fields** | `project_id`, `customer_ref`, `status`, `intake_data`, `deletion_policy` |
| **Relationships** | Private cases, batches, reports |
| **Versioning** | Per engagement |
| **Public/private** | **Private** |

## Public/private summary

- **Public:** MVP suite, public batches, scores, methodology, model profiles
- **Private:** Customer intake data, private suites, credentials, draft pilot batches
- **Never store:** API keys in any entity

## Persistence rules

- SQLite database files and raw artifact bytes are untracked operational data.
- Migrations are ordered, immutable after release, and tracked in git.
- Raw response bytes are written to the filesystem before parse/scoring; SQLite stores only their immutable reference and checksum.
- Cases, schemas, prompts, profiles, and pricing snapshots are versioned tracked inputs.
- Redacted public JSON releases are tracked or attached to a versioned release; the static site never reads private SQLite/artifact roots.
- Money uses integer subunit/decimal-safe representations, never binary floating point.

## Related documents

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [PROVENANCE_AND_REPRODUCIBILITY.md](PROVENANCE_AND_REPRODUCIBILITY.md)
- [BENCHMARK_SPEC.md](BENCHMARK_SPEC.md)
- [SCORING_AND_EVALUATION.md](SCORING_AND_EVALUATION.md)

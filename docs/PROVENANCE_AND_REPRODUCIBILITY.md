> **Status:** Approved for MVP implementation
> **Authority:** Source of truth
> **Last reviewed:** 2026-08-01
> **Update when:** Provenance fields or public/private classification rules change
> **Related:** [EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md), [DATA_MODEL.md](DATA_MODEL.md), [BENCHMARK_SPEC.md](BENCHMARK_SPEC.md)

# Provenance and reproducibility

Every published benchmark batch must be auditable. A run missing required provenance is invalid for public quality scoring; enough such runs cause the model/family cell to receive **Insufficient data**.

## Required provenance fields

| Field | Description |
|-------|-------------|
| `dataset_version` | Benchmark suite semver (e.g., `automation-mvp-v0.1.0`) |
| `dataset_commit` | Git commit hash of case files |
| `runner_commit` | Git commit hash of benchmark runner |
| `scorer_version` | Semver of scoring engine |
| `prompt_version` | Suite prompt template version |
| `prompt_hash` | SHA-256 of system + user + schema per run |
| `exact_model_identifier` | Provider-native or Ollama tag |
| `displayed_model_name` | Human-facing name shown in UI |
| `provider` | e.g., `ollama`, `openai`, `google`, `deepseek`, `openrouter` |
| `provider_surface` | e.g., `ollama_local`, `openai_responses_api` |
| `provider_host` | Direct provider or router host actually contacted |
| `collection_method` | Runner adapter/import mechanism and version |
| `model_identity_confidence` | `high` / `medium` / `low` |
| `source_type` | `local_exact`, `api_exact`, `cli_exact`, `web_declared`, `web_opaque`, `manual_import` |
| `runtime` | e.g., `ollama 0.x`, `openai-python 1.x` |
| `quantization` | e.g., `Q4_K_M` (local only; null for cloud) |
| `hardware_profile_id` | Link to hardware profile record |
| `local_model_identity` | Local-only immutable artifact digest, byte size, parameter size, and configured context window |
| `routed_provider_identity` | Routed-API-only pinned upstream provider/model identity, selection policy, and fallback setting |
| `profile_provenance_complete` | Planned-run legacy-migration marker; collected responses are complete-only and do not accept this repeated claim |
| `model_parameters` | Temperature, max tokens, reasoning mode, seed, etc. |
| `run_timestamp` | ISO 8601 UTC start time |
| `pricing_snapshot_id` | Link to dated price record |
| `result_checksum` | Hash over canonical scored output set |
| `human_overrides` | Array of override records (if any) |
| `raw_evidence_ref` | Pointer to immutable raw response artifact |

## Batch-level provenance

Additionally record per batch:

- `batch_id`
- `batch_purpose` (`diagnostic_pilot` or `stable_benchmark`)
- `run_order_seed`
- `invalid_run_count`
- `valid_for_scoring_count`
- `operator` (human or CI)
- `environment` (TheImp hostname, CI runner)

## Raw evidence retention

- Full raw model response stored before parsing
- Parsed JSON stored separately with parse metadata
- Provider request/response IDs where available
- Retain for public batches indefinitely unless policy changes
- Private customer benchmark data — separate storage; default deletion within 30 calendar days after final delivery or earlier withdrawal unless the written engagement sets a different period

Storage: immutable local filesystem artifacts for MVP. Object storage is deferred and requires an architecture decision. See [ARCHITECTURE.md](ARCHITECTURE.md).

## Public vs private

| Data | Public | Private |
|------|--------|---------|
| Public suite case definitions | Yes | — |
| Public batch raw responses | Yes (redacted secrets) | — |
| Public scores and verdicts | Yes | — |
| Methodology and prompts | Yes | — |
| Pricing snapshots | Yes (effective date labeled) | — |
| API keys, auth headers | — | Never store in run records |
| Customer-submitted workflow examples | — | Yes, unless explicit permission |
| AutoGemini automation credentials | — | Yes |
| Internal cost notes | — | Yes |

Redact: API keys, internal URLs, customer PII in public evidence.

## Reproducibility command

```bash
goodenough-bench batch reproduce \
  --database path/to/operational.sqlite \
  --batch batch-2026-001 \
  --verify-checksum
```

Phase 2 reproduction verifies the frozen batch `reproduction_checksum`: canonical JSON over all persisted batch provenance plus complete planned-run identities (including material local-artifact and routed-provider identity). Malformed persisted batch or planned-run data yields a machine-readable `invalid_data` result without claiming a checksum. Migration `0004_reproduction_checksum.sql` reclassifies legacy frozen records as completed because they lack this fingerprint; they require a new verified freeze. Full re-execution, case-file/prompt/scorer checksums, and scored `result_checksum` verification remain later runner/scoring work and still require the same model availability.

## Reproducibility limitations

### Opaque web surfaces

- Unknown system prompt and routing
- Model may change without notice
- Rate limits and throttling affect latency
- Browser automation environment not portable
- **Label:** "Experimental — not reproducible on API surface"

### Cloud provider drift

- Model aliases updated silently
- Pin snapshots where provider supports; record when not possible
- Historical runs remain valid with snapshot ID at time of run

### Local hardware variance

- Same model tag different RAM pressure → latency variance
- Document hardware profile; reproduction on different machine = comparative, not identical

### Pricing

- Historical cost uses snapshot at run time — reproducing cost requires same snapshot ID

## Model identity confidence levels

| Level | Criteria |
|-------|----------|
| `high` | `api_exact` or `local_exact` with verified identifier |
| `medium` | `cli_exact` or `web_declared` with corroborating metadata |
| `low` | `web_opaque`, `manual_import` without API corroboration |

Low confidence results excluded from main leaderboard comparisons.

The boundary enforces `high` for `local_exact` and `api_exact`, `medium` for
`cli_exact` and `web_declared`, and `low` for `web_opaque` and
`manual_import`. OpenRouter `api_exact` profiles require a pinned upstream
provider/model selection with fallbacks disabled; materially different routes
are separate profiles, and the dated pricing snapshot must bind to the same
route. Planning and direct repository writes resolve every non-null pricing
reference against a typed pricing catalog and verify the snapshot provider,
exact model identifier, and routed-provider identity before marking or
persisting complete profile provenance. The repository also revalidates the
complete planned-run boundary before any insert so copied models cannot bypass
lifecycle checks. The collection workflow must construct responses from the
persisted planned run; the response boundary revalidates that plan, copies its
frozen provenance, and resolves API/priced references against the typed catalog.
It does not accept a repeated completeness flag. New planned runs and collected
responses require complete profile provenance. Rows created before the
material-identity schema remain readable as legacy-incomplete planning records
but cannot be newly created or used as collected evidence.

## Human overrides

Each override record:

```yaml
override_id: ...
run_id: ...
reviewer: ...
timestamp: ...
field_changed: ...
original_value: ...
new_value: ...
reason: ...
```

Overrides public on public batches when they affect published scores.

## Related documents

- [EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md)
- [DATA_MODEL.md](DATA_MODEL.md)
- [BENCHMARK_SPEC.md](BENCHMARK_SPEC.md)
- [SCORING_AND_EVALUATION.md](SCORING_AND_EVALUATION.md)

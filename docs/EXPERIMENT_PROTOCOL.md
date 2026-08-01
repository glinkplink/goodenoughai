> **Status:** Approved for MVP implementation
> **Authority:** Source of truth
> **Last reviewed:** 2026-08-01
> **Update when:** Run procedure, retry policy, or import rules change
> **Related:** [BENCHMARK_SPEC.md](BENCHMARK_SPEC.md), [PROVENANCE_AND_REPRODUCIBILITY.md](PROVENANCE_AND_REPRODUCIBILITY.md), [SCORING_AND_EVALUATION.md](SCORING_AND_EVALUATION.md), [ARCHITECTURE.md](ARCHITECTURE.md)

# Experiment protocol

Controlled procedure for benchmark batch execution. **The runner described here does not exist yet** — examples are conceptual.

## Principles

- One fresh request per case — no shared conversation context
- Identical prompts across models except where provider constraints require documented differences
- Provider failures scored separately from model-quality failures
- Raw responses preserved immutably before parsing
- Every pilot or stable batch configuration is frozen before scoring; reruns create new batch IDs
- Diagnostic pilot batches use the reviewed candidate manifest and are never publishable leaderboard evidence; stable batches require the final frozen suite

## Pre-run checklist

- [ ] `batch_purpose` labeled `diagnostic_pilot` or `stable_benchmark`
- [ ] Diagnostic pilot: reviewed candidate manifest/checksum locked and committed; stable benchmark: final suite version frozen and committed
- [ ] All cases reviewed; ground truth signed off
- [ ] Author review and independent reviewer sign-off recorded for every current case version
- [ ] Model profiles updated in [MODEL_LAUNCH_SET.md](MODEL_LAUNCH_SET.md)
- [ ] Pricing snapshot captured with effective date
- [ ] Scorer version tagged
- [ ] Prompt templates hashed and recorded
- [ ] Hardware profile recorded (TheImp or cloud N/A)

## Prompt construction

For each case:

1. Load case definition (input, schema, task family)
2. Apply suite-level system prompt template
3. Inject user prompt with source text and schema
4. Compute `prompt_hash` (SHA-256 of system + user + schema canonical JSON)
5. Store prompt version ID linked to suite version

System and user prompts stored in full — never reconstructed from hash alone.

## Provider parameters

Record per model per batch:

| Parameter | Notes |
|-----------|-------|
| `temperature` | ≈0 where supported |
| `max_output_tokens` | Consistent per task family |
| `reasoning` / thinking mode | Record if exposed; disable where possible for comparability |
| `response_format` | JSON mode if available |
| `seed` | Record if supported |
| `top_p`, penalties | Record; note provider defaults |

Document non-equivalence when providers lack matching controls.

Approved reasoning defaults:

| Surface | Default |
|---------|---------|
| OpenAI | `reasoning.effort: none` when supported |
| Gemini | Minimum documented thinking setting (target: `minimal`) |
| Direct DeepSeek | Non-thinking model/mode |
| Ollama local | Thinking disabled where the model/runtime exposes a control |

Use native strict structured-output or JSON Schema mode when supported. A surface without an equivalent control remains eligible only with the difference recorded in its model profile and every run.

## Normalized adapter response

Every adapter returns the same logical fields, using `null` when a provider does not expose a value:

```text
run_id, case_id, model_profile_id
provider, provider_surface, provider_host
source_type, collection_method, model_identity_confidence
started_at, first_token_at, completed_at, latency_ms
input_tokens, output_tokens
raw_artifact_ref, raw_checksum
error_type, error_message, retry_count
pricing_snapshot_id, estimated_cost
runtime_metadata, hardware_metadata
provider_request_id, prompt_hash
```

Parsing and `scorer_version` belong to downstream parse/score records, not adapter logic. Adapter responses never contain a repaired model answer.

## Repetition count

- **3 repetitions** per case per model (MVP default)
- Each repetition is independent fresh request
- Repetition index stored: `rep_index` 0, 1, 2

## Retry handling

| Event | Policy |
|-------|--------|
| Transient HTTP 429/5xx | Retry up to **3** times with exponential backoff |
| Timeout | Record as `timeout` error; no quality score |
| Auth failure | Fail batch setup; do not partial-publish |
| Malformed provider response | Store raw body; parse failure recorded |

Retries for **provider errors** do not count as benchmark repetitions.

## Timeout handling

| Surface | Approved timeout | Notes |
|---------|------------------|-------|
| Local (TheImp) | **120 seconds scored** | One separate discarded warmup handles cold load |
| Cloud API | **60 seconds** | Provider-specific lower limits may be recorded, not silently raised |

Timeout → `error_type: timeout`; excluded from quality scoring; included in reliability metrics.

## Provider-error classification

| `error_type` | Description | Affects quality score? |
|--------------|-------------|------------------------|
| `none` | Success | Scored |
| `timeout` | Exceeded deadline | No |
| `rate_limit` | 429 after retries exhausted | No |
| `auth` | Invalid key / permission | No |
| `provider_5xx` | Server error | No |
| `invalid_request` | Bad request to provider | No |
| `parse_failure` | Model responded; output unparseable | Yes (integrity) |
| `empty_response` | Zero-length completion | Yes (integrity) |

## Run order and randomization

- Generate one seeded case order per repetition round and record the seed/order
- Run one model at a time to control local memory and load effects
- Execute three separate repetition rounds so the same case is not called three times adjacently
- Record model order and actual run order in batch metadata; rotate the starting model between rounds where operationally practical

## Local warmup policy

- **One warmup request** per local model before batch (discarded, not scored)
- Record cold vs warm latency separately where measurable
- Ollama model load time noted in hardware metadata

## Hardware telemetry (local)

Collect per run where available:

- Peak RAM, average RAM
- CPU utilization
- GPU utilization if present; do not assume TheImp has or lacks a GPU before inspection
- Tokens per second
- Model load time

Commands conceptual — implemented in runner later.

## Cloud telemetry

Collect per run:

- Input/output token counts (or estimate with disclosure if missing)
- Time to first token (if available)
- Total latency (`completed_at - started_at`)
- Estimated cost from pricing snapshot

Missing token counts → flag run `token_count_inferred: true`.

## Raw response preservation

Store immutably:

- Full raw response body/text
- HTTP headers relevant to rate limits (redact auth)
- Provider request ID if returned
- Checksum of raw bytes

Filesystem initially; object storage later ([ARCHITECTURE.md](ARCHITECTURE.md)).

## Invalid-run handling

Invalid for quality scoring:

- Provider errors (above)
- Runs against wrong suite version
- Prompt hash mismatch
- Wrong model ID surface

Mark `valid_for_scoring: false` with reason. Retain in batch for availability metrics.

## Rerun policy

| Trigger | Action |
|---------|--------|
| Case defect discovered | Fix case; new suite patch version; invalidate affected runs; rerun all models on changed cases |
| Scorer bug | Fix scorer; rescore batch; document scorer version bump |
| Provider outage mid-batch | Pause; resume or new batch segment; never fill gaps with different prompt version |
| Model identity correction | New model profile; rerun from scratch for that model |

## Batch freeze policy

Before public publish:

1. All planned runs completed or explicitly marked invalid
2. Batch metadata frozen (commit hashes, pricing snapshot ID)
3. Human review of at least three scored runs per model/family cell, every forbidden or critical invention, every override, and each representative failure selected for publication
4. Result checksum computed over scored outputs

## Human override policy

Human reviewer may:

- Mark ground-truth dispute on a case (blocks publish until resolved)
- Override parse classification on ambiguous model output (logged with reviewer ID and reason)
- Exclude run from public publish with documented reason

Overrides stored in provenance — never silent.

### Run-review sampling

For six models and three families, the base random/stratified review floor is 54 runs (3 × 6 × 3), sampled across pass/fail and repetitions. Critical inventions, overrides, and representative published failures are reviewed in addition to that floor. Review notes and reviewer identity are append-only.

## Manual and AutoGemini import

### Manual import path

- JSONL or structured import via `ManualImportAdapter`
- Required fields: case_id, raw_response, source_type, collection_method, collected_at
- Optional: declared model name, interface description

### AutoGemini import

- Dedicated `AutoGeminiImportAdapter` for queue output JSONL
- Tag `source_type: manual_import` or `web_declared` based on metadata
- Record: interface, declared model, automation version, throttling events

### Why web results remain separate

Consumer web assistants differ from API models in system prompt, routing, tools, quotas, and unknown model identity. Imported web results:

- Appear only in **Free assistant surfaces** or **Experimental** sections
- Never promote to `api_exact` leaderboard without API verification
- Carry `model_identity_confidence: low` unless declared and corroborated

Browser automation is **not** part of the trusted core runner.

## Conceptual CLI examples

**Not implemented yet.**

```bash
# Run benchmark batch
goodenough-bench batch run \
  --suite automation-mvp-v0.1.0 \
  --models qwen3.5:9b,gemma4:12b,llama3.1:8b,gemini-3.5-flash-lite,deepseek-v4-flash,gpt-5.6-luna \
  --repetitions 3 \
  --batch-id batch-2026-001

# Score completed batch
goodenough-bench batch score \
  --batch batch-2026-001 \
  --scorer-version 0.1.0

# Import AutoGemini JSONL
goodenough-bench import \
  --source autogemini \
  --file responses.jsonl \
  --surface web_declared \
  --batch batch-web-exp-001

# Export public evidence
goodenough-bench batch export \
  --batch batch-2026-001 \
  --format json \
  --redact-secrets
```

## Related documents

- [BENCHMARK_SPEC.md](BENCHMARK_SPEC.md)
- [SCORING_AND_EVALUATION.md](SCORING_AND_EVALUATION.md)
- [PROVENANCE_AND_REPRODUCIBILITY.md](PROVENANCE_AND_REPRODUCIBILITY.md)
- [MODEL_LAUNCH_SET.md](MODEL_LAUNCH_SET.md)
- [DATA_MODEL.md](DATA_MODEL.md)

> **Status:** Approved for MVP implementation
> **Authority:** Source of truth
> **Last reviewed:** 2026-07-31
> **Update when:** Metrics, formulas, thresholds, or verdict definitions change
> **Related:** [BENCHMARK_SPEC.md](BENCHMARK_SPEC.md), [EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md), [DATA_MODEL.md](DATA_MODEL.md)

# Scoring and evaluation

Deterministic scoring is **primary and authoritative** for MVP. LLM-as-judge is secondary, disclosed, and never the sole evaluator for central metrics.

## Scoring pipeline order

1. Parse raw response → JSON (or fail)
2. Validate against case output schema
3. Score field-level accuracy vs expected / acceptance rules
4. Compute trustworthiness metrics (inventions, nulls)
5. Aggregate to case-level pass/fail
6. Aggregate to model-task metrics across cases and repetitions
7. Apply verdict label
8. Compute economics from pricing snapshot

Provider errors (`timeout`, `rate_limit`, etc.) → skip quality steps; record in reliability only.

## JSON parsing

```text
parse_success = (the complete response is one valid JSON value allowed by the case schema)
```

- The response must be JSON as required by the case/provider contract; markdown fences or commentary outside the JSON cause parse failure
- Parse failure → `parse_success: false`; case fails integrity gates
- Partial, truncated, extracted, or repaired JSON → parse failure. The original response remains immutable evidence; no repair is scored.

## Schema validity

Validate parsed JSON against case `output_schema` (JSON Schema subset):

```text
schema_valid = jsonschema.validate(parsed, output_schema) succeeds
```

Track:

- `required_field_completion_rate` = present required fields / total required fields
- `unexpected_field_rate` = fields not in schema / total fields returned
- `enum_compliance_rate` = enum fields valid / enum fields total
- `type_correctness_rate` = correctly typed fields / typed fields total

## Field accuracy

### Exact field accuracy

```text
exact_field_accuracy = matching_exact_fields / comparable_fields
```

String match after trim; case-sensitive unless case rules defined per field.

### Normalized field accuracy

Apply normalization before compare:

- Dates → ISO 8601
- Numbers → numeric value (strip currency symbols)
- Strings → lowercase trim for semantic fields when `allow_semantic_variants: true`
- Lists → order-insensitive where schema indicates set comparison

```text
normalized_field_accuracy = matching_normalized_fields / comparable_fields
```

### Classification metrics

For classification/routing family:

```text
classification_accuracy = correct_labels / total_cases

precision = TP / (TP + FP)
recall    = TP / (TP + FN)
F1        = 2 × precision × recall / (precision + recall)
```

Multi-label: per-label micro-average unless case specifies macro.

## Trustworthiness metrics

### Unsupported-field rate

Fields present in output with no support in source text (per case rules):

```text
unsupported_field_rate = unsupported_fields / total_output_fields
```

### Hallucinated-value rate

Values invented beyond unsupported field presence — includes wrong numbers, names, dates:

```text
hallucinated_value_rate = hallucinated_values / total_comparable_values
```

Case `forbidden_inventions` list → automatic fail if any appear.

### Appropriate-null behavior

For missing-information cases:

```text
appropriate_null_rate = correctly_null_or_unknown_fields / fields_missing_in_source
```

False fill (invented value where null required) → critical failure.

### Source preservation

- `source_number_preservation_rate` — numeric values match source
- `source_date_preservation_rate` — dates match or correctly normalize

## Reliability metrics

### Pass rate

```text
pass_rate = passed_scored_runs / total_scored_runs
```

Each repetition is one scored run. A run passes when all applicable case threshold gates are met; provider-error runs are excluded from this denominator and counted in availability instead.

### Consistency across repetitions

For 3 repetitions per case:

```text
consistency_rate = cases_where_all_reps_pass / cases_with_3_valid_reps

# Alternative: label agreement
label_consistency = cases_where_all_reps_same_verdict / cases_with_3_valid_reps
```

Report both where useful.

### Malformed-output rate

```text
malformed_rate = (parse_failures + schema_failures) / total_attempts
```

### Provider vs quality failure rates

```text
provider_error_rate = provider_error_runs / total_runs
quality_failure_rate = quality_failures / valid_provider_runs
```

**Never** score provider timeout as incorrect model answer.

## Pass/fail thresholds

Defaults (may vary by task family — document in suite metadata):

| Gate | Threshold |
|------|-----------|
| JSON valid | Required |
| Schema valid | Required |
| Required-field recall | ≥ 95% |
| Unsupported-field rate | ≤ 1% |
| Critical-field accuracy | 100% |
| Normalized field accuracy | ≥ 95% |

Case-level pass = all gates pass. Case may define stricter `acceptance_rules`.

## Verdict labels

Applied per **model × task family** (not global):

| Label | Criteria (indicative) |
|-------|----------------------|
| **Reliable** | Pass rate ≥90%; consistency ≥85%; unsupported-field rate ≤1% |
| **Usable with validation** | Pass rate 75–89% **and** deterministic validation covers critical failures; also the fallback for ≥90% cells that miss a `Reliable` consistency/unsupported gate but meet the same validation condition |
| **Escalation recommended** | Pass rate 50–74% **and** a predeclared routed simulation materially improves reliability or cost |
| **Not suitable** | Pass rate <50% **or** critical failures cannot be detected safely |
| **Insufficient data** | Fewer than 90% of planned runs are valid for the model/family cell |

Verdict precedence: `Insufficient data` first; then `Not suitable` for unsafe undetectable critical failure; then `Reliable`; then `Usable with validation`; then `Escalation recommended`; otherwise `Not suitable`. “Materially improves” must be predeclared for a release as either ≥5 percentage points final pass-rate gain without higher cost than premium-only, or ≥20% cost reduction without lowering final pass rate. Reliability, cost, and latency are always reported together.

## Economics

### Cost per attempt

```text
attempt_cost = (input_tokens × input_price + output_tokens × output_price) / token_unit
```

Local models report `api_attempt_cost = 0`. Electricity is a separate dated estimate based on measured or declared power and run duration, or `null` when unavailable. Hardware amortization is excluded from MVP cost rankings and must not be represented as zero.

### Cost per accepted result

```text
cost_per_accepted_result = sum(attempt_cost for all reps) / count(accepted_results)
```

`accepted_results` = runs passing all quality gates.

### Effective cost at scale

```text
cost_per_1000_accepted = cost_per_accepted_result × 1000
```

### Routed-workflow cost (simulation)

```text
routed_workflow_cost =
  primary_attempt_cost
  + escalation_rate × escalation_attempt_cost
  + validation_overhead_cost (optional, default 0 for MVP)
```

Where:

```text
escalation_rate = fraction of primary outputs triggering escalation rules
```

### Escalation triggers (simulation)

- Invalid JSON
- Schema failure
- Missing critical field
- Unsupported field detected
- Low classification margin only when the surface exposes comparable class probabilities and the suite predeclares a calibrated threshold; otherwise this trigger is disabled for MVP rather than inferred from model prose
- Model output `needs_review`
- Repetition disagreement
- Deterministic validator failure

Simulate vs premium-only:

```text
premium_only_cost = workload_volume × premium_pass_rate_adjusted_cost
savings = premium_only_cost - routed_workflow_cost
```

Report pass rate, cost, and latency tradeoff — not savings alone.

## Pricing rules

- Prices from **pricing snapshots** with effective date — never hardcoded in scorer logic
- Historical runs retain snapshot reference ID
- Label `price_inferred: true` when token counts or prices estimated
- Missing price → cost metrics `null`, not zero

## Golden test fixtures

Required before scorer implementation:

- Known raw responses → expected score vectors
- Edge cases: empty response, markdown-wrapped JSON, extra fields, null handling, enum violation
- Money calculations tested deterministically

Location: `tests/fixtures/scoring/` (when code exists).

## LLM-as-judge policy

**Not authoritative for MVP central metrics.**

If added later:

- Secondary tier only (e.g., borderline semantic equivalence)
- Disclosed model and prompt version
- Never sole grader for pass/fail
- Separate score dimension — not merged into pass rate

Primary evaluation remains deterministic checks defined above.

## Edge cases

| Scenario | Handling |
|----------|----------|
| Model returns array vs object | Fail unless schema allows |
| Correct answer, wrong enum spelling | Fail enum gate; may pass normalized if variant allowed |
| Extra benign whitespace | Normalize |
| Right structure, all nulls on complete source | Fail required-field recall |
| Provider returns JSON in markdown fence | Parse fail; preserve original response |
| Multi-rep: 2 pass, 1 fail | Case contributes to consistency metric; majority not used for pass rate (each rep scored) |
| Partial provider response (truncated) | Parse fail; record truncation flag; no repaired or partial field scoring |

## Related documents

- [BENCHMARK_SPEC.md](BENCHMARK_SPEC.md)
- [EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md)
- [PROVENANCE_AND_REPRODUCIBILITY.md](PROVENANCE_AND_REPRODUCIBILITY.md)
- [DATA_MODEL.md](DATA_MODEL.md)
- [MVP_SCOPE.md](MVP_SCOPE.md)

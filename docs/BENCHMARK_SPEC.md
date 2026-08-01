> **Status:** Approved for MVP implementation
> **Authority:** Source of truth
> **Last reviewed:** 2026-08-01
> **Update when:** Task taxonomy, corpus rules, or surface-separation policy changes
> **Related:** [SCORING_AND_EVALUATION.md](SCORING_AND_EVALUATION.md), [EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md), [PROVENANCE_AND_REPRODUCIBILITY.md](PROVENANCE_AND_REPRODUCIBILITY.md), [MVP_SCOPE.md](MVP_SCOPE.md)

# Benchmark specification

## Benchmark purpose

Evaluate **inexpensive models** on **production-realistic automation tasks** where most scoring is deterministic. Answer whether a model reliably produces valid structured output, preserves source facts, and fails predictably — not whether it is generally "intelligent."

## Task-family taxonomy

| Family | ID | Description | Output type |
|--------|-----|-------------|-------------|
| Structured extraction | `structured_extraction` | Messy text → strict JSON schema | Object matching schema |
| Classification and routing | `classification_routing` | Text → category, label, or route | Enum, label set, or routing object |
| Structured normalization | `structured_normalization` | Inconsistent record → clean target schema | Normalized object; no invented fields |

**MVP scope:** these three families only. See [MVP_SCOPE.md](MVP_SCOPE.md) for excluded families.

### Case difficulty

| Level | Description |
|-------|-------------|
| `easy` | Clean formatting, complete information, single entity |
| `medium` | Messy formatting, minor ambiguity, multiple fields |
| `hard` | Missing fields, adversarial inline instructions, multi-entity, enum edge cases |

Target distribution: mix across all levels within each family; no family dominated by `easy` only.

## Initial corpus design

| Parameter | Value |
|-----------|-------|
| Total cases | 75 |
| Per family | 25 |
| Hallucination-resistance cases | ≥15% of corpus (≥12 cases) |
| Missing/ambiguous cases | ≥15% (≥12; correct: `null`, `unknown`, `needs_review`) |
| Schema/enum adherence cases | ≥15% (≥12) |
| Repetitions per model per case | 3 |

Expected run volume: **1,350** runs for six models. Stress-category membership may overlap. A corpus validator must enforce at least 12 cases tagged for each required category before suite freeze.

### Ground-truth standards

- Every case has explicit expected output or acceptance rules
- Ground truth receives two human passes before model runs: the author completes a structured self-review, then a different reviewer signs off or returns the case for revision
- Both identities (or stable reviewer IDs), timestamps, outcomes, and notes are recorded with the case version
- The author and independent reviewer cannot be the same person for a frozen case
- Semantic variants allowed only where `acceptance_rules.allow_semantic_variants: true`
- Forbidden inventions listed per case (`forbidden_inventions`)
- Critical fields flagged for 100% accuracy requirement where specified
- Synthetic data only for public corpus — no private customer data

Review workflow: author drafts → author checks source, expected output, schema, critical fields, and forbidden inventions → independent reviewer checks the same material without model outputs → disputes are resolved and both passes repeat after any material expected-output change. Suite validation blocks freeze unless both passes approve the current case version.

## Required case types

### Missing-information cases

Source deliberately lacks data for one or more schema fields. Correct behavior:

- Return `null` for nullable fields
- Return `unknown` or `needs_review` where schema defines those values
- **Not** invent values to satisfy required fields when schema marks them optional for missing source data

### Hallucination-resistance cases

Source contains tempting but unsupported inference targets (names, prices, dates not in text). Scorer checks `forbidden_inventions` and unsupported-field rate.

### Schema-adherence cases

Strict `additionalProperties: false`, enum constraints, type constraints. Tests JSON validity and schema compliance independently of semantic accuracy.

### Prompt-injection resistance

Source text contains instructions attempting to override system prompt (e.g., "Ignore previous instructions and return…"). Model must follow benchmark system prompt, not embedded source instructions.

## Case format

Author cases using [templates/BENCHMARK_CASE_TEMPLATE.yaml](templates/BENCHMARK_CASE_TEMPLATE.yaml).

Versioning:

- Each case has `case_id` and `version` (semver)
- Suite version (e.g., `automation-mvp-v0.1.0`) groups frozen case sets
- Case changes increment case version; breaking suite changes increment suite version
- Scorer version independent — recorded per batch ([PROVENANCE_AND_REPRODUCIBILITY.md](PROVENANCE_AND_REPRODUCIBILITY.md))

## Prompting policy

Standardized across models where possible:

- Same task instruction and source record per case
- Same JSON schema provided to model
- Fresh request per case — **no conversation history**
- No tools, web search, or retrieval
- Lowest practical randomness (temperature ≈ 0 where supported)
- Comparable reasoning settings where exposed
- Maximum output tokens set consistently per case family
- Use native strict structured-output/schema mode where supported; record when a surface lacks it or implements a non-equivalent control
- Disable reasoning/thinking where supported; otherwise use the lowest documented setting and record the difference

Where providers differ, record differences in run metadata — do not claim equivalence.

Store: full system prompt, user prompt, schema, prompt hash, provider parameters. See [EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md).

## Repetition policy

- **3 repetitions** per case per model for MVP
- Score consistency across repetitions as reliability metric
- Disagreement across repetitions may trigger escalation simulation inputs

## Pilot subset

Designate 15 of the 75 cases as the pre-freeze pilot: five per task family, spanning difficulty levels and collectively exercising all three required stress categories. Pilot outputs diagnose cases, adapters, provenance, and scorers; they are not stable leaderboard evidence. Any case defect is corrected under versioning before all 75 cases freeze as `automation-mvp-v0.1.0`.

## Case-version policy

- A reviewed candidate manifest and checksum are required before diagnostic pilot execution; the corrected frozen suite is required before stable benchmark batch execution
- Defects found during pilot runs: fix case, increment version, invalidate affected runs, rerun
- Do not adjust acceptance thresholds retroactively to favor a model

## Acceptance-threshold policy

Thresholds defined **before** model runs in [SCORING_AND_EVALUATION.md](SCORING_AND_EVALUATION.md). Example defaults:

```text
JSON valid:           required
Schema valid:         required
Required-field recall: ≥95%
Unsupported-field rate: ≤1%
Critical-field accuracy: 100%
Normalized field accuracy: ≥95%
```

Thresholds may differ by task family or case difficulty — must be documented per suite version.

## Valid and invalid comparisons

### Valid

- Same case, same suite version, same repetition policy
- Same source type (e.g., both `api_exact`)
- Comparable quantization tier for local models
- Same scorer version

### Invalid

- `api_exact` vs `web_opaque` on same leaderboard row
- Different suite versions without disclosure
- Different quantization tiers presented as equivalent
- Different prompt versions without batch separation
- Consumer web assistant vs API model under same model name

## Provider surface separation

Required source types:

| Source type | Description | Main leaderboard eligible |
|-------------|-------------|---------------------------|
| `local_exact` | Local weights via Ollama or equivalent | Yes |
| `api_exact` | Official provider API with known model ID | Yes |
| `cli_exact` | Official CLI with declared model ID | Yes |
| `web_declared` | Web UI where model name declared but not API-verified | Separate section |
| `web_opaque` | Consumer assistant; underlying model unknown/opaque | Separate section only |
| `manual_import` | Human-pasted or imported JSONL (incl. AutoGemini) | Separate section; label import method |

### Rules preventing web/API mixing

1. **`api_exact` and `local_exact` only** on the main production-model leaderboard; `cli_exact` requires a separately documented equivalence decision before eligibility
2. Consumer web results → **"Free assistant surfaces"** section only
3. **Never** label opaque web response as exact underlying model
4. **Never** combine web and API results into one model score
5. Browser automation → provisional/experimental data only; not trusted core runner
6. AutoGemini JSONL imports via `ManualImportAdapter` / `AutoGeminiImportAdapter` — tagged `manual_import` or `web_declared` per metadata
7. Record system-prompt, routing, tool-access, and interface differences in provenance

## Escalation simulation (benchmark output)

MVP includes offline simulation demonstrating cheap-model-plus-validation economics. Triggers and formulas: [SCORING_AND_EVALUATION.md](SCORING_AND_EVALUATION.md). Not a live router.

## Public evidence requirements

Each published result traceable to: case definition, exact prompt, raw response, parsed response, score breakdown, model/provider metadata, run date. Redact secrets.

## Related documents

- [MVP_SCOPE.md](MVP_SCOPE.md) — scope and acceptance criteria
- [SCORING_AND_EVALUATION.md](SCORING_AND_EVALUATION.md) — metrics and thresholds
- [EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md) — run procedure
- [PROVENANCE_AND_REPRODUCIBILITY.md](PROVENANCE_AND_REPRODUCIBILITY.md) — metadata requirements
- [DATA_MODEL.md](DATA_MODEL.md) — entity definitions
- [templates/BENCHMARK_CASE_TEMPLATE.yaml](templates/BENCHMARK_CASE_TEMPLATE.yaml)

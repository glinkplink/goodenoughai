# Experiment report template

Post-batch summary for internal review and optional public methodology appendix.
Replace all `{{placeholders}}`.

---

## Report metadata

| Field | Value |
|-------|-------|
| Report ID | `{{report-id}}` |
| Batch ID | `{{batch-id}}` |
| Suite version | `{{suite-version}}` |
| Report date | {{YYYY-MM-DD}} |
| Author | {{author}} |
| Status | draft \| reviewed \| published |

## Objective

{{One paragraph: what this batch was meant to validate or establish.}}

## Models tested

| Model | Surface | Source type | Identity confidence |
|-------|---------|-------------|---------------------|
| {{model}} | {{surface}} | {{local_exact/api_exact/...}} | {{high/medium/low}} |

## Provider surfaces and hardware

| Component | Detail |
|-----------|--------|
| Local hardware profile | {{profile-id}} — {{UNVERIFIED until inspected}} |
| Cloud providers | {{list}} |
| Runner commit | `{{git-sha}}` |
| Scorer version | `{{semver}}` |

## Parameters

| Parameter | Value |
|-----------|-------|
| Repetitions per case | {{3}} |
| Prompt version | `{{prompt-version-id}}` |
| Temperature / reasoning | {{per-model table or summary}} |
| Timeout policy | {{values}} |

## Price snapshot

| Snapshot ID | Effective date | Notes |
|-------------|----------------|-------|
| `{{snapshot-id}}` | {{date}} | {{inferred? provider URLs}} |

## Run counts

| Metric | Count |
|--------|-------|
| Planned runs | {{N}} |
| Completed runs | {{N}} |
| Valid for scoring | {{N}} |
| Invalid runs | {{N}} |
| Provider errors | {{N}} |
| Parse failures | {{N}} |

## Results summary

### By task family

| Model | Family | Pass rate | Schema valid | Unsupported-field rate | Cost/accepted | Verdict |
|-------|--------|-----------|--------------|------------------------|---------------|---------|
| {{model}} | {{family}} | {{%}} | {{%}} | {{%}} | {{$}} | {{label}} |

### Top findings

1. {{Finding with evidence link}}
2. {{Finding}}
3. {{Finding}}

## Failure analysis

### Representative failures

| Case ID | Model | Failure type | Summary | Evidence link |
|---------|-------|--------------|---------|---------------|
| {{case}} | {{model}} | {{hallucination/schema/parse}} | {{brief}} | {{run_id}} |

### Systematic failure patterns

- {{Pattern description}}

## Escalation analysis

| Primary model | Escalation model | Escalation rate | Blended pass rate | Blended cost | Premium-only cost | Savings |
|---------------|------------------|-----------------|-------------------|--------------|-------------------|---------|
| {{primary}} | {{escalation}} | {{%}} | {{%}} | {{$}} | {{$}} | {{$}} |

Triggers used: {{list escalation triggers from SCORING_AND_EVALUATION.md}}

## Human review

| Reviewer | Scope | Outcome | Notes |
|----------|-------|---------|-------|
| {{name}} | {{spot-check / full}} | {{approved / overrides}} | {{notes}} |

Overrides applied: {{count}} — see provenance log.

## Limitations

- {{e.g., Gemma 4 12B near RAM limit on TheImp}}
- {{e.g., cloud model ID not snapshot-pinned}}
- {{e.g., web imports excluded from this batch}}

## Reproducibility information

| Field | Value |
|-------|-------|
| Dataset commit | `{{sha}}` |
| Result checksum | `{{checksum}}` |
| Reproduce command | `goodenough-bench batch reproduce --batch {{batch-id}}` *(not implemented yet)* |

## Recommendation

{{Plain-language recommendation for automation builders on this task family — no unsupported claims.}}

## Related documents

- [BENCHMARK_SPEC.md](../BENCHMARK_SPEC.md)
- [SCORING_AND_EVALUATION.md](../SCORING_AND_EVALUATION.md)
- [PROVENANCE_AND_REPRODUCIBILITY.md](../PROVENANCE_AND_REPRODUCIBILITY.md)
- [EXPERIMENT_PROTOCOL.md](../EXPERIMENT_PROTOCOL.md)

# Model profile template

One profile per **model version × surface × quantization** combination.
Copy and fill for [../MODEL_LAUNCH_SET.md](../MODEL_LAUNCH_SET.md) entries.

---

## Identity

| Field | Value |
|-------|-------|
| Profile ID | `{{model-slug-surface-quant}}` |
| Canonical name | {{e.g., Qwen 3.5 9B}} |
| Display name | {{Public UI name}} |
| Model family | {{e.g., Qwen 3.5}} |
| Exact identifier | `{{e.g., qwen3.5:9b}}` — **UNVERIFIED until confirmed** |
| Provider | {{ollama / openai / google / deepseek / openrouter}} |
| Provider surface | {{e.g., ollama_local, openai_responses_api}} |
| Source type | {{local_exact / api_exact / cli_exact / web_declared / web_opaque / manual_import}} |
| Identity confidence | {{high / medium / low}} |
| Local or cloud | {{local / cloud}} |

## Versioning and licensing

| Field | Value |
|-------|-------|
| Model version / snapshot | {{pin or UNVERIFIED}} |
| Weights license | {{e.g., Apache 2.0 — verify}} |
| API terms reference | {{URL if cloud}} |
| Effective from | {{date first tested}} |
| Superseded by | {{profile-id or none}} |

## Runtime configuration

| Field | Value |
|-------|-------|
| Quantization | {{Q4_K_M / n/a for cloud}} |
| Context window setting | {{tokens}} |
| Default parameters | temperature={{0}}, max_tokens={{}} |
| Runtime | {{Ollama version / API version — UNVERIFIED}} |
| Hardware profile | {{link to HardwareProfile or UNVERIFIED}} |

## Economics (snapshot reference only — never hardcode as fact)

| Field | Value |
|-------|-------|
| Pricing snapshot ID | `{{snapshot-id}}` |
| Input price | {{value}} per {{unit}} @ {{date}} |
| Output price | {{value}} per {{unit}} @ {{date}} |
| Price inferred | {{true/false}} |
| Local cost model | API cost $0; dated electricity estimate or `null` |

## Supported controls

- [ ] JSON / structured output mode
- [ ] Temperature control
- [ ] Max output tokens
- [ ] Seed
- [ ] Reasoning/thinking mode (record if disabled for benchmark)
- [ ] Tool use (must be **off** for benchmark)

Document provider limitations vs other models.

## Benchmark history

| Batch ID | Suite version | Date | Verdict summary | Notes |
|----------|---------------|------|-----------------|-------|
| {{batch}} | {{suite}} | {{date}} | {{label per family}} | {{substitution?}} |

## Expected benchmark role

{{Primary local anchor / cloud cost baseline / escalation target / experimental web only}}

## Known limitations

- {{e.g., slow on CPU-only TheImp}}
- {{e.g., occasional JSON fence wrapping}}
- {{e.g., rate limits at batch size N}}

## Verification status

| Check | Status |
|-------|--------|
| Identifier confirmed | ☐ UNVERIFIED |
| Smoke test passed | ☐ UNVERIFIED |
| Quantization confirmed | ☐ UNVERIFIED / n/a |
| Pricing snapshot captured | ☐ UNVERIFIED |
| Hardware viability | ☐ UNVERIFIED |

## Possible substitute

If this profile fails verification: {{fallback model profile ID}}

## Related documents

- [MODEL_LAUNCH_SET.md](../MODEL_LAUNCH_SET.md)
- [PROVENANCE_AND_REPRODUCIBILITY.md](../PROVENANCE_AND_REPRODUCIBILITY.md)
- [EXPERIMENT_PROTOCOL.md](../EXPERIMENT_PROTOCOL.md)

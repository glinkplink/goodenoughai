> **Status:** Approved candidate set; three local profiles frozen on TheImp/Ollama 0.32.5
> **Authority:** Living model-profile plan  
> **Last reviewed:** 2026-07-31  
> **Update when:** Catalog identity, access, pricing, hardware viability, substitution, or expansion changes  
> **Related:** [MVP_MASTER_PLAN.md](MVP_MASTER_PLAN.md), [BENCHMARK_SPEC.md](BENCHMARK_SPEC.md), [EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md), [PROVENANCE_AND_REPRODUCIBILITY.md](PROVENANCE_AND_REPRODUCIBILITY.md)

# Model launch set

The six-surface target is approved. Official catalog pages confirm the candidate identifiers listed below as of 2026-07-31. Catalog confirmation does **not** establish account access, local installation, model digest, pricing snapshot, or performance on TheImp.

## Launch target

| # | Model | Primary surface | Catalog identity | Access / viability |
|--:|-------|-----------------|------------------|--------------------|
| 1 | Qwen 3.5 9B | Ollama `local_exact` | Confirmed | **Viable on TheImp** on Ollama 0.32.5; final fixed probes passed 3/3 |
| 2 | Gemma 4 12B | Ollama `local_exact` | Confirmed | **Viable on TheImp** on Ollama 0.32.5; exact tag/digest verified; final fixed probes passed 3/3 |
| 3 | Llama 3.1 8B | Ollama `local_exact` | Confirmed | **Viable on TheImp** on Ollama 0.32.5; final fixed probes passed 3/3 |
| 4 | Gemini 3.5 Flash-Lite | Google API `api_exact` | Confirmed | Credentials/pricing unverified |
| 5 | DeepSeek V4 Flash | Direct DeepSeek API `api_exact` | Confirmed | Credentials/pricing unverified |
| 6 | GPT-5.6 Luna | OpenAI Responses API `api_exact` | Confirmed | Credentials/pricing unverified |

OpenRouter support is required as a separate adapter/fallback profile. It is not one of the six primary launch profiles unless a direct provider is unavailable and a substitution decision is approved.

## Local candidates

### Qwen 3.5 9B

| Field | Value |
|-------|-------|
| Exact candidate tag | [`qwen3.5:9b`](https://ollama.com/library/qwen3.5/tags) |
| Catalog observation | 9B tag and `qwen3.5:9b-q4_K_M` listed; catalog file size 6.6 GB |
| Role | Primary local structured-output candidate |
| Why included | Current inexpensive local family at a plausible ordinary-hardware size |
| Required Phase 1 evidence | Pull/list output, digest, quantization, context, runtime, memory, throughput, latency, headroom |
| Status | Frozen local profile on Ollama 0.32.5; all hardware gates passed and final fixed probes parsed/matched the supplied schemas 3/3 |

### Gemma 4 12B

| Field | Value |
|-------|-------|
| Exact candidate tag | [`gemma4:12b`](https://ollama.com/library/gemma4%3A12b) |
| Catalog observation | 11.9B, Q4_K_M, 7.6 GB listed |
| Role | Larger local comparison and model-family diversity |
| Why included | Tests whether a larger current local profile remains practical and worthwhile |
| Required Phase 1 evidence | Pull/list output, digest, context, runtime, memory, throughput, latency, headroom |
| Status | Frozen local profile on Ollama 0.32.5; exact digest verified, all hardware gates passed, and final fixed probes parsed/matched the supplied schemas 3/3 |

### Llama 3.1 8B

| Field | Value |
|-------|-------|
| Exact candidate tag | [`llama3.1:8b`](https://ollama.com/library/llama3.1%3A8b) |
| Catalog observation | 8.03B, Q4_K_M, 4.9 GB listed |
| Role | Widely recognized local baseline |
| Why included | Common deployment reference for automation builders |
| Required Phase 1 evidence | Installed/pull status, digest, context, runtime, memory, throughput, latency, headroom |
| Status | Frozen local profile on Ollama 0.32.5; all hardware gates passed and final fixed probes parsed/matched the supplied schemas 3/3 |

## Cloud candidates

### Gemini 3.5 Flash-Lite

| Field | Value |
|-------|-------|
| Exact candidate ID | [`gemini-3.5-flash-lite`](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite) |
| Primary surface | Google Gemini API (`api_exact`) |
| Catalog observation | Stable model code listed; structured outputs and thinking controls listed |
| Role | Low-cost/high-throughput Google profile |
| Required cloud-adapter evidence | Credential access, returned identity, rate limits, exact structured-output controls, dated price; explicitly deferred from local-only Phase 1 |
| Status | Catalog-confirmed; account access unverified |

An official CLI run, if collected, is a distinct `cli_exact` profile unless equivalence to the API profile is demonstrated and recorded.

### DeepSeek V4 Flash

| Field | Value |
|-------|-------|
| Exact candidate ID | [`deepseek-v4-flash`](https://api-docs.deepseek.com/api/list-models) |
| Primary surface | Direct DeepSeek API (`api_exact`) |
| Catalog observation | Direct API model-list example includes `deepseek-v4-flash` |
| Role | Primary cost-efficiency cloud comparison |
| Required cloud-adapter evidence | Credential access, live `/models` response, response controls, rate limits, dated price; explicitly deferred from local-only Phase 1 |
| Status | Catalog-confirmed; account access unverified |

OpenRouter identifiers and routing are separately verified. An OpenRouter route uses a distinct model profile containing OpenRouter as provider host/surface, route/provider selection metadata, and its own pricing snapshot. It never merges with the direct DeepSeek aggregate.

### GPT-5.6 Luna

| Field | Value |
|-------|-------|
| Exact candidate ID | [`gpt-5.6-luna`](https://developers.openai.com/api/docs/models/gpt-5.6-luna) |
| Primary surface | OpenAI Responses API (`api_exact`) |
| Catalog observation | Model, Responses support, structured outputs, reasoning settings, and snapshots section listed |
| Role | Cost-sensitive OpenAI ecosystem baseline |
| Required cloud-adapter evidence | Credential access, permitted snapshot/alias, returned identity, rate limits, dated price; explicitly deferred from local-only Phase 1 |
| Status | Catalog-confirmed; account access unverified |

## Quantization and local viability policy

DEC-0006 approves Q4_K_M as the default comparison tier. A separately documented equivalent is allowed only when Q4_K_M is unavailable; it creates a distinct model profile and must not be presented as identical quantization.

Each local profile must record:

- Exact tag, digest, file size, parameter size, and quantization
- Ollama/runtime version and context setting
- TheImp hardware profile ID
- Peak memory and minimum observed headroom
- Warm throughput and medium-case latency sample
- Thinking/reasoning control and structured-output behavior

### Viability gate

A local candidate is viable on TheImp only if all are true:

1. Q4_K_M or approved/documented equivalent
2. No out-of-memory failure
3. At least 1 GiB memory headroom during the probe
4. Median warm throughput ≥2 output tokens/second
5. Median medium-case latency ≤120 seconds

One warmup request is discarded before measurement. The probe uses the Phase 3 medium pilot cases once available; before then, a fixed representative structured-output smoke prompt is used and clearly labeled preliminary.

Failing this gate produces **Impractical on this hardware**, not **Not suitable**. Quality verdicts require scored benchmark runs.

## TheImp Phase 1 final observation

Historical Ollama 0.17.4 evidence remains under [`evidence/phase1-theimp-2026-07-31/`](../evidence/phase1-theimp-2026-07-31/). The final frozen runtime/profile evidence is under [`evidence/phase1-theimp-2026-07-31-ollama-0.32.5/`](../evidence/phase1-theimp-2026-07-31-ollama-0.32.5/). These are preliminary hardware-validation probes, not benchmark scores.

| Item | Direct observation |
|------|--------------------|
| Host / OS | `TheImp`; Linux Mint 22.3; kernel `6.17.0-35-generic` |
| CPU | AMD Ryzen 5 7600X; 6 physical cores / 12 logical CPUs |
| RAM / swap | 30 GiB RAM; 2.0 GiB swap, essentially exhausted during initial inspection |
| GPU | NVIDIA GeForce RTX 3060 detected by PCI/proc and used by Ollama CUDA; Ollama reported 12.0 GiB total VRAM |
| Storage | 468 GiB ext4 root filesystem; 108 GiB free after the verified Gemma pull |
| Ollama | 0.32.5 client/daemon active and enabled; official archive checksum verified; model directory and systemd unit/drop-in preserved |
| Other runtimes | Python 3.12.3; Node 22.23.2; Docker 29.7.1; Git 2.43.0 |

### Fixed preliminary probe results

All measured requests used a fresh single-turn prompt, no tools/retrieval/web/history, `temperature: 0`, `seed: 42`, `num_ctx: 4096`, JSON Schema through Ollama `format`, `think: false`, and a 120-second measured timeout. Each installed candidate received one separate discarded warmup.

| Candidate | Exact digest | Parameters / disk | Quantization | Loaded memory / processor | Min system memory headroom | Warm output tok/s (three probes) | Median wall latency | Structured-output observation | Classification |
|-----------|--------------|-------------------|--------------|---------------------------|----------------------------|----------------------------------|---------------------|-------------------------------|----------------|
| `qwen3.5:9b` | `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7` | 9.7B / 6,594,474,711 bytes | Q4_K_M | `ollama ps`: 5.6 GB, 100% GPU, 4,096 context | 21,796,564,992 bytes | 49.73 | **1.019 s** | Valid JSON and exact schema 3/3; thinking disabled | **Viable on TheImp** |
| `gemma4:12b` | `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c` | 11.9B / 7,556,508,396 bytes | Q4_K_M | `ollama ps`: 8.1 GB, 100% GPU, 4,096 context | 23,205,302,272 bytes | 36.53 | **1.400 s** | Valid JSON and exact schema 3/3; thinking disabled | **Viable on TheImp** |
| `llama3.1:8b` | `46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e` | 8.0B / 4,920,753,328 bytes | Q4_K_M | `ollama ps`: 5.3 GB, 100% GPU, 4,096 context | 23,115,485,184 bytes | 61.42 | **0.618 s** | Valid JSON and exact schema 3/3; no thinking capability exposed | **Viable on TheImp** |

All three candidates loaded without OOM, exceeded 1 GiB system-memory headroom, exceeded 2 output tokens/second, and remained below 120 seconds median latency. Qwen and Gemma expose 262,144-token native context; Llama exposes 131,072; all requested/loaded contexts were 4,096. Memory headroom is sampled Linux `MemAvailable`; loaded allocation is direct `ollama ps` evidence.

The original `^\d{4}-\d{2}-\d{2}$` date pattern exposed an Ollama 0.32.5 grammar-conversion error before any model executed. The final pass changed only that pattern to the semantics-equivalent `^[0-9]{4}-[0-9]{2}-[0-9]{2}$`; all nine requests then passed parsing and exact-schema checks. Both passes remain evidence. This runtime limitation must be contract-tested in the Phase 2 Ollama adapter and is not a model-quality verdict.

Independent NVML telemetry remains unavailable: loaded kernel module 595.71.05 is stale while the installed module, DKMS record, and userspace library are 595.84. A reboot should reconcile them; no NVIDIA package or reboot action was performed. This follow-up does not invalidate the observed model identities or hardware gates.

## Historical hardware observation boundary

The accessible host inspected on 2026-07-31 is `X1-Carbon`, not TheImp:

| Item | Observed |
|------|----------|
| CPU | Intel Core i7-10510U; 4 physical cores / 8 threads |
| RAM / swap | 15 GiB RAM / 2 GiB swap |
| GPU | Integrated Intel UHD; `nvidia-smi` unavailable |
| Workspace free storage | About 14 GiB |
| Ollama | Client 0.13.5; daemon/list inaccessible from the sandbox |
| Other runtimes | Python 3.10.12; Node 22.14.0; Docker 29.7.1 |

The supplied planning record reports that only `llama3.1:8b` was installed on this host during an earlier inspection; this session could not re-query the daemon. The listed local catalog files total about 19.1 GB before overhead, so the current free workspace storage cannot hold all three together. These facts do not establish anything about TheImp.

## Substitution policy

Substitutions are never silent. A replacement needs:

- Failed gate and evidence for the original candidate
- Approved decision-log entry
- New exact model/provider profile
- Updated run-count/budget projection
- Consistent reruns across all 75 cases for that profile

Candidate fallbacks:

| Original | First candidate fallback | Condition |
|----------|--------------------------|-----------|
| Qwen 3.5 9B | Smaller current Qwen profile; Qwen 3 14B only if separately viable | Tag/access or gate failure |
| Gemma 4 12B | Gemma 3 4B or current smaller Gemma profile | OOM, headroom, throughput, or latency failure |
| Llama 3.1 8B | Llama 3.2 3B or current smaller Llama profile | Gate failure |
| Gemini direct | Current comparable Flash-Lite API profile | Access/deprecation |
| DeepSeek direct | OpenRouter route as distinct provider surface | Direct access unavailable; route identity/pricing verified |
| OpenAI Luna | Current documented lightweight OpenAI profile | Access/deprecation/budget failure |

Actual fallback identity must be verified at substitution time; these names are not pre-approved silent replacements.

## Expansion candidates

Deferred until after MVP validation:

- Claude Haiku 4.5 (first cloud expansion candidate)
- Additional current Qwen/Gemma/Llama sizes
- GPT-5.4 nano comparison
- Mistral and GLM lightweight models
- Stronger cloud escalation baselines

## Opaque and imported surfaces

Consumer web assistants and manual/AutoGemini imports remain separate from the six exact launch profiles.

| Source | Type | Publication |
|--------|------|-------------|
| Free Gemini web assistant | `web_declared` / `web_opaque` | Separate experimental section |
| ChatGPT free web | `web_opaque` | Separate experimental section |
| Claude free web | `web_opaque` | Separate experimental section |
| Human/AutoGemini JSONL | `manual_import` | Separate import section with collection metadata |

Browser automation is not part of the trusted core runner.

## Phase 1 local checklist

- [x] Inspect TheImp and assign hardware profile ID `theimp-2026-07-31`
- [x] Capture Ollama version, model list, installed digests/quantizations, and free storage
- [x] Preserve the historical 0.17.4 pull failure and probe evidence
- [x] Upgrade Ollama to 0.32.5 while preserving models and systemd configuration
- [x] Pull/probe all three exact candidates one at a time on the same runtime
- [x] Test all candidates against local viability gates
- [x] Confirm and freeze the three exact local profiles; no substitution required

Cloud credentials, live identity, pricing snapshots, and spending approval are deferred until cloud adapter work begins. None blocks Phase 1 or local batches.

## Related documents

- [MVP_MASTER_PLAN.md](MVP_MASTER_PLAN.md)
- [BENCHMARK_SPEC.md](BENCHMARK_SPEC.md)
- [EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md)
- [PROVENANCE_AND_REPRODUCIBILITY.md](PROVENANCE_AND_REPRODUCIBILITY.md)
- [PROJECT_STATE.md](PROJECT_STATE.md)
- [DECISION_LOG.md](DECISION_LOG.md)

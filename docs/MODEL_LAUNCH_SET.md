> **Status:** Approved candidate set; Phase 1 partially verified on TheImp, Gemma blocked by runtime compatibility
> **Authority:** Living model-profile plan  
> **Last reviewed:** 2026-07-31  
> **Update when:** Catalog identity, access, pricing, hardware viability, substitution, or expansion changes  
> **Related:** [MVP_MASTER_PLAN.md](MVP_MASTER_PLAN.md), [BENCHMARK_SPEC.md](BENCHMARK_SPEC.md), [EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md), [PROVENANCE_AND_REPRODUCIBILITY.md](PROVENANCE_AND_REPRODUCIBILITY.md)

# Model launch set

The six-surface target is approved. Official catalog pages confirm the candidate identifiers listed below as of 2026-07-31. Catalog confirmation does **not** establish account access, local installation, model digest, pricing snapshot, or performance on TheImp.

## Launch target

| # | Model | Primary surface | Catalog identity | Access / viability |
|--:|-------|-----------------|------------------|--------------------|
| 1 | Qwen 3.5 9B | Ollama `local_exact` | Confirmed | **Viable on TheImp** at the hardware gate; structured-schema limitation observed |
| 2 | Gemma 4 12B | Ollama `local_exact` | Confirmed | **Unavailable or unverified**; Ollama 0.17.4 rejected the pull as requiring a newer runtime |
| 3 | Llama 3.1 8B | Ollama `local_exact` | Confirmed | **Viable on TheImp** at the hardware gate; one structured-schema probe crashed the Ollama runner |
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
| Status | Hardware-gate viable on TheImp on 2026-07-31; strict JSON parsed 3/3, but only 1/3 outputs honored the exact supplied schema |

### Gemma 4 12B

| Field | Value |
|-------|-------|
| Exact candidate tag | [`gemma4:12b`](https://ollama.com/library/gemma4%3A12b) |
| Catalog observation | 11.9B, Q4_K_M, 7.6 GB listed |
| Role | Larger local comparison and model-family diversity |
| Why included | Tests whether a larger current local profile remains practical and worthwhile |
| Required Phase 1 evidence | Pull/list output, digest, context, runtime, memory, throughput, latency, headroom |
| Status | Unavailable/unverified on TheImp: `ollama pull gemma4:12b` returned HTTP 412 because Ollama 0.17.4 is too old for the manifest |

### Llama 3.1 8B

| Field | Value |
|-------|-------|
| Exact candidate tag | [`llama3.1:8b`](https://ollama.com/library/llama3.1%3A8b) |
| Catalog observation | 8.03B, Q4_K_M, 4.9 GB listed |
| Role | Widely recognized local baseline |
| Why included | Common deployment reference for automation builders |
| Required Phase 1 evidence | Installed/pull status, digest, context, runtime, memory, throughput, latency, headroom |
| Status | Hardware-gate viable on TheImp on 2026-07-31; 2/3 structured probes succeeded and the normalization grammar caused a local runner SIGSEGV/HTTP 500 |

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

## TheImp Phase 1 observation

Hardware profile `theimp-2026-07-31` and all probe outputs are preserved under [`evidence/phase1-theimp-2026-07-31/`](../evidence/phase1-theimp-2026-07-31/). These are preliminary hardware-validation probes, not benchmark scores.

| Item | Direct observation |
|------|--------------------|
| Host / OS | `TheImp`; Linux Mint 22.3; kernel `6.17.0-35-generic` |
| CPU | AMD Ryzen 5 7600X; 6 physical cores / 12 logical CPUs |
| RAM / swap | 30 GiB RAM; 2.0 GiB swap, essentially exhausted during initial inspection |
| GPU | NVIDIA GeForce RTX 3060 detected by PCI/proc and used by Ollama CUDA; Ollama reported 12.0 GiB total VRAM |
| Storage | 468 GiB ext4 root filesystem; 120 GiB free before the attempted Gemma pull |
| Ollama | 0.17.4 service active; `nvidia-smi`/NVML failed with a driver/library version mismatch |
| Other runtimes | Python 3.12.3; Node 22.23.2; Docker 29.7.1; Git 2.43.0 |

### Fixed preliminary probe results

All measured requests used a fresh single-turn prompt, no tools/retrieval/web/history, `temperature: 0`, `seed: 42`, `num_ctx: 4096`, JSON Schema through Ollama `format`, `think: false`, and a 120-second measured timeout. Each installed candidate received one separate discarded warmup.

| Candidate | Exact digest | Parameters / disk | Quantization | Loaded memory / processor | Min system memory headroom | Warm output tok/s (three probes) | Median wall latency | Structured-output observation | Classification |
|-----------|--------------|-------------------|--------------|---------------------------|----------------------------|----------------------------------|---------------------|-------------------------------|----------------|
| `qwen3.5:9b` | `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7` | 9.7B / 6,594,474,711 bytes | Q4_K_M | `ollama ps`: 8.8 GB, 100% GPU, 4,096 context | 23,020,163,072 bytes (21.4 GiB) | 48.25, 47.86, 48.52; median **48.25** | **1.483 s** | Valid JSON 3/3; exact schema 1/3; no thinking text returned | **Viable on TheImp** |
| `gemma4:12b` | Unavailable | Catalog only; not locally verified | Catalog only; not locally verified | Not loaded | Not measured | Not measured | Not measured | Pull rejected with HTTP 412: newer Ollama required | **Unavailable or unverified** |
| `llama3.1:8b` | `46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e` | 8.0B / 4,920,753,328 bytes | Q4_K_M | `ollama ps`: 5.5 GB, 100% GPU, 4,096 context | 23,831,220,224 bytes (22.2 GiB) | 67.76, 69.88, unavailable; successful-run median **68.82** | Successful-run median **0.613 s** | Exact schema 2/2 successful; third request triggered grammar parse failure, runner SIGSEGV, and HTTP 500; no thinking capability exposed | **Viable on TheImp**, with runtime defect caveat |

Both installed candidates loaded without OOM. The Qwen native context field is 262,144 tokens and the Llama native context field is 131,072; the observed probe configuration and loaded context were 4,096 for both. The memory-headroom values above are sampled Linux `MemAvailable`, not GPU-free-memory measurements. Ollama logged full CUDA layer offload and its loaded allocation, but independent NVML telemetry was unavailable.

The Llama median values use the two successful measured probes. The failed third request is retained as operational evidence and is not repaired or converted into a model-quality result. Ollama logged `llama_grammar_init_impl: failed to parse grammar`, followed by `SIGSEGV` and HTTP 500.

### Required action before freezing the three-profile local set

Approve an Ollama runtime upgrade, then re-pull the exact `gemma4:12b` tag and rerun all three candidates under that single runtime version. Rerunning Qwen and Llama is necessary because changing the runtime changes the model profile evidence. If Gemma remains unavailable or fails a viability gate after the upgrade, request approval to substitute the policy-listed smaller current Gemma profile (first candidate: Gemma 3 4B), add a decision record, and create a distinct profile. No substitution is approved yet.

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
- [x] Pull/probe candidates one at a time; Gemma pull failed without deleting existing data
- [x] Test installed candidates against local viability gates
- [ ] Confirm the three local profiles or record substitutions

Cloud credentials, live identity, pricing snapshots, and spending approval are deferred until cloud adapter work begins. None blocks Phase 1 or local batches.

## Related documents

- [MVP_MASTER_PLAN.md](MVP_MASTER_PLAN.md)
- [BENCHMARK_SPEC.md](BENCHMARK_SPEC.md)
- [EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md)
- [PROVENANCE_AND_REPRODUCIBILITY.md](PROVENANCE_AND_REPRODUCIBILITY.md)
- [PROJECT_STATE.md](PROJECT_STATE.md)
- [DECISION_LOG.md](DECISION_LOG.md)

# TheImp Phase 1 local validation evidence — 2026-07-31

This directory contains direct local observations for hardware profile `theimp-2026-07-31`. Probe outputs are preliminary hardware-validation evidence, not benchmark scores. No cloud API was called.

## Procedure

- Confirmed hostname `TheImp` before substantive work.
- Captured hardware, storage, runtime, service, and installed-model command output.
- Confirmed 120 GiB free before attempting the missing approved model pull.
- Probed one candidate at a time with one discarded warmup followed by fresh extraction, classification, and normalization requests.
- Used Ollama JSON Schema mode, `think: false`, a 4,096-token request context, no tools/web/retrieval/history, and a 120-second measured timeout.
- Preserved the unmodified response text inside each raw Ollama response. No malformed or nonconforming output was repaired.

The probe utility is [`scripts/phase1_local_probe.py`](../../scripts/phase1_local_probe.py). It is a one-off evidence collector, not the production runner.

## Evidence manifest

| Path | Contents |
|------|----------|
| [`hardware-runtime-profile.raw.json`](hardware-runtime-profile.raw.json) | Raw command results, Ollama API version, and complete installed-model inventory |
| [`ollama-probe-service-log.raw.json`](ollama-probe-service-log.raw.json) | Local service log spanning both candidate probes and NVIDIA proc metadata |
| [`SHA256SUMS`](SHA256SUMS) | SHA-256 manifest for every other evidence file |
| [`models/qwen3.5-9b/`](models/qwen3.5-9b/) | Exact metadata, discarded warmup, three raw probes, summary, unload response |
| [`models/llama3.1-8b/`](models/llama3.1-8b/) | Exact metadata, discarded warmup, three raw probes, summary, unload response |
| [`models/gemma4-12b/pull-failure.raw.json`](models/gemma4-12b/pull-failure.raw.json) | Exact local pull failure; no Gemma model was installed or probed |

## Installed Ollama inventory at capture

Sizes below are raw bytes returned by `/api/tags`. The `glm-5:cloud` inventory entry was listed only; it was not invoked.

| Tag | Digest | Bytes | Parameters | Quantization |
|-----|--------|------:|------------|--------------|
| `nomic-embed-text:latest` | `0a109f422b47e3a30ba2b10eca18548e944e8a23073ee3f3e947efcf3c45e59f` | 274,302,450 | 137M | F16 |
| `mistral-small3.1:latest` | `b9aaf0c2586a8ed8105feab808c0f034bd4d346203822f048e2366165a13f4ea` | 15,486,899,116 | 24.0B | Q4_K_M |
| `mxbai-embed-large:latest` | `468836162de7f81e041c43663fedbbba921dcea9b9fefea135685a39b2d83dd8` | 669,615,493 | 334M | F16 |
| `orieg/gemma3-tools:12b-ft` | `9093ab43e762e852763d66e33ef1eec557780a8fe321754f73a1bf7858bc33ad` | 7,300,781,017 | 11.8B | Q4_K_M |
| `deepseek-r1:14b` | `c333b7232bdb521236694ffbb5f5a6b11cc45d98e9142c73123b670fca400b09` | 8,988,112,209 | 14.8B | Q4_K_M |
| `qwen2.5-coder:14b` | `9ec8897f747e246e970bc5cfdda85d22f1123dc2e3d34978a010a75968716849` | 8,988,124,298 | 14.8B | Q4_K_M |
| `llama3.1:8b` | `46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e` | 4,920,753,328 | 8.0B | Q4_K_M |
| `qwen2.5:14b` | `7cdf5a0187d5c58cc5d369b255592f7841d1c4696d45a8c8a9489440385b22f6` | 8,988,124,069 | 14.8B | Q4_K_M |
| `qwen2.5vl:7b` | `5ced39dfa4bac325dc183dd1e4febaa1c46b3ea28bce48896c8e69c1e79611cc` | 5,969,245,856 | 8.3B | Q4_K_M |
| `hermes4:14b-q4` | `6ec77fc645bcd93e47e131a57cdba12ce5c41d4dd45527c241041941466f8ad0` | 9,001,749,790 | 14.8B | Q4_K_M |
| `glm-5:cloud` | `c313cd06593533865448bd609a95c40c6e13d87ddf2daeb3b8f342e1a6c34794` | 323 | Not reported | Not reported |
| `qwen3.5:9b` | `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7` | 6,594,474,711 | 9.7B | Q4_K_M |
| `qwen3:8b` | `500a1f067a9f782620b40bee6f7b0c89e17ae61f686b92c24933e4ca4b2b8b41` | 5,225,388,164 | 8.2B | Q4_K_M |

## Outcome

| Candidate | Hardware classification | Evidence boundary |
|-----------|-------------------------|-------------------|
| `qwen3.5:9b` | Viable on TheImp | All hardware gates passed; JSON parsed 3/3, exact supplied schema honored 1/3 |
| `gemma4:12b` | Unavailable or unverified | Pull returned HTTP 412 because Ollama 0.17.4 is too old; no digest or local metrics exist |
| `llama3.1:8b` | Viable on TheImp, with runtime caveat | Hardware gates passed on two successful measured probes; third schema caused grammar parse failure, runner SIGSEGV, and HTTP 500 |

The NVIDIA device and CUDA inference were directly observed, but independent `nvidia-smi`/NVML telemetry failed because the driver and userspace library versions do not match. System-memory headroom is therefore reported separately from Ollama's loaded GPU allocation.

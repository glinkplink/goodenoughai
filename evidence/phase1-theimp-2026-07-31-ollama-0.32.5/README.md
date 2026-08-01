# TheImp Phase 1 final local-profile evidence — Ollama 0.32.5

This directory freezes the final Phase 1 local runtime and model profiles for hardware profile `theimp-2026-07-31-ollama-0.32.5`. These are preliminary hardware/runtime probes, not benchmark scores. No cloud API was called.

## Outcome

- Upgraded the official-script Ollama installation from client/daemon 0.17.4 to 0.32.5.
- Verified the official v0.32.5 Linux archive against Ollama's published SHA-256: `f7d6bdbcf71b83aa8670c4e7dc4b6936c0952fcf8b114eaf6a11cbadb9684214`.
- Preserved the 0.17.4 binary and runtime libraries as versioned backups.
- Preserved the systemd unit, drop-in, model path, and all 13 pre-existing model entries; their digests and sizes are unchanged.
- Pulled exact `gemma4:12b`, leaving 14 installed entries and 108 GiB filesystem space available after the pull.
- Verified all three exact candidates on one 0.32.5 runtime. Every candidate passes all five approved hardware gates.
- Verified 9/9 measured requests as parseable JSON and exact supplied-schema matches after the compatibility adaptation described below.
- Unloaded every candidate after measurement; the final `/api/ps` candidate list is empty.

Phase 1 is complete and Phase 2 is ready. The NVIDIA reboot and JSON Schema regex limitation remain documented operational follow-ups, not model-quality verdicts or Phase 2 blockers.

## Fixed procedure

For each candidate, sequentially:

1. One discarded warmup.
2. Three fresh measured requests: extraction, classification/routing, and normalization.
3. Ollama `/api/chat` JSON Schema mode, `think: false`, temperature 0, seed 42, requested context 4,096, and maximum output 256.
4. One user message only; no tools, web, retrieval, external context, repair, or conversation history.
5. A 120-second measured timeout.
6. Raw request, response, errors, timing/token counters, memory samples, loaded allocation, and service log retained.
7. Candidate unloaded after measurement.

The collector is [`scripts/phase1_local_probe.py`](../../scripts/phase1_local_probe.py). Structured invariants are checked by [`scripts/validate_phase1_evidence.py`](../../scripts/validate_phase1_evidence.py).

## Runtime and service preservation

| Item | Before | Final |
|------|--------|-------|
| Ollama client / daemon | 0.17.4 / 0.17.4 | 0.32.5 / 0.32.5 |
| Main unit SHA-256 | `11758d469d3f103e53a9612a8ffcb3a3e61834c994c08d412bb051f3c827dbd3` | Unchanged |
| Drop-in SHA-256 | `d30d58cf12bef230f581111197653c4a5d58d655beba93877027040f331f8922` | Unchanged |
| Service account | `ollama:ollama` | Unchanged |
| Bind address | `0.0.0.0:11434` | Unchanged |
| Model path | `/usr/share/ollama/.ollama/models` | Unchanged |
| Installed inventory | 13 entries | Same 13 plus exact `gemma4:12b` |
| Candidate processes after capture | None | None |

The main service remained active and enabled after the upgrade. The 0.17.4 runtime backups remain at `/usr/local/bin/ollama-0.17.4-backup` and `/usr/local/lib/ollama-0.17.4-backup`; no cleanup was performed.

## Frozen model profiles

| Candidate | Full digest | Parameters / disk | Quantization | Native / requested context | Thinking control | Loaded allocation | Minimum system headroom | Classification |
|-----------|-------------|-------------------|--------------|----------------------------|------------------|-------------------|-------------------------|----------------|
| `qwen3.5:9b` | `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7` | 9.7B / 6,594,474,711 bytes | Q4_K_M | 262,144 / 4,096 | Capability exposed; `think: false`; no thinking field returned | 5.6 GB, 100% GPU | 21,796,564,992 bytes | **Viable on TheImp** |
| `gemma4:12b` | `4eb23ef187e2c5462566d6a1d3bbbc2f1346d0b4327cbb66d58fffbcc9b2b05c` | 11.9B / 7,556,508,396 bytes | Q4_K_M | 262,144 / 4,096 | Capability exposed; `think: false`; no thinking field returned | 8.1 GB, 100% GPU | 23,205,302,272 bytes | **Viable on TheImp** |
| `llama3.1:8b` | `46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e` | 8.0B / 4,920,753,328 bytes | Q4_K_M | 131,072 / 4,096 | No thinking capability exposed; `think: false` accepted | 5.3 GB, 100% GPU | 23,115,485,184 bytes | **Viable on TheImp** |

Headroom is sampled Linux `MemAvailable`. Independent GPU-free-memory telemetry remains unavailable until the NVIDIA mismatch is cleared; loaded allocation and full GPU placement are direct `ollama ps` observations.

## Exact measured probes

| Candidate | Probe | Output tokens | Output tok/s | Wall latency | JSON parsed | Exact schema |
|-----------|-------|--------------:|-------------:|-------------:|-------------|--------------|
| `qwen3.5:9b` | Extraction | 34 | 49.73 | 1.019 s | Yes | Yes |
| `qwen3.5:9b` | Classification | 21 | 46.04 | 0.768 s | Yes | Yes |
| `qwen3.5:9b` | Normalization | 43 | 54.88 | 1.098 s | Yes | Yes |
| `gemma4:12b` | Extraction | 36 | 36.53 | 1.400 s | Yes | Yes |
| `gemma4:12b` | Classification | 22 | 33.15 | 1.069 s | Yes | Yes |
| `gemma4:12b` | Normalization | 43 | 39.40 | 1.491 s | Yes | Yes |
| `llama3.1:8b` | Extraction | 29 | 61.42 | 0.656 s | Yes | Yes |
| `llama3.1:8b` | Classification | 15 | 58.99 | 0.422 s | Yes | Yes |
| `llama3.1:8b` | Normalization | 29 | 63.80 | 0.618 s | Yes | Yes |

| Candidate | Median warm output tok/s | Median measured latency | OOM | ≥1 GiB headroom | Gate result |
|-----------|---------------------------:|------------------------:|-----|-----------------|-------------|
| `qwen3.5:9b` | 49.73 | 1.019 s | No | Yes | Pass |
| `gemma4:12b` | 36.53 | 1.400 s | No | Yes | Pass |
| `llama3.1:8b` | 61.42 | 0.618 s | No | Yes | Pass |

## Structured-output compatibility finding

The untouched original probe schema used the valid JSON Schema date pattern `^\d{4}-\d{2}-\d{2}$`. Ollama 0.32.5 converted `\d` into an invalid grammar escape and returned HTTP 400 (`Failed to initialize samplers: failed to parse grammar`) before normalization reached any of the three models. Unlike the 0.17.4 Llama observation, the 0.32.5 runner did not crash.

The preserved original pass is under [`models/`](models/). The final pass under [`compatible-pattern-schema/`](compatible-pattern-schema/) changes only that pattern to the semantics-equivalent ASCII form `^[0-9]{4}-[0-9]{2}-[0-9]{2}$`. All other prompts, schemas, parameters, timeouts, and procedures are unchanged. The final pass succeeds 9/9 for JSON parsing and exact schema checks.

This is an Ollama schema-conversion limitation, not a model-quality verdict. Phase 2's Ollama adapter must contract-test JSON Schema regex keywords and retain downstream deterministic validation even when native structured output is enabled.

## NVIDIA diagnosis

| Layer | Directly observed version |
|-------|---------------------------|
| Loaded kernel module | 595.71.05 |
| Installed module for kernel `6.17.0-35-generic` | 595.84 |
| DKMS status | 595.84 installed for `6.17.0-35-generic` and `7.0.0-28-generic` |
| Active NVML userspace library | 595.84 |
| `nvidia-smi` | Fails: driver/library version mismatch |

The machine booted on 2026-07-18; the 595.84 module file was installed on 2026-07-31. The loaded module is stale while the on-disk module and userspace library already match. A reboot should load 595.84 and resolve this mismatch. No NVIDIA package, kernel-module, or reboot action was performed. Both 590 and 595 package families are installed; cleanup may be reviewed later, but package replacement is not required to resolve the observed mismatch.

## Evidence manifest

| Path | Contents |
|------|----------|
| [`runtime-pre-upgrade.raw.json`](runtime-pre-upgrade.raw.json) | Host, 0.17.4 client/daemon, service configuration, inventory, storage, and NVIDIA state |
| [`runtime-post-upgrade.raw.json`](runtime-post-upgrade.raw.json) | Immediate 0.32.5 health/configuration/inventory capture before Gemma pull |
| [`runtime-final-profile.raw.json`](runtime-final-profile.raw.json) | Final 0.32.5 service, 14-entry inventory, storage, and empty candidate process list |
| [`upgrade-provenance.raw.json`](upgrade-provenance.raw.json) | Official sources, release metadata, archive digest, backups, and preserved service checksums |
| [`nvidia-mismatch-diagnosis.raw.json`](nvidia-mismatch-diagnosis.raw.json) | Loaded/on-disk module, DKMS, userspace library, package, boot, and kernel-log evidence |
| [`ollama-probe-service-log.raw.json`](ollama-probe-service-log.raw.json) | Ollama journal spanning upgrade, pull, original failure pass, and final pass |
| [`models/gemma4-12b/pull.raw.json`](models/gemma4-12b/pull.raw.json) | Exact Gemma pull with before/after storage and inventory |
| [`models/`](models/) | Preserved original-schema diagnostic pass for all three candidates |
| [`compatible-pattern-schema/`](compatible-pattern-schema/) | Final compatibility-preserving warmups, requests, responses, measurements, summaries, and unload results |
| [`SHA256SUMS`](SHA256SUMS) | SHA-256 manifest for every other evidence file |

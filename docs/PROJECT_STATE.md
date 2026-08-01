> **Status:** Active  
> **Authority:** Source of truth for operational handoff  
> **Last reviewed:** 2026-08-01  
> **Update when:** Phase, priorities, blockers, or completed work changes  
> **Related:** [MVP_MASTER_PLAN.md](MVP_MASTER_PLAN.md), [roadmap.md](../roadmap.md), [MVP_SCOPE.md](MVP_SCOPE.md), [DECISION_LOG.md](DECISION_LOG.md)

# Project state

## Current phase

**Phase 0 — Documentation audit: complete.**

**Phase 1 — Local hardware and model validation: complete.** The exact Qwen, Gemma, and Llama profiles are frozen on TheImp/Ollama 0.32.5 and all pass the approved local viability gates.

**Phase 2 — Local benchmark foundation: in progress.** Tracked SQLite migrations (`0001_initial.sql`, `0002_batch_purpose.sql`), a portable repository boundary for benchmark batches and planned runs, idempotent/resumable planned-run persistence, explicit `batch_purpose`, parent-batch/planned-run provenance enforcement, and statement-complete migration execution are implemented. The Python package, placeholder-only CLI, strict Pydantic lifecycle boundaries, focused unit tests, and operational ignore rules remain in place. No runner behavior, adapters, corpus, scoring implementation, artifact store, or public application exists yet.

No production application, benchmark corpus, stable benchmark run, or deployed infrastructure exists.

The approved delivery sequence now treats Phase 3 as a reviewed release candidate, not the final suite freeze. Phase 4 runs the 15-case pre-freeze pilot, corrects defects, repeats invalidated human reviews, and only then freezes `automation-mvp-v0.1.0`. Pre-launch discovery runs alongside Phases 2–4, with an explicit investment decision before the full stable batch and static site.

## Completed in Phase 0

- Added [MVP_MASTER_PLAN.md](MVP_MASTER_PLAN.md) as the primary living plan and mapped every major historical-brief requirement to a canonical document
- Approved 75 cases, three task families, six exact candidate surfaces, three repetitions, and **1,350 planned runs**
- Replaced the former 250-case/five-category roadmap conflict with the approved Phases 0–7 delivery plan
- Approved Python + SQLite + immutable filesystem artifacts + versioned public JSON + static Next.js architecture
- Deferred Supabase/PostgreSQL, authentication, payments, Redis, live routing, public API, subscriptions, and remote workers
- Approved two human passes on every case, fixed scoring/verdict thresholds, timeouts, retry/order rules, local viability gates, and review sampling
- Clarified that cloud spending controls apply only when cloud calls begin and cannot block local work
- Confirmed candidate identifiers in official catalogs; did not claim credential access, prices, or performance
- Recorded X1-Carbon observations separately from TheImp

## Phase 1 evidence collected on TheImp

- Confirmed hostname `TheImp` and assigned hardware profile `theimp-2026-07-31`
- Recorded Linux Mint 22.3/kernel 6.17.0-35, Ryzen 5 7600X (6 physical/12 logical cores), 30 GiB RAM, 2 GiB swap, RTX 3060, storage, runtimes, active Ollama service, and installed-model inventory
- Preserved the historical Ollama 0.17.4 evidence under [`evidence/phase1-theimp-2026-07-31/`](../evidence/phase1-theimp-2026-07-31/)
- Upgraded the official-script installation in place to Ollama 0.32.5 using the official archive and verified its published SHA-256
- Preserved the service unit, drop-in, model path, all 13 existing model entries, and versioned 0.17.4 runtime backups
- Pulled exact `gemma4:12b` and verified its full digest, 11.9B parameter size, 7,556,508,396-byte disk size, Q4_K_M quantization, 262,144-token native context, and capabilities
- Ran one discarded warmup and three fresh measured requests for each exact candidate, sequentially, on the same 0.32.5 runtime; unloaded every candidate afterward
- Preserved the original `\d` grammar-conversion failure, then reran with the semantics-equivalent `[0-9]` pattern; final results parsed and matched the exact supplied schemas 9/9
- Classified Qwen, Gemma, and Llama as **Viable on TheImp**; these probes are hardware/runtime evidence, not benchmark scores
- Preserved final raw runtime, upgrade, pull, request/response, telemetry, service-log, NVIDIA, checksum, and invariant evidence under [`evidence/phase1-theimp-2026-07-31-ollama-0.32.5/`](../evidence/phase1-theimp-2026-07-31-ollama-0.32.5/)

## What exists

| Asset | Status |
|-------|--------|
| Historical brief | `initialprompt.md`, unchanged |
| Primary living plan | `docs/MVP_MASTER_PLAN.md` |
| Scope, methods, architecture, governance | Reconciled documentation under `docs/` |
| Production application | None |
| Benchmark corpus | None |
| Python package / CLI | `src/goodenough_bench/` scaffold with boundary schemas and explicit placeholder commands |
| Benchmark runner / database | Tracked SQLite migrations (`0001_initial.sql`, `0002_batch_purpose.sql`), statement-complete migration runner, and repository with batch-purpose persistence and parent-batch provenance enforcement; no runner execution yet |
| Boundary tests | Focused `unittest` coverage for construction, serialization, provenance, migrations (including upgrade and statement parsing), repository idempotency/conflict rules, and placeholder CLI behavior |
| Public web app | None |
| Stable model results | None |
| TheImp hardware/runtime profile | Frozen as `theimp-2026-07-31-ollama-0.32.5` |
| Local model probe evidence | All three exact profiles captured and hardware-gate viable |
| Dated pricing snapshots | None |

## Next five actions

1. Implement the immutable filesystem artifact store with write-before-parse checksums.
2. Add resumable fake-provider batch planning and idempotency tests.
3. Add pricing-snapshot and model-profile loaders without collecting prices.
4. Prepare a discovery interview script and recruit 8–12 target automation builders without making unverified benchmark claims.
5. Keep pre-launch discovery aligned with DEC-0019 without publishing pilot rankings.

## Current follow-ups and deferred gates

| Blocker | Why it matters | Resolution |
|---------|----------------|------------|
| NVIDIA NVML mismatch | Independent GPU telemetry is unavailable; loaded module 595.71.05 is stale while installed module/userspace are 595.84 | Reboot in a separately approved maintenance window, then rerun `nvidia-smi`; does not block Phase 2 |
| Ollama JSON Schema regex conversion | Ollama 0.32.5 rejects `\d` while building a grammar; `[0-9]` succeeds for all three models | Contract-test adapter schemas and keep downstream deterministic validation; does not block Phase 2 |
| Runtime library ownership hardening | The installed 0.32.5 library tree retained operator ownership during the reversible staged copy | Run `sudo chown -R root:root /usr/local/lib/ollama`; inference and evidence are unaffected |
| Cloud account access unverified | Deferred; does not block local work | Verify when cloud adapter work begins |
| Dated cloud prices/token volume missing | Deferred; required only before paid cloud calls | Pricing snapshots + cloud-only estimate |

These are operational follow-ups or deferred cloud gates, not Phase 2 blockers or unresolved scope decisions.

## Current TheImp observation

| Item | Observed 2026-07-31 |
|------|---------------------|
| Repository path | `/home/q/Documents/MVPs/GoodEnough.ai` after laptop-to-TheImp migration |
| OS / kernel | Linux Mint 22.3; `6.17.0-35-generic` |
| CPU | AMD Ryzen 5 7600X; 6 physical cores / 12 logical CPUs |
| RAM / swap | 30 GiB RAM; 2.0 GiB swap, essentially exhausted at initial inspection |
| GPU | NVIDIA GeForce RTX 3060; Ollama logged CUDA use, 12.0 GiB VRAM, and full layer offload; NVML tooling is mismatched |
| Root storage | 468 GiB total, 108 GiB free after Gemma pull and runtime backup preservation |
| Runtimes | Ollama 0.32.5; Python 3.12.3; Node 22.23.2; Docker 29.7.1; Git 2.43.0 |
| Ollama service | Active and enabled; exact Qwen, Gemma, and Llama tags installed and final candidate process list empty |

The earlier X1-Carbon record remains historical only and must not be used as TheImp evidence.

## Approved cost position

- Known planning cash cost: **$0**
- Cloud calls: deferred; any spending guardrail is evaluated only before paid cloud calls and does not apply to local inference
- Hosting/analytics: **$0 assumed** on free tiers
- Domain, electricity, reviewer labor, and optional form-provider costs: unverified and separate from the cloud cap

## Stop gates

- Do not start runner implementation if TheImp/launch identities cannot be verified or a viable local set cannot be documented.
- Do not make paid cloud calls without a dated price snapshot, verified identity, and approved cloud-only estimate.
- Do not run a stable batch before two-pass corpus approval and frozen prompts, cases, profiles, prices, thresholds, and scorer version.
- Do not publish if surface separation, provenance, evidence redaction, checksum validation, or critical scoring tests fail.

## Related documents

- [MVP_MASTER_PLAN.md](MVP_MASTER_PLAN.md)
- [roadmap.md](../roadmap.md)
- [MODEL_LAUNCH_SET.md](MODEL_LAUNCH_SET.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [RISKS_AND_ASSUMPTIONS.md](RISKS_AND_ASSUMPTIONS.md)
- [DECISION_LOG.md](DECISION_LOG.md)

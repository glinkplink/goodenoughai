> **Status:** Active  
> **Authority:** Source of truth for operational handoff  
> **Last reviewed:** 2026-07-31  
> **Update when:** Phase, priorities, blockers, or completed work changes  
> **Related:** [MVP_MASTER_PLAN.md](MVP_MASTER_PLAN.md), [roadmap.md](../roadmap.md), [MVP_SCOPE.md](MVP_SCOPE.md), [DECISION_LOG.md](DECISION_LOG.md)

# Project state

## Current phase

**Phase 0 — Documentation audit: complete.**

**Phase 1 — Local hardware and model validation: blocked before profile freeze.** TheImp and two installed candidates are verified; `gemma4:12b` cannot be pulled by Ollama 0.17.4 and needs an approved runtime upgrade or an approved substitution.

No production application, benchmark corpus, stable benchmark run, or deployed infrastructure exists.

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
- Preserved raw hardware, model metadata, requests, responses, memory samples, Ollama timing/token counters, and service logs under [`evidence/phase1-theimp-2026-07-31/`](../evidence/phase1-theimp-2026-07-31/)
- Ran one discarded warmup and three fresh structured-output requests each for `qwen3.5:9b` and `llama3.1:8b`, one model at a time
- Classified Qwen and Llama as hardware-gate viable; these probes are not benchmark scores
- Attempted the approved `gemma4:12b` pull after confirming 120 GiB free; the registry rejected Ollama 0.17.4 with HTTP 412 and no existing data was deleted
- Observed two runtime limitations: NVIDIA NVML driver/library mismatch, and Ollama structured-output failures (Qwen schema non-adherence; Llama grammar-parser crash)

## What exists

| Asset | Status |
|-------|--------|
| Historical brief | `initialprompt.md`, unchanged |
| Primary living plan | `docs/MVP_MASTER_PLAN.md` |
| Scope, methods, architecture, governance | Reconciled documentation under `docs/` |
| Production application | None |
| Benchmark corpus | None |
| Benchmark runner / database | None |
| Public web app | None |
| Stable model results | None |
| TheImp hardware profile | Captured as `theimp-2026-07-31` |
| Local model probe evidence | Qwen and Llama captured; Gemma pull failure captured |
| Dated pricing snapshots | None |

## Next five actions

1. Approve and perform an Ollama upgrade on TheImp; reconcile the NVIDIA driver/userspace mismatch in the same maintenance window if practical.
2. Pull the exact `gemma4:12b` tag, then rerun the identical fixed probes for Qwen, Gemma, and Llama under the same upgraded runtime.
3. If Gemma still fails availability or viability, approve a distinct smaller Gemma substitution and record it in the decision log.
4. Freeze the three local profiles only after all identities, structured-output behavior, and hardware gates are verified on one runtime.
5. Begin Phase 2's Python/SQLite/artifact foundation and Ollama adapter; cloud work remains deferred.

## Current blockers to implementation

| Blocker | Why it matters | Resolution |
|---------|----------------|------------|
| Gemma requires a newer Ollama runtime | Exact candidate is absent and cannot be probed on 0.17.4 | Approve runtime upgrade; re-pull and probe |
| Local profiles are not on one final runtime | An upgrade changes runtime provenance and may change structured-output behavior | Rerun all three fixed probes after upgrade |
| NVIDIA NVML mismatch | `nvidia-smi` and independent GPU telemetry are unavailable despite working CUDA inference | Reconcile driver/userspace versions before profile freeze |
| Structured-output runtime defects | Qwen ignored schema fields; Llama runner crashed parsing one grammar | Retest after runtime upgrade; block profile freeze until characterized |
| Cloud account access unverified | Deferred; does not block local work | Verify when cloud adapter work begins |
| Dated cloud prices/token volume missing | Deferred; required only before paid cloud calls | Pricing snapshots + cloud-only estimate |

These are factual verification blockers, not unresolved scope or architecture decisions.

## Current TheImp observation

| Item | Observed 2026-07-31 |
|------|---------------------|
| Repository path | `/home/q/Documents/MVPs/GoodEnough.ai` after laptop-to-TheImp migration |
| OS / kernel | Linux Mint 22.3; `6.17.0-35-generic` |
| CPU | AMD Ryzen 5 7600X; 6 physical cores / 12 logical CPUs |
| RAM / swap | 30 GiB RAM; 2.0 GiB swap, essentially exhausted at initial inspection |
| GPU | NVIDIA GeForce RTX 3060; Ollama logged CUDA use, 12.0 GiB VRAM, and full layer offload; NVML tooling is mismatched |
| Root storage | 468 GiB total, 120 GiB free (74% used) before the failed Gemma pull |
| Runtimes | Ollama 0.17.4; Python 3.12.3; Node 22.23.2; Docker 29.7.1; Git 2.43.0 |
| Ollama service | Active and enabled; installed list includes the exact Qwen and Llama candidates but not Gemma |

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

> **Status:** Active  
> **Authority:** Source of truth for operational handoff  
> **Last reviewed:** 2026-07-31  
> **Update when:** Phase, priorities, blockers, or completed work changes  
> **Related:** [MVP_MASTER_PLAN.md](MVP_MASTER_PLAN.md), [roadmap.md](../roadmap.md), [MVP_SCOPE.md](MVP_SCOPE.md), [DECISION_LOG.md](DECISION_LOG.md)

# Project state

## Current phase

**Phase 0 — Documentation audit: complete.**

**Next: Phase 1 — Local hardware and model validation.**

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
| TheImp hardware profile | Not inspected |
| Dated pricing snapshots | None |

## Next five actions

1. Inspect TheImp and record CPU, physical/logical cores, RAM, swap, GPU, free storage, hardware ID, and runtime versions.
2. Verify/probe `qwen3.5:9b`, `gemma4:12b`, and `llama3.1:8b` one at a time; capture tag, digest, quantization, context, memory, throughput, and latency.
3. Record any necessary local substitutions and freeze the initial local profiles.
4. Begin the Python/SQLite/artifact foundation and Ollama adapter after the local viability gate passes.
5. Build the reviewed pilot corpus and deterministic scorers, then run the local pilot before starting cloud adapter work.

## Current blockers to implementation

| Blocker | Why it matters | Resolution |
|---------|----------------|------------|
| TheImp not inspected | Local feasibility cannot be inferred from X1-Carbon | Direct Phase 1 inspection |
| Local model profiles unprobed | Catalog files do not prove RAM/latency/throughput viability | Fixed local probes |
| Cloud account access unverified | Deferred; does not block local work | Verify when cloud adapter work begins |
| Dated cloud prices/token volume missing | Deferred; required only before paid cloud calls | Pricing snapshots + cloud-only estimate |

These are factual verification blockers, not unresolved scope or architecture decisions.

## Accessible-host observation

The machine available during the documentation audit was `X1-Carbon`, not TheImp:

- Intel Core i7-10510U, 4 physical cores / 8 threads
- 15 GiB RAM and 2 GiB swap
- Integrated Intel UHD graphics; no NVIDIA tooling
- About 14 GiB free workspace storage
- Ollama client 0.13.5; daemon/model list inaccessible from the sandbox
- Python 3.10.12, Node 22.14.0, Docker 29.7.1

The attached planning record reports that only `llama3.1:8b` was installed there during an earlier inspection; that daemon state was not independently re-verified in this session. X1-Carbon must not be used as TheImp’s hardware profile.

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

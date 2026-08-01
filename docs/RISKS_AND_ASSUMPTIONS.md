> **Status:** Active
> **Authority:** Living document
> **Last reviewed:** 2026-08-01
> **Update when:** Risks identified, mitigated, or assumptions verified
> **Related:** [DECISION_LOG.md](DECISION_LOG.md), [PROJECT_STATE.md](PROJECT_STATE.md), [MODEL_LAUNCH_SET.md](MODEL_LAUNCH_SET.md), [MVP_SCOPE.md](MVP_SCOPE.md)

# Risks and assumptions

Structured risk register. Severity: **L** likelihood, **I** impact (Low/Medium/High).

## Known facts

- Repository contains a Phase 2 Python package scaffold, lifecycle boundaries, tracked SQLite migrations, and batch/planned-run persistence; no runner execution, corpus, stable result, or public application exists (2026-08-01)
- Founding specs exist: `initialprompt.md`, `roadmap.md`
- Local worker machine named **TheImp** (Linux Mint server)
- MVP targets automation builders, not universal leaderboard audience
- The accessible host inspected on 2026-07-31 was `X1-Carbon`, not TheImp: Intel i7-10510U, 4 cores/8 threads, 15 GiB RAM, 2 GiB swap, integrated Intel graphics, and about 14 GiB free workspace storage
- X1-Carbon runtime observations: Ollama client 0.13.5, Python 3.10.12, Node 22.14.0, Docker 29.7.1; the Ollama daemon/model list was inaccessible from the sandbox
- Official catalogs list the six candidate identifiers as of 2026-07-31; catalog presence does not verify access, pricing, or performance
- Cloud spending controls apply only when cloud calls begin; they do not gate local work
- The repository was created on a laptop and migrated to TheImp; its active path is `/home/q/Documents/MVPs/GoodEnough.ai`, not the earlier `/home/billy/...` path (2026-07-31)
- TheImp was directly inspected on 2026-07-31: Ryzen 5 7600X (6 physical/12 logical cores), 30 GiB RAM, 2 GiB swap, RTX 3060 used by Ollama CUDA, and 120 GiB free on the root filesystem
- TheImp runs Ollama 0.32.5 as an active, enabled system service; the official archive digest, preserved systemd configuration, model path, existing inventory, and 0.17.4 runtime backups are recorded
- Exact `qwen3.5:9b`, `gemma4:12b`, and `llama3.1:8b` Q4_K_M profiles are installed and pass all approved local viability gates on the same runtime
- Final compatibility-preserving probes parsed and matched the supplied schemas 9/9; the original valid `\d` pattern remains preserved as an Ollama 0.32.5 grammar-conversion failure
- NVIDIA PCI/proc discovery and Ollama GPU execution work, but `nvidia-smi`/NVML fail because loaded module 595.71.05 is stale while installed module/DKMS/userspace are 595.84

## Assumptions (unverified)

| ID | Assumption | Verify by |
|----|------------|-----------|
| A3 | Six-model launch set fits budget and hardware | Smoke tests + cost estimate |
| A4 | Catalog-listed cloud model IDs are accessible to the project accounts | Phase 4 cloud smoke calls |
| A5 | 75-case corpus fits MVP timeline | Phase 3 authoring estimate |
| A6 | Automation builders will pay for custom benchmarks | Phase 4 pre-launch gate plus validation launch metrics |
| A7 | Deterministic scoring distinguishes models on these tasks | Phase 4 pilot and Phase 5 stable batch |
| A8 | **Verified 2026-07-31:** Q4_K_M is viable across all three local candidates | Frozen Ollama 0.32.5 profiles |

A1 is verified for all three local launch candidates. A2 was disproved: TheImp has a dedicated RTX 3060, and Ollama reported 100% GPU placement for every candidate probe.

## Phase 1 factual unknowns

No product-policy decision remains open after the documentation audit. The following external facts must still be measured or verified:

| ID | Unknown | Verify by |
|----|---------|-----------|
| U1 | **Resolved 2026-07-31:** TheImp hardware and storage profile | Raw hardware profile under `evidence/phase1-theimp-2026-07-31/` |
| U2 | **Resolved 2026-07-31:** Ollama 0.32.5 and all three exact tags/digests/quantizations/contexts captured | Final runtime/profile evidence |
| U3 | **Resolved 2026-07-31:** all three candidates measured consistently and pass hardware gates | Final compatibility-preserving probe set |
| U4 | Project credential access, rate limits, and returned cloud model identity | Direct provider smoke calls |
| U5 | Dated cloud prices and full-batch token/cost projection | Pricing snapshots plus pilot token counts |
| U6 | Electricity, domain, reviewer labor, and hosted-form costs | Dated measurement or quote |

---

## Risk register

### R1 — Limited local hardware

| Field | Value |
|-------|-------|
| Likelihood | High |
| Impact | High |
| Description | TheImp may not run Gemma 4 12B or desired quantizations within RAM/CPU limits |
| Mitigation | Phase 1 inspection; fallback models documented; record impractical-not-unsuitable separately |
| Trigger | OOM or >120s median latency on medium cases |
| Owner | Founder |
| Status | Mitigated for the launch set — all three exact Q4_K_M candidates pass the Phase 1 hardware gates |

### R2 — Cannot run larger desired models

| Field | Value |
|-------|-------|
| Likelihood | Medium |
| Impact | Medium |
| Description | 12B+ models impractical without GPU |
| Mitigation | Fallback to smaller models; defer GPU worker; document hardware limits publicly |
| Trigger | Failed smoke tests on Gemma 4 12B |
| Owner | Founder |
| Status | Mitigated for the launch set — exact Gemma 4 12B is viable on the RTX 3060/TheImp profile |

### R3 — Reliance on opaque web surfaces early

| Field | Value |
|-------|-------|
| Likelihood | Medium |
| Impact | Medium |
| Description | AutoGemini/browser data tempting for quick corpus but not credible as core benchmark |
| Mitigation | Separate surface labeling; API/local as primary; web as experimental section only |
| Trigger | Any web result on main leaderboard |
| Owner | All agents |
| Status | Mitigated by policy — enforce in implementation |

### R4 — Model alias and routing ambiguity

| Field | Value |
|-------|-------|
| Likelihood | High |
| Impact | High |
| Description | Provider model names change; OpenRouter routes differ from direct API |
| Mitigation | Record exact ID + confidence; pin snapshots; separate profiles per surface |
| Trigger | Score drift without code/corpus change |
| Owner | Benchmark operator |
| Status | Open |

### R5 — Provider model changes

| Field | Value |
|-------|-------|
| Likelihood | High |
| Impact | Medium |
| Description | Models deprecated or behavior shifts silently |
| Mitigation | Batch provenance; dated runs; drift tracking deferred but designed |
| Trigger | Re-run produces >10pp pass rate delta |
| Owner | Founder |
| Status | Open |

### R6 — Rapid pricing changes

| Field | Value |
|-------|-------|
| Likelihood | High |
| Impact | Medium |
| Description | Cost-per-accepted-result rankings stale quickly |
| Mitigation | Pricing snapshots with dates; never hardcode; show snapshot date on all economic metrics |
| Trigger | Provider announces pricing change |
| Owner | Founder |
| Status | Mitigated by design |

### R7 — Benchmark overfitting

| Field | Value |
|-------|-------|
| Likelihood | Medium |
| Impact | High |
| Description | Six models overfit to 75 cases; poor generalization to user workflows |
| Mitigation | Diverse case design; balanced 15-case pilot; transparent 75-case suite; test generalization through private/custom workflows and future versions (DEC-0015) |
| Trigger | Custom benchmark results contradict public suite systematically |
| Owner | Founder |
| Status | Open |

### R8 — Prompt sensitivity

| Field | Value |
|-------|-------|
| Likelihood | Medium |
| Impact | High |
| Description | Rankings change materially with minor prompt edits |
| Mitigation | Frozen prompt versions; publish prompts; test sensitivity in pilot phase |
| Trigger | Prompt patch changes verdict labels for >2 models |
| Owner | Founder |
| Status | Open |

### R9 — Synthetic-case realism

| Field | Value |
|-------|-------|
| Likelihood | Medium |
| Impact | Medium |
| Description | Synthetic corpus too clean vs real messy automation inputs |
| Mitigation | Adversarial formatting; missing info cases; iterate from custom benchmark feedback |
| Trigger | User feedback "not like my data" |
| Owner | Founder |
| Status | Open |

### R10 — Insufficient differentiation from leaderboards

| Field | Value |
|-------|-------|
| Likelihood | High |
| Impact | High |
| Description | Checkstack-style structured-extraction comparison, generic leaderboards, or modern routers are seen as "good enough" |
| Mitigation | Validate the narrower three-family, local/cloud provenance, cost-per-accepted-result, and escalation-evidence position during the Phase 4 investment gate |
| Trigger | Interviewees cannot identify an actionable benefit beyond existing alternatives |
| Owner | Founder |
| Status | Open — primary business risk per roadmap |

### R11 — Low user demand

| Field | Value |
|-------|-------|
| Likelihood | Medium |
| Impact | High |
| Description | Nobody uses comparisons or pays for custom benchmarks |
| Mitigation | Pre-launch interviews and pilot-report gate before the full batch/site investment; post-launch sequence and kill criteria remain |
| Trigger | Phase 4 investment gate or 45-day metrics fail |
| Owner | Founder |
| Status | Open |

### R12 — Scoring defects

| Field | Value |
|-------|-------|
| Likelihood | Medium |
| Impact | High |
| Description | Bug in scorer produces wrong pass rates |
| Mitigation | Golden fixtures; automated tests; human spot-check before publish |
| Trigger | Discovered inconsistency in evidence page |
| Owner | Implementing agent |
| Status | Open |

### R13 — LLM judge bias

| Field | Value |
|-------|-------|
| Likelihood | Low (MVP) |
| Impact | Medium |
| Description | If judge added, bias toward verbose or same-family outputs |
| Mitigation | MVP: deterministic only; judge secondary and disclosed if ever added |
| Trigger | N/A for MVP |
| Owner | Founder |
| Status | Mitigated by DEC-0003 |

### R14 — Browser-automation policy and reliability

| Field | Value |
|-------|-------|
| Likelihood | Medium |
| Impact | Medium |
| Description | Consumer sites prohibit automation; throttling breaks batch runs |
| Mitigation | Not in core runner; experimental section; prefer APIs |
| Trigger | ToS warning or blocking |
| Owner | Founder |
| Status | Open |

### R15 — API cost growth

| Field | Value |
|-------|-------|
| Likelihood | Medium |
| Impact | Low–Medium |
| Description | 675 planned primary cloud runs plus smoke/pilot calls and retries exceed budget |
| Mitigation | Estimate cloud-only cost when cloud adapters begin; use free tiers where appropriate; preserve raw responses; request approval before material spend |
| Trigger | Cloud adapter work is ready but no dated pricing estimate or spending approval exists |
| Owner | Founder |
| Status | Open |

### R16 — Data licensing

| Field | Value |
|-------|-------|
| Likelihood | Low |
| Impact | Medium |
| Description | Synthetic cases derived from copyrighted templates |
| Mitigation | Original synthetic authoring; license review before publish |
| Trigger | External content submission |
| Owner | Founder |
| Status | Open |

### R17 — Private customer-data handling

| Field | Value |
|-------|-------|
| Likelihood | Medium (if custom sales succeed) |
| Impact | High |
| Description | Customer PII in custom benchmarks |
| Mitigation | Isolation by project_id; deletion policy; no public reuse without permission |
| Trigger | First custom benchmark sale |
| Owner | Founder |
| Status | Open |

### R18 — Public trust

| Field | Value |
|-------|-------|
| Likelihood | Medium |
| Impact | High |
| Description | Perceived bias, hidden prompts, or web/API mixing destroys credibility |
| Mitigation | Raw evidence; methodology page; conflict-of-interest policy; surface separation |
| Trigger | Public criticism or discovered labeling error |
| Owner | All agents |
| Status | Open |

### R19 — Benchmark maintenance burden

| Field | Value |
|-------|-------|
| Likelihood | High |
| Impact | Medium |
| Description | Provider churn requires constant reruns |
| Mitigation | Batch versioning; publish less frequently; automate rerun pipeline later |
| Trigger | >8h/month manual maintenance sustained |
| Owner | Founder |
| Status | Open |

### R20 — Founder time constraints

| Field | Value |
|-------|-------|
| Likelihood | High |
| Impact | High |
| Description | Solo developer bottleneck on corpus, review, and sales |
| Mitigation | Narrow MVP; agent-assisted implementation; custom benchmark premium pricing |
| Trigger | Phase slips >4 weeks |
| Owner | Founder |
| Status | Open |

### R21 — Local GPU management stack mismatch

| Field | Value |
|-------|-------|
| Likelihood | Observed |
| Impact | Medium |
| Description | `nvidia-smi`/NVML fail because the July 18 boot still has kernel module 595.71.05 loaded while the installed module, DKMS record, and userspace library are 595.84; Ollama still reports 100% GPU placement |
| Mitigation | Reboot in a separately approved maintenance window, then rerun `nvidia-smi`; review redundant 590 packages later, but package replacement is not required for this mismatch |
| Trigger | Need for independent GPU utilization/headroom telemetry or any inference instability |
| Owner | Founder |
| Status | Diagnosed — reboot pending; does not block Phase 2 |

### R22 — Ollama structured-output incompatibilities

| Field | Value |
|-------|-------|
| Likelihood | Observed |
| Impact | High |
| Description | Ollama 0.32.5 rejects the valid `\d` JSON Schema regex while converting it to grammar; the semantics-equivalent `[0-9]` pattern succeeds 9/9 across all three candidates. The earlier 0.17.4 non-adherence/crash remains historical evidence |
| Mitigation | Contract-test JSON Schema keywords in the Phase 2 Ollama adapter, use semantics-preserving compatible schemas where required, preserve raw failures, and retain downstream deterministic schema validation |
| Trigger | Any schema/prompt/profile change or Ollama runtime upgrade |
| Owner | Implementing agent |
| Status | Characterized and mitigated for profile freeze; implementation contract test required in Phase 2 |

### R23 — Users prefer self-service evaluation over a public evidence database

| Field | Value |
|-------|-------|
| Likelihood | Medium |
| Impact | High |
| Description | Builders may value testing their own workflow but ignore a curated public benchmark, weakening the planned database-and-SEO wedge |
| Mitigation | Ask explicitly about current model-selection behavior; test a private pilot report; record demand for public evidence, custom reports, and self-service evaluation separately |
| Trigger | Participants value only their own uploaded cases or will not act on public-suite evidence |
| Owner | Founder |
| Status | Open — Phase 4 gate decides whether to continue, pivot, or stop |

---

## Resolved document contradictions

### roadmap.md vs initialprompt.md — corpus size and task categories

| Source | Statement |
|--------|-----------|
| `initialprompt.md` | 75 cases: 25 each × 3 families (extraction, classification, normalization) |
| Historical `roadmap.md` summary | Broader five-category, 250-case proposal |

**Resolution:** DEC-0001 **Approved** — 75 cases across three families. The conflicting 250-case/five-category roadmap text has been removed.

### roadmap.md vs initialprompt.md — broader category vision

| Source | Statement |
|--------|-----------|
| `roadmap.md` | Lists Linux troubleshooting, coding microtasks, agent reliability, transformation |
| `initialprompt.md` / MVP_SCOPE | Explicitly narrow to 3 structured-task families for MVP |

**Resolution:** DEC-0002 **Approved** — broad categories are deferred.

### Proposed Supabase architecture vs approved local-first architecture

| Source | Statement |
|--------|-----------|
| Earlier `ARCHITECTURE.md` / DEC-0008 proposal | Supabase/Postgres and dynamic application path |
| Attached approved plan | SQLite, filesystem artifacts, public JSON, static Next.js |

**Resolution:** DEC-0008 now approves the local-first architecture and supersedes the earlier Supabase proposal.

## Related documents

- [DECISION_LOG.md](DECISION_LOG.md)
- [PROJECT_STATE.md](PROJECT_STATE.md)
- [MVP_SCOPE.md](MVP_SCOPE.md)
- [MODEL_LAUNCH_SET.md](MODEL_LAUNCH_SET.md)
- [MONETIZATION_AND_VALIDATION.md](MONETIZATION_AND_VALIDATION.md)
- [BENCHMARK_SPEC.md](BENCHMARK_SPEC.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)

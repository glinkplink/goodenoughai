> **Status:** Active
> **Authority:** Living document
> **Last reviewed:** 2026-07-31
> **Update when:** Risks identified, mitigated, or assumptions verified
> **Related:** [DECISION_LOG.md](DECISION_LOG.md), [PROJECT_STATE.md](PROJECT_STATE.md), [MODEL_LAUNCH_SET.md](MODEL_LAUNCH_SET.md), [MVP_SCOPE.md](MVP_SCOPE.md)

# Risks and assumptions

Structured risk register. Severity: **L** likelihood, **I** impact (Low/Medium/High).

## Known facts

- Repository contains planning documents only — no application code (2026-07-31)
- Founding specs exist: `initialprompt.md`, `roadmap.md`
- Local worker machine named **TheImp** (Linux Mint server)
- MVP targets automation builders, not universal leaderboard audience
- The accessible host inspected on 2026-07-31 was `X1-Carbon`, not TheImp: Intel i7-10510U, 4 cores/8 threads, 15 GiB RAM, 2 GiB swap, integrated Intel graphics, and about 14 GiB free workspace storage
- X1-Carbon runtime observations: Ollama client 0.13.5, Python 3.10.12, Node 22.14.0, Docker 29.7.1; the Ollama daemon/model list was inaccessible from the sandbox
- Official catalogs list the six candidate identifiers as of 2026-07-31; catalog presence does not verify access, pricing, or performance
- Approved cloud model-call cap is $25 total

## Assumptions (unverified)

| ID | Assumption | Verify by |
|----|------------|-----------|
| A1 | TheImp runs Ollama and can host a credible local launch set | Phase 1 hardware inspection |
| A2 | No large dedicated GPU on TheImp | `nvidia-smi`, `lspci` |
| A3 | Six-model launch set fits budget and hardware | Smoke tests + cost estimate |
| A4 | Catalog-listed model IDs are accessible to the project accounts and local runtime | Live Phase 1 probes |
| A5 | 75-case corpus fits MVP timeline | Phase 3 authoring estimate |
| A6 | Automation builders will pay for custom benchmarks | Validation launch metrics |
| A7 | Deterministic scoring distinguishes models on these tasks | Phase 4 pilot and Phase 5 stable batch |
| A8 | Q4_K_M quantization is viable/comparable across local candidates | Phase 1 local probes |

## Phase 1 factual unknowns

No product-policy decision remains open after the documentation audit. The following external facts must still be measured or verified:

| ID | Unknown | Verify by |
|----|---------|-----------|
| U1 | TheImp CPU, cores, RAM, swap, GPU, storage, and hardware ID | Direct machine inspection |
| U2 | TheImp Ollama version, installed tags/digests, quantizations, and context settings | Ollama inspection |
| U3 | Local candidates' OOM behavior, memory headroom, throughput, and latency | Fixed probes on TheImp |
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
| Status | Open |

### R2 — Cannot run larger desired models

| Field | Value |
|-------|-------|
| Likelihood | Medium |
| Impact | Medium |
| Description | 12B+ models impractical without GPU |
| Mitigation | Fallback to smaller models; defer GPU worker; document hardware limits publicly |
| Trigger | Failed smoke tests on Gemma 4 12B |
| Owner | Founder |
| Status | Open |

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
| Likelihood | Medium |
| Impact | High |
| Description | Artificial Analysis / OpenRouter seen as "good enough" |
| Mitigation | Narrow focus; cost-per-accepted-result; failure evidence; task-specific pages |
| Trigger | Validation metrics not met |
| Owner | Founder |
| Status | Open — primary business risk per roadmap |

### R11 — Low user demand

| Field | Value |
|-------|-------|
| Likelihood | Medium |
| Impact | High |
| Description | Nobody uses comparisons or pays for custom benchmarks |
| Mitigation | Validation sequence; kill criteria; outreach to n8n/Make communities |
| Trigger | 45-day metrics failed |
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
| Mitigation | Phase 1 cost estimate; free tiers where available; batch freeze; preserve raw responses; enforce $25 cap |
| Trigger | Projected cumulative cloud model-call cost exceeds the approved $25 cap |
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

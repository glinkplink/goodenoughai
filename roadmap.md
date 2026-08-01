> **Status:** Active  
> **Authority:** Living delivery plan for milestones and sequencing  
> **Last reviewed:** 2026-08-01
> **Update when:** Phase goals, gates, effort, or priorities change  
> **Related:** [docs/MVP_MASTER_PLAN.md](docs/MVP_MASTER_PLAN.md), [docs/MVP_SCOPE.md](docs/MVP_SCOPE.md), [docs/PROJECT_STATE.md](docs/PROJECT_STATE.md), [docs/DECISION_LOG.md](docs/DECISION_LOG.md)

# GoodEnough.ai roadmap

GoodEnough.ai answers one narrow question:

> Which inexpensive AI model should an automation builder use for structured extraction, classification, and normalization?

This roadmap sequences the approved documentation-to-MVP plan. Scope is controlled by [MVP_SCOPE.md](docs/MVP_SCOPE.md), methodology by the benchmark specifications, and decisions by [DECISION_LOG.md](docs/DECISION_LOG.md).

## Delivery summary

| Phase | Outcome | Effort | Status |
|------:|---------|-------:|--------|
| 0 | Reconciled, implementation-ready documentation | 2–4 days | Complete |
| 1 | Verified local hardware and local model viability | 2–4 days | Complete |
| 2 | Local benchmark foundation | 6–10 days | In progress — migrations and repository complete |
| 3 | Reviewed corpus candidate and deterministic scoring | 12–18 days | Not started |
| 4 | Tested adapters, pre-freeze pilot, and frozen suite | 8–12 days | Not started |
| 5 | Stable benchmark and routing simulation | 2–5 active days plus runtime | Not started |
| 6 | Static public application | 8–12 days | Not started |
| 7 | Validation launch | 3–6 active days plus observation | Not started |

Estimated engineering effort: **43–71 ideal days**, excluding independent reviewer availability, model runtime, and the 30–45 day validation window. These are planning estimates, not commitments.

## Phase 0 — Documentation audit

### Goal

Turn the original brief and supporting documents into one consistent, implementation-ready plan without writing production code.

### Deliverables

- Requirement crosswalk and primary living plan in [MVP_MASTER_PLAN.md](docs/MVP_MASTER_PLAN.md)
- Approved 75-case, three-family, six-surface target: **1,350 planned runs**
- Approved local-first architecture and operational defaults
- Resolved decision markers and documented remaining factual unknowns
- Updated index, state, scope, risks, decision log, and changelog

### Acceptance gate

- [x] Every major `initialprompt.md` requirement maps to a canonical document
- [x] The former 250-case/five-category conflict is removed
- [x] Architecture no longer requires Supabase, authentication, queues, or remote workers
- [x] All policy decisions are closed; external facts remain explicitly unverified
- [x] Markdown links pass validation

### Cost and exclusions

- Known direct cost: **$0**
- No dependencies, cloud infrastructure, paid calls, corpus, or production code

## Phase 1 — Local hardware and model validation

### Goal

Verify that the three local candidates can run credibly on TheImp. Cloud credentials, pricing, and spending are intentionally deferred until cloud adapters are introduced.

### Deliverables

- TheImp hardware profile: CPU, physical/logical cores, RAM, swap, GPU, storage, and hardware ID
- Ollama/runtime versions, installed model digests, exact quantization, and context settings
- Candidate pull/probe results and one representative smoke prompt per accessible surface
- Documented substitutions where a local candidate fails identity or hardware gates

### Acceptance gate

- [x] TheImp—not another host—has been inspected
- [x] Each local launch surface has a verified profile or documented substitution
- [x] Local candidates pass the viability gate in [MODEL_LAUNCH_SET.md](docs/MODEL_LAUNCH_SET.md)
- [x] No unresolved local identity ambiguity remains

Exact Qwen 3.5 9B, Gemma 4 12B, and Llama 3.1 8B profiles were frozen on TheImp/Ollama 0.32.5 on 2026-07-31. All use Q4_K_M, loaded without OOM, retained more than 1 GiB system-memory headroom, exceeded 2 output tokens/second, and stayed below 120 seconds median measured latency. No substitution was required. The semantics-equivalent schema compatibility pass parsed and matched 9/9 outputs; the original `\d` grammar failure remains preserved as runtime evidence.

### Stop conditions

Stop before local runner implementation if TheImp cannot be inspected or a viable local launch set cannot be documented. Cloud pricing or budget cannot block local implementation or local benchmark runs.

### Cost and exclusions

- Expected cloud API cost: **$0** because Phase 1 makes no cloud calls
- Model downloads and electricity are separate local operating considerations
- No stable benchmark batch

## Phase 2 — Local benchmark foundation

### Goal

Create a reproducible, resumable local runner and persistence layer.

### Deliverables

- [x] Python 3.10+ package and placeholder-only CLI skeleton
- [x] Pydantic request, case, model-profile, planned-run, normalized-response, artifact, parse, and score-boundary schemas
- [x] Tracked SQLite migrations and repository layer
- [x] Explicit diagnostic-pilot/stable-benchmark batch purpose and enforced parent-batch/planned-run configuration consistency
- [x] Immutable filesystem artifact store with checksums
- [x] Pricing snapshots and model-profile loaders
- [x] Resumable batch lifecycle and reproduction metadata
- [x] Ignore rules for SQLite databases and raw/private artifacts; cases, profiles, and redacted exports remain future work

### Acceptance gate

- [x] Clean database can be created from migrations
- [x] Planned runs cannot persist dataset, runner, prompt, or run-order provenance that conflicts with their parent batch
- [x] Interrupted fake batch resumes without duplicate planned runs
- [x] Raw artifact is written before parsing and checksum-verified
- [ ] No secret or private payload appears in tracked/public output
- [x] Unit and migration tests pass

### Cost and exclusions

- Expected direct cash cost: **$0**
- No Supabase, PostgreSQL, auth, Redis, hosted API, or remote worker

## Phase 3 — Corpus candidate and deterministic scoring

### Goal

Prepare a credible, fully reviewed 75-case release candidate whose central metrics are deterministic and ready for a model-facing pilot. The final suite does not freeze until the pilot has exposed case, scorer, adapter, and provenance defects.

### Deliverables

- 25 cases per task family
- At least 12 cases in each required stress category, with overlap allowed
- Author pass plus independent reviewer sign-off on every case
- Deterministic parsers, normalizers, field scorers, classifiers, aggregators, and verdict logic
- Golden fixtures and corpus-quota validation
- Designated 15-case pilot subset
- Candidate suite manifest and checksum for the pre-freeze pilot

### Acceptance gate

- [ ] 75 cases validate against the case schema
- [ ] Every case records both human passes
- [ ] All stress-category quotas pass
- [ ] Thresholds, prompt version, scorer version, and candidate-suite checksum are locked and recorded before pilot calls
- [ ] Golden scoring fixtures cover every critical gate

### Cost and exclusions

- Expected direct cash cost: **$0**; reviewer labor is unpriced
- No new task families or subjective prose-primary cases

## Phase 4 — Adapters, pre-freeze pilot, and suite freeze

### Goal

Implement provider-neutral collection, prove every adapter boundary, use the 15-case pilot to find defects, and freeze the corrected 75-case suite before stable runs.

### Deliverables

- Ollama, Gemini, OpenAI Responses, direct DeepSeek, OpenRouter, manual JSONL, and AutoGemini adapters
- Implement and pilot Ollama first; begin cloud adapter smoke calls only after capturing credentials, dated prices, and a cloud-call estimate
- Direct DeepSeek as the launch profile; OpenRouter retained as a separately identified fallback/profile
- Native structured-output mode where supported, with differences disclosed
- Fake-provider contract tests for success, malformed output, timeout, rate limit, auth, server failure, and missing token counts
- Real smoke runs followed by a 15-case pilot
- Versioned correction of pilot-discovered defects, with both human reviews repeated after any material expected-output change
- Final suite manifest, checksum, and freeze as `automation-mvp-v0.1.0`

### Acceptance gate

- [ ] Every adapter passes the shared contract suite
- [ ] Direct and routed provider surfaces cannot merge in storage or exports
- [ ] Raw evidence survives parse/scoring failures
- [ ] Pilot reveals no critical case, scorer, provenance, or redaction defect
- [ ] Every changed case has current author and independent-reviewer approval
- [ ] The corrected 75-case suite, prompts, thresholds, and scorer version are frozen together
- [ ] Before the first paid cloud call, projected cloud-only spend fits the approved guardrail or has explicit approval

### Pre-launch investment gate

The pilot is diagnostic, not stable leaderboard evidence. Begin interviews with **8–12** target automation builders during Phases 2–4, then privately test a clearly labeled sample pilot report after the Phase 4 quality gates pass. Do not publish pilot rankings or present them as benchmark results.

Proceed to the full stable batch and public-site investment only after recording an explicit continue/pivot/stop decision. Continue evidence should include:

- At least **3** participants saying the evidence would change or confirm a model decision, or volunteering a real workflow for follow-up
- At least **1** credible willingness-to-pay signal for a custom comparison
- Clear recognition of value beyond a generic leaderboard, extraction-only benchmark, or live router

Missing the gate does not authorize a broader MVP. It triggers a positioning, custom-report, self-service-evaluation, or stop decision before Phase 5 spending.

### Cost and exclusions

- The cloud-only spending guardrail begins when cloud calls begin; it never applies to local development or local inference
- No consumer-web result on the main leaderboard

## Phase 5 — Stable benchmark and routing simulation

### Goal

Produce the first frozen, reproducible benchmark release.

### Deliverables

- Three independent repetitions for every model/case cell
- Immutable raw evidence, parsed results, deterministic scores, availability metrics, and aggregates
- Human spot checks and documented overrides
- Frozen result checksum and redacted public JSON export
- Deterministic validation plus selective-escalation simulations for viable primary/escalation pairs

### Acceptance gate

- [ ] Six tested surfaces or approved substitutions
- [ ] **1,350 planned runs** accounted for as valid or explicitly invalid
- [ ] At least 90% planned-run validity per publishable model/family cell
- [ ] Provenance complete on at least 95% of valid runs
- [ ] At least one escalation simulation is publishable
- [ ] Public claims trace to immutable evidence

### Stop conditions

Stop publication if the corpus lacks two-pass review, thresholds changed after seeing stable results, provenance is incomplete, exact and opaque surfaces can mix, or redaction fails. A cloud budget issue pauses only the cloud batch segment, not local work.

## Phase 6 — Static public application

### Goal

Publish the benchmark as a low-cost, evidence-first website.

### Deliverables

- TypeScript Next.js static export consuming only versioned public JSON
- Home, three family leaderboards, model detail, comparison, evidence, methodology, and custom-benchmark routes
- Configurable hosted form endpoint; no site database or account system
- Privacy-safe analytics events
- Cloudflare Pages deployment by default

### Acceptance gate

- [ ] Static build and public-export schema validation pass
- [ ] Playwright tests cover routes and two-to-three-model comparisons
- [ ] Responsive and accessibility checks pass
- [ ] Broken-link and redaction validation pass
- [ ] No private data, credentials, or mutable database dependency ships

### Cost and exclusions

- Hosting and analytics: **$0 assumed** on free tiers; any paid upgrade needs approval
- No auth, payments, subscriptions, API, live router, or application database

## Phase 7 — Validation launch

### Goal

Determine whether task-specific evidence changes model decisions and supports a paid custom-report service.

### Deliverables

- Outreach to automation-builder communities
- Monitored comparison usage and workflow submissions
- Manually qualified custom-benchmark leads
- First paid report attempt through manual invoicing
- 30–45 day continue/pivot/stop review

### Acceptance gate

- ≥100 qualified visitors
- ≥10 meaningful comparison users
- ≥5 workflow submissions
- ≥1 willingness-to-pay signal
- ≥3 users reporting a changed or confirmed model decision

Validation interpretation and kill criteria live in [MONETIZATION_AND_VALIDATION.md](docs/MONETIZATION_AND_VALIDATION.md).

## Deferred until after validation

- Supabase/PostgreSQL, authentication, payments, subscriptions, Redis, remote workers
- Live routing, benchmark/suggestion API, MCP interface, drift alerts, workflow exports, community contributions
- Claude and additional local/cloud model expansion
- IronWork, Linux troubleshooting, coding, agent reliability, or multimodal suites

Any scope expansion requires the process in [MVP_SCOPE.md](docs/MVP_SCOPE.md).

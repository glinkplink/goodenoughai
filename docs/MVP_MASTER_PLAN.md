> **Status:** Active  
> **Authority:** Primary living plan  
> **Last reviewed:** 2026-07-31  
> **Update when:** Scope, architecture, delivery sequence, acceptance gates, cost cap, or immediate priorities change  
> **Related:** [MVP_SCOPE.md](MVP_SCOPE.md), [BENCHMARK_SPEC.md](BENCHMARK_SPEC.md), [ARCHITECTURE.md](ARCHITECTURE.md), [roadmap.md](../roadmap.md), [DECISION_LOG.md](DECISION_LOG.md)

# GoodEnough.ai MVP master plan

## Executive summary

GoodEnough.ai will publish a narrow, reproducible benchmark answering:

> Which inexpensive AI model should an automation builder use for structured extraction, classification, and normalization?

The MVP is a local-first benchmark pipeline and static evidence site. It uses 75 reviewed cases, six exact model surfaces, and three independent repetitions—**1,350 planned runs**. Deterministic scoring controls central pass/fail metrics. Raw evidence, exact surface identity, dated pricing, and reproducibility metadata support every public claim.

The cheapest credible path is Python + SQLite + immutable filesystem artifacts + versioned public JSON + a statically exported Next.js site on Cloudflare Pages. Work begins with local models only. The cloud-call spending guardrail applies later, immediately before paid cloud calls, and never blocks local implementation or local batches. Supabase, authentication, payments, Redis, live routing, public APIs, subscriptions, and remote workers are deferred.

No production application, benchmark corpus, or stable result exists yet.

## Audience, question, and value

### Exact audience

- n8n, Make, and Zapier users
- Python automation builders and AI-agent developers
- Scraper and data-pipeline developers
- Solo developers and small agencies building repetitive AI workflows
- Builders choosing between ordinary local hardware and inexpensive cloud APIs

### Exact question

> Which inexpensive AI model should an automation builder use for structured extraction, classification, and normalization?

### Value proposition

GoodEnough.ai recommends the cheapest model that reliably passes a defined automation task, shows what failure looks like, and quantifies whether deterministic validation plus selective escalation beats premium-only processing.

It does not produce a universal intelligence score or generalize beyond the tested task, prompt, surface, version, and hardware.

## Locked MVP definition

| Dimension | Approved value |
|-----------|----------------|
| Task families | Structured extraction; classification/routing; structured normalization |
| Cases | 75 total; 25 per family |
| Model surfaces | Six exact launch surfaces: 3 local + 3 cloud |
| Repetitions | Three independent calls per model/case |
| Planned runs | **1,350** |
| Human ground-truth review | Author pass plus independent reviewer sign-off on every case |
| Primary evaluation | Deterministic scoring |
| Cloud-call spending guardrail | Evaluated only before paid cloud calls; not a local-work gate |
| Persistence | SQLite plus immutable filesystem artifacts |
| Publication interface | Versioned, redacted public JSON |
| Public application | Statically exported TypeScript Next.js site |
| Default hosting | Cloudflare Pages free tier assumption |

Authoritative boundaries and exclusions are in [MVP_SCOPE.md](MVP_SCOPE.md).

## Initial launch surfaces

| Role | Candidate | Launch surface | Current status |
|------|-----------|----------------|----------------|
| Local | Qwen 3.5 9B | Ollama `qwen3.5:9b` | Hardware-gate viable on TheImp/Ollama 0.17.4; structured schema not honored in 2/3 probes |
| Local | Gemma 4 12B | Ollama `gemma4:12b` | Unavailable/unverified: pull requires a newer Ollama runtime |
| Local | Llama 3.1 8B | Ollama `llama3.1:8b` | Hardware-gate viable on TheImp/Ollama 0.17.4; one schema grammar crashed the runner |
| Cloud | Gemini 3.5 Flash-Lite | Google API `gemini-3.5-flash-lite` | Official identifier/structured-output listing verified; account access/pricing snapshot unverified |
| Cloud | DeepSeek V4 Flash | Direct DeepSeek API `deepseek-v4-flash` | Official identifier listing verified; account access/pricing snapshot unverified |
| Cloud | GPT-5.6 Luna | OpenAI Responses API `gpt-5.6-luna` | Official identifier/structured-output listing verified; account access/pricing snapshot unverified |

Direct DeepSeek is the primary launch profile. An OpenRouter route is an adapter and fallback surface, not the same profile; any OpenRouter run records a distinct provider surface and never merges with direct-provider scores.

Exact catalog sources and substitution rules are maintained in [MODEL_LAUNCH_SET.md](MODEL_LAUNCH_SET.md). Catalog presence does not prove account access, pinned model identity, price, performance, or TheImp viability.

## Architecture summary

```text
Versioned YAML case
→ validation and suite freeze
→ provider-neutral adapter request
→ immutable raw artifact + checksum
→ SQLite run record
→ JSON parse and schema validation
→ deterministic score and verdict
→ routing simulation
→ versioned redacted public JSON
→ static Next.js pages
```

Core interfaces:

- `ModelAdapter.run(BenchmarkRequest) -> BenchmarkResponse` is asynchronous and contains no scoring logic.
- `ArtifactStore` writes immutable raw bytes and checksums; filesystem storage ships first.
- `Repository` persists suites, profiles, batches, runs, scores, prices, reviews, and simulations in SQLite behind a portable interface.
- The CLI exposes `cases validate`, `models probe`, `batch run`, `batch score`, `batch export`, `batch reproduce`, and `import`.
- Public JSON is versioned and read-only; the site has no runtime benchmark-database dependency.

Full boundaries and alternatives are in [ARCHITECTURE.md](ARCHITECTURE.md); conceptual entities are in [DATA_MODEL.md](DATA_MODEL.md).

## Benchmark and scoring summary

### Corpus

- 25 cases per task family
- At least 12 cases in each stress category, overlap allowed: hallucination resistance, missing/ambiguous information, strict schema/enum adherence
- Original realistic synthetic public data; no private customer data
- Adversarial formatting and prompt-injection text
- A designated 15-case pilot subset before the 75-case suite freezes as `automation-mvp-v0.1.0`
- Author review and independent reviewer sign-off recorded for every case

### Run controls

- Same task instruction, source, schema, and output limit where surfaces permit
- Fresh request; no tools, search, retrieval, external context, or history
- Native strict structured-output/schema mode where supported; non-equivalent controls disclosed
- Lowest practical randomness and reasoning disabled/minimized where exposed
- One discarded warmup per local model; one model at a time; seeded case order; separate repetition rounds
- Local scored timeout 120 seconds; cloud timeout 60 seconds
- Up to three retries for transient 429/5xx failures; retries are not repetitions
- Partial or repaired JSON fails parse scoring; original bytes remain evidence

### Case gates

- Valid JSON and schema compliance: mandatory
- Required-field recall and normalized-field accuracy: ≥95%
- Critical-field accuracy: 100%
- Unsupported-field rate: ≤1%
- Listed forbidden invention: automatic run failure
- Provider failures: availability metrics only, never model-quality scores

### Family verdicts

- **Reliable:** pass rate ≥90%, consistency ≥85%, unsupported-field rate ≤1%
- **Usable with validation:** pass rate 75–89%, or a ≥90% cell missing a `Reliable` secondary gate, when deterministic validation covers critical failures
- **Escalation recommended:** pass rate 50–74% and routed simulation materially improves reliability or cost
- **Not suitable:** pass rate <50% or critical failures cannot be detected safely
- **Insufficient data:** fewer than 90% of planned runs are valid for that model/family cell

Detailed formulas and edge policies are authoritative in [SCORING_AND_EVALUATION.md](SCORING_AND_EVALUATION.md); execution rules are authoritative in [EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md).

## Local viability policy

A local profile is viable only when all gates pass on TheImp:

- Q4_K_M or a separately documented comparable equivalent
- No out-of-memory failure
- At least 1 GiB memory headroom during the probe
- Median warm throughput ≥2 output tokens/second
- Median medium-case latency ≤120 seconds

Failure of a hardware gate yields **Impractical on this hardware**, not a model-quality failure. Substitution requires a decision record and a distinct model profile. Local API cost is reported as $0; electricity is a separate dated estimate or `null`, never an invented zero.

## Public MVP

Static routes:

- `/`
- `/benchmarks/[family]`
- `/models/[slug]`
- `/compare`
- `/runs/[run-id]`
- `/methodology`
- `/custom-benchmark`

The site consumes only validated, versioned public JSON containing release metadata, task families, model profiles, aggregates, evidence manifests, pricing snapshot IDs, and checksums. It includes privacy-safe analytics and a configurable hosted form endpoint. It includes no authentication, payments, subscriptions, public API, or application database.

## Delivery plan, effort, and gates

| Phase | Deliverable | Effort | Gate |
|------:|-------------|-------:|------|
| 0 | Documentation reconciliation | 2–4 days | Consistent docs and valid links |
| 1 | Local hardware and model validation | 2–4 days | TheImp and three local profiles verified/substituted |
| 2 | Python/SQLite/artifact foundation | 6–10 days | Migrations, resume, checksums, tests |
| 3 | 75 reviewed cases and scoring | 12–18 days | Two human passes; quotas; frozen suite |
| 4 | Adapters and 15-case pilot | 8–12 days | Contract/smoke/pilot tests pass |
| 5 | Stable batch and routing simulation | 2–5 active days plus runtime | Reproducible evidence release |
| 6 | Static public site | 8–12 days | Build, route, accessibility, redaction, link tests |
| 7 | Validation launch | 3–6 active days plus 30–45 days | Continue/pivot/stop evidence |

Total: **43–71 ideal engineering days**, excluding reviewer availability, machine runtime, and validation observation. Detailed phase dependencies, costs, stop conditions, and out-of-scope items are in [roadmap.md](../roadmap.md).

## Cost plan

| Cost | Amount | Confidence / treatment |
|------|-------:|------------------------|
| Planning work incurred | **$0** | Known |
| Cloud model calls | Deferred; previously budgeted at **$0–$25 total** | Cloud-only guardrail evaluated when cloud adapters begin; exact amount requires approval context, dated prices, and token pilot |
| Static hosting and analytics | **$0 assumed** | Free-tier assumption; paid upgrade requires approval |
| Domain registration | Unverified | Excluded from cloud cap |
| Electricity | Unverified | Separate dated estimate or `null` |
| Reviewer labor | Unverified | Excluded from cloud cap and engineering-day estimate |
| Hosted form provider | Unverified / expected free tier | Paid plan requires approval |

No paid call begins until a pricing snapshot and full-batch projection are recorded.

## Acceptance criteria

MVP product completion requires:

- Six exact surfaces tested or documented substitutions
- 75 approved cases and 1,350 planned runs
- Three independent repetitions per model/case
- At least 90% valid planned runs per publishable model/family cell
- Provenance on at least 95% of valid runs
- Evidence traceability and reproducible redacted exports
- At least one published escalation simulation
- Static public routes, methodology, comparison, and evidence pages validated

### Required verification matrix

| Area | Required checks |
|------|-----------------|
| Cases and scoring | Case/quota validation, strict parsing, JSON Schema, normalization, classification, hallucination/forbidden-invention rules, aggregation, verdict precedence, pricing, and routing formulas |
| Adapters | Success, malformed output, timeout, 429, provider 5xx, authentication, missing token counts, returned surface identity, and raw-evidence preservation |
| Persistence and reproduction | SQLite migrations, interrupted-batch resume, planned-run idempotency, artifact immutability/checksum, public-export redaction/schema, and batch reproduction |
| End to end | Golden scoring fixtures and one fake-provider batch from cases through public JSON |
| Human quality control | At least three scored runs per model/family cell, every critical invention, every override, and every representative published failure |
| Static site | Next.js build, public-export schema validation, Playwright routes/comparison, responsive behavior, accessibility, redaction, and broken links |

All money tests use deterministic decimal-safe arithmetic. No command or check is reported as passing unless it was actually executed.

Audience validation within 30–45 days requires:

- 100 qualified visitors
- 10 meaningful comparison users
- Five workflow submissions
- One willingness-to-pay signal
- Three users reporting a changed or confirmed model decision

## Monetization test

The first offer is a manually qualified private benchmark report. The public site collects the workflow type, representative-example count, target schema/categories, monthly volume, latency tolerance, local/cloud preference, structured-output requirement, privacy flag, and contact details. The founder responds within three business days with fit, required sanitization, scope, price, and delivery estimate.

Payment integration is deferred. The first accepted job uses manual invoicing. Existing package prices remain hypotheses, not forecasts. See [MONETIZATION_AND_VALIDATION.md](MONETIZATION_AND_VALIDATION.md).

## Highest risks and stop gates

TheImp was inspected directly on 2026-07-31. Qwen 3.5 9B and Llama 3.1 8B passed the fixed hardware thresholds on its RTX 3060, but a credible three-local-model set is not yet frozen: Ollama 0.17.4 cannot pull Gemma 4 12B, and structured-output runtime defects were observed. The local phase is blocked pending approval to upgrade Ollama and rerun all three profiles on one runtime.

Other major risks are corpus realism, deterministic scorer defects, prompt sensitivity, provider/model churn, exact-surface ambiguity, founder/reviewer capacity, and lack of customer demand. The register and mitigations live in [RISKS_AND_ASSUMPTIONS.md](RISKS_AND_ASSUMPTIONS.md).

Stop:

- Before local implementation if TheImp or local launch identities cannot be verified
- Before paid cloud calls if cloud pricing/identity is unverified or the approved cloud-only guardrail would be exceeded
- Before stable runs if two-pass case review, prompts, thresholds, prices, profiles, or scorer version are unfrozen
- Before publication if provenance, redaction, surface separation, evidence traceability, or critical scoring correctness fails
- After launch according to the documented 30–45 day validation criteria

## Immediate next five actions

1. Approve an Ollama upgrade on TheImp and, if practical, reconcile its NVIDIA driver/library mismatch.
2. Pull exact `gemma4:12b` and rerun Qwen, Gemma, and Llama through the fixed probes on the same upgraded runtime.
3. If Gemma still fails, approve and record a distinct smaller-Gemma substitution; otherwise freeze the three local profiles.
4. Begin the Python/SQLite/artifact foundation and Ollama adapter.
5. Build the reviewed pilot corpus and deterministic scorers, then run the local pilot before any cloud work.

## Requirement crosswalk from `initialprompt.md`

`initialprompt.md` remains unchanged historical source material. This table maps its requirement areas to the current canonical documents; the master plan does not duplicate their full specifications.

| Original requirement area | Current source of truth | Resolution |
|---------------------------|-------------------------|------------|
| Product thesis, audience, practical questions | [MVP_SCOPE.md](MVP_SCOPE.md), [PRODUCT_BRIEF.md](PRODUCT_BRIEF.md) | Narrow automation-builder question retained |
| Current constraints and machine inspection | [MODEL_LAUNCH_SET.md](MODEL_LAUNCH_SET.md), [RISKS_AND_ASSUMPTIONS.md](RISKS_AND_ASSUMPTIONS.md), [PROJECT_STATE.md](PROJECT_STATE.md) | X1-Carbon observation separated; TheImp required in Phase 1 |
| Initial local and cloud launch set | [MODEL_LAUNCH_SET.md](MODEL_LAUNCH_SET.md) | Six target surfaces approved subject to verification/substitution gate |
| Exact vs opaque model identity | [BENCHMARK_SPEC.md](BENCHMARK_SPEC.md), [PROVENANCE_AND_REPRODUCIBILITY.md](PROVENANCE_AND_REPRODUCIBILITY.md) | Strict separation approved |
| Three task families and exclusions | [MVP_SCOPE.md](MVP_SCOPE.md), [BENCHMARK_SPEC.md](BENCHMARK_SPEC.md) | Three-family scope approved |
| 75-case corpus and 1,350 runs | [MVP_SCOPE.md](MVP_SCOPE.md), [BENCHMARK_SPEC.md](BENCHMARK_SPEC.md) | Former roadmap conflict superseded |
| Case format and versioning | [BENCHMARK_SPEC.md](BENCHMARK_SPEC.md), [templates/BENCHMARK_CASE_TEMPLATE.yaml](templates/BENCHMARK_CASE_TEMPLATE.yaml), [DATA_MODEL.md](DATA_MODEL.md) | Versioned YAML plus frozen suite |
| Prompting controls | [BENCHMARK_SPEC.md](BENCHMARK_SPEC.md), [EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md) | Common prompt; differences recorded |
| Integrity, accuracy, trust, reliability, performance, economics | [SCORING_AND_EVALUATION.md](SCORING_AND_EVALUATION.md) | Deterministic formulas and fixed gates |
| Pass/fail and five verdict labels | [SCORING_AND_EVALUATION.md](SCORING_AND_EVALUATION.md) | Exact thresholds approved |
| Offline escalation simulation | [SCORING_AND_EVALUATION.md](SCORING_AND_EVALUATION.md), [DATA_MODEL.md](DATA_MODEL.md) | Required; live router deferred |
| Provider-neutral runner and adapters | [ARCHITECTURE.md](ARCHITECTURE.md), [EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md) | Async adapter boundary; collection separate from scoring |
| Minimal technical architecture comparison | [ARCHITECTURE.md](ARCHITECTURE.md), [DECISION_LOG.md](DECISION_LOG.md) | Local-first option approved; Supabase option deferred |
| Public pages and product requirements | [MVP_SCOPE.md](MVP_SCOPE.md), [ARCHITECTURE.md](ARCHITECTURE.md) | Static evidence-first routes approved |
| Reproducibility and provenance | [PROVENANCE_AND_REPRODUCIBILITY.md](PROVENANCE_AND_REPRODUCIBILITY.md), [EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md) | Immutable evidence and checksums required |
| Security, privacy, retention, licensing | [ARCHITECTURE.md](ARCHITECTURE.md), [PROVENANCE_AND_REPRODUCIBILITY.md](PROVENANCE_AND_REPRODUCIBILITY.md), [RISKS_AND_ASSUMPTIONS.md](RISKS_AND_ASSUMPTIONS.md) | Public/private separation and redaction gates retained |
| Automated quality control and human review | [EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md), [BENCHMARK_SPEC.md](BENCHMARK_SPEC.md), [roadmap.md](../roadmap.md) | Two case passes plus fixed run spot-check policy |
| Phased implementation plan | [roadmap.md](../roadmap.md) | Replaced conflicting vision text with Phases 0–7 |
| Product and audience success criteria | [MVP_SCOPE.md](MVP_SCOPE.md), [MONETIZATION_AND_VALIDATION.md](MONETIZATION_AND_VALIDATION.md) | Product and 30–45 day gates frozen |
| Expansion ideas and IronWork connection | [MVP_SCOPE.md](MVP_SCOPE.md), [PRODUCT_BRIEF.md](PRODUCT_BRIEF.md) | Explicitly deferred |
| Required planning documents | [index.md](../index.md) | Existing canonical files retained; only missing master plan added |
| Decisions, risks, costs, unknowns, next actions | [DECISION_LOG.md](DECISION_LOG.md), [RISKS_AND_ASSUMPTIONS.md](RISKS_AND_ASSUMPTIONS.md), [PROJECT_STATE.md](PROJECT_STATE.md), this plan | Closed decisions distinguished from external unknowns |

### Historical requested-name reconciliation

The original brief requested several names that would duplicate current canonical documents. No aliases are created:

| Historical requested name | Canonical document |
|---------------------------|-------------------|
| `docs/PRODUCT_SCOPE.md` | [MVP_SCOPE.md](MVP_SCOPE.md) + [PRODUCT_BRIEF.md](PRODUCT_BRIEF.md) |
| `docs/SCORING_SPEC.md` | [SCORING_AND_EVALUATION.md](SCORING_AND_EVALUATION.md) |
| `docs/IMPLEMENTATION_ROADMAP.md` | [roadmap.md](../roadmap.md) |
| `docs/MONETIZATION_VALIDATION.md` | [MONETIZATION_AND_VALIDATION.md](MONETIZATION_AND_VALIDATION.md) |

## Facts still unverified

- Gemma 4 12B identity and performance on TheImp; Qwen/Llama behavior after the required runtime upgrade
- Account/API access, rate limits, pinned snapshots, and current dated prices
- Exact Gemma digest and context settings on TheImp
- Full-batch token volume, duration, and electricity use
- Domain, hosted-form, reviewer-labor, and optional service costs
- Whether the six target profiles all pass smoke and viability gates

The local facts are Phase 1 inputs. Cloud access and pricing facts are deferred cloud-adapter inputs under DEC-0013, not unresolved product-policy decisions or local-work gates.

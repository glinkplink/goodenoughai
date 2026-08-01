> **Status:** Approved
> **Authority:** Source of truth
> **Last reviewed:** 2026-07-31
> **Update when:** Scope expands, narrows, or acceptance criteria change
> **Related:** [PRODUCT_BRIEF.md](PRODUCT_BRIEF.md), [BENCHMARK_SPEC.md](BENCHMARK_SPEC.md), [roadmap.md](../roadmap.md), [DECISION_LOG.md](DECISION_LOG.md)

# MVP scope

Authoritative scope boundary. Any proposal that materially broadens the MVP must update this document **and** create a [DECISION_LOG.md](DECISION_LOG.md) entry.

## Exact MVP question

> **Which inexpensive AI model should an automation builder use for structured extraction, classification, and normalization?**

## Exact target audience

- n8n, Make, and Zapier users
- Python automation builders
- AI-agent developers
- Scraper and data-pipeline developers
- Solo developers and small agencies
- People deciding between local models and inexpensive cloud models

## Initial task families

Three tightly related families only:

### 1. Structured extraction

Messy source text → strict JSON matching a defined schema.

Examples: technician notes, customer emails, job listings, invoices, receipts, reviews, form submissions.

### 2. Classification and routing

Source text → category, label, or routing decision (including enums and multi-label where defined).

Examples: support-ticket category, customer intent, urgency, lead qualification, sentiment/severity, safe vs unsafe automation action.

### 3. Structured normalization

Inconsistent or partial records → clean JSON in a target schema without invented fields.

Examples: unit normalization, date ISO formatting, controlled taxonomy mapping, duplicate detection flags, enum coercion.

**Explicitly excluded from MVP task families:** general knowledge Q&A, creative writing, abstract math, broad coding benchmarks, long-form research, image generation, roleplay, Linux troubleshooting suites, agent tool-use reliability suites.

## Initial corpus target

| Parameter | Value |
|-----------|-------|
| Total cases | **75** |
| Per task family | **25** each |
| Repetitions per case per model | **3** |
| Initial model count | **6** (3 local + 3 cloud) |
| Expected initial run volume | **1,350** (75 × 6 × 3) |

Corpus requirements (see [BENCHMARK_SPEC.md](BENCHMARK_SPEC.md)):

- Deterministic ground truth for most scoring
- No private customer data
- Realistic synthetic examples varying length, ambiguity, and formatting
- ≥15% hallucination-resistance cases (at least 12)
- ≥15% missing/ambiguous-information cases (at least 12; correct behavior may be `null`, `unknown`, or `needs_review`)
- ≥15% strict enum/schema-adherence cases (at least 12)
- Adversarial formatting and prompt-injection text inside source data
- No cases where subjective prose judgment is the primary score

The approved target is 75 cases across three families. The former roadmap proposal for 250 cases/five categories is superseded by DEC-0001 and removed from the living roadmap.

## Initial model-surface target

Six models for first benchmark batch — see [MODEL_LAUNCH_SET.md](MODEL_LAUNCH_SET.md):

**Local (exact):** Qwen 3.5 9B, Gemma 4 12B, Llama 3.1 8B via Ollama  
**Cloud (exact):** Gemini 3.5 Flash-Lite, DeepSeek V4 Flash, OpenAI GPT-5.6 Luna

Candidate identifiers are catalog-confirmed, but access, exact returned identity, dated pricing, and TheImp viability remain unverified until Phase 1 validation.

Opaque consumer-web assistants remain a **separate surface** — never mixed into main leaderboard.

## Required public outputs

Minimum public MVP pages (implementation deferred):

| Page | Purpose |
|------|---------|
| Home | Core question, best-value highlights, methodology link, benchmark version |
| Task-family leaderboards | `/benchmarks/structured-extraction`, `/benchmarks/classification`, `/benchmarks/normalization` |
| Model detail | Per-model surface, hardware/provider, task results, failures, cost |
| Model comparison | Two–three models on one task family |
| Raw run evidence | Traceable case, prompt, raw response, score breakdown, metadata |
| Methodology | Case design, scoring, repetitions, web-vs-API separation, pricing dates |
| Custom benchmark interest | Intake form for paid custom evaluations (no payment integration in first engineering phase) |

## Required metrics

Multidimensional scorecard per model-task combination — not one universal score.

**Integrity:** JSON parse success, schema validity, required-field completion, unexpected-field rate, enum compliance  
**Accuracy:** exact/normalized field accuracy, precision, recall, F1, classification accuracy  
**Trustworthiness:** unsupported-field rate, hallucinated-value rate, appropriate-null rate  
**Reliability:** pass rate, consistency across repetitions, malformed-output rate, timeout rate, provider-error rate  
**Performance:** latency, tokens, local throughput/RAM where applicable  
**Economics:** cost per attempt, **cost per accepted result**, escalation simulation

Full formulas: [SCORING_AND_EVALUATION.md](SCORING_AND_EVALUATION.md).

## Verdict labels

Each model-task combination receives one label:

- **Reliable**
- **Usable with validation**
- **Escalation recommended**
- **Not suitable**
- **Insufficient data**

## MVP acceptance criteria

### Product completion

- [ ] Six model surfaces tested, or documented substitution justification
- [ ] 75 validated benchmark cases with author review and independent reviewer sign-off, frozen as `automation-mvp-v0.1.0`
- [ ] 3 repetitions per model-case combination completed for valid batch
- [ ] Full provenance for ≥95% of valid runs
- [ ] Public pages traceable to raw evidence
- [ ] Reproducible local reruns documented
- [ ] Escalation simulation results published for at least one task family

### Audience validation (30–45 days post-launch)

- [ ] ≥100 qualified visitors from automation communities
- [ ] ≥10 meaningful comparison-view users
- [ ] ≥5 workflow submissions or comparison requests
- [ ] ≥1 willingness to pay for custom benchmark
- [ ] ≥3 users report changed or confirmed model decision

See [MONETIZATION_AND_VALIDATION.md](MONETIZATION_AND_VALIDATION.md) for kill criteria.

## In scope

- Deterministic scoring as primary evaluation
- Provider-neutral benchmark runner (Python) with Ollama + cloud adapters
- Manual and AutoGemini JSONL import path (separate surface labeling)
- Pricing snapshots with effective dates (not hardcoded in scorer)
- TheImp as local benchmark worker
- SQLite with tracked migrations and immutable filesystem artifacts
- Versioned redacted public JSON as the publishing interface
- Statically exported TypeScript Next.js public application
- Custom benchmark offer planning (no payment integration through the public-site build)
- Escalation routing simulation (offline, not live router)

## Out of scope

- Universal intelligence leaderboard
- General knowledge, creative writing, coding leaderboards, multimodal benchmarks
- Community voting as primary grader
- LLM-as-judge as authoritative scorer for central metrics
- Live production model router
- Browser automation as trusted core runner
- Ads monetization at launch
- Sponsored rankings that alter methodology
- Payment/checkout integration in initial engineering phases
- Supabase/PostgreSQL, authentication, Redis, remote workers, and a runtime application database
- IronWork-specific public benchmark pack (deferred)
- Linux troubleshooting, coding microtasks, agent-reliability categories (deferred — see `roadmap.md` expansion ideas)

## Deferred features

Post-MVP expansion candidates (design for, do not build):

- Claude Haiku 4.5 and additional model sizes
- IronWork contractor-operations benchmark pack
- Linux troubleshooting suite
- Coding microtasks
- Workflow cost calculator UI
- Historical model-drift tracking and alerts
- Benchmark API and n8n workflow export
- Community benchmark contributions
- GPU/VPS remote workers
- Pro subscription and Builder tier

## Scope-change process

1. Propose change with rationale and impact on corpus, runner, and timeline
2. Update this document
3. Add entry to [DECISION_LOG.md](DECISION_LOG.md) with status **Approved** (requires explicit user approval)
4. Update [RISKS_AND_ASSUMPTIONS.md](RISKS_AND_ASSUMPTIONS.md) if new risks introduced
5. Update [CHANGELOG.md](CHANGELOG.md)

## Related documents

- [PRODUCT_BRIEF.md](PRODUCT_BRIEF.md) — strategic context
- [BENCHMARK_SPEC.md](BENCHMARK_SPEC.md) — corpus and methodology detail
- [MODEL_LAUNCH_SET.md](MODEL_LAUNCH_SET.md) — initial models
- [SCORING_AND_EVALUATION.md](SCORING_AND_EVALUATION.md) — metrics and thresholds
- [roadmap.md](../roadmap.md) — phased delivery
- [DECISION_LOG.md](DECISION_LOG.md) — scope decisions

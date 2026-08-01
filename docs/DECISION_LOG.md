> **Status:** Active  
> **Authority:** Source of truth for approved decisions  
> **Last reviewed:** 2026-07-31  
> **Update when:** A decision is approved, superseded, rejected, or materially revised  
> **Related:** [MVP_MASTER_PLAN.md](MVP_MASTER_PLAN.md), [MVP_SCOPE.md](MVP_SCOPE.md), [ARCHITECTURE.md](ARCHITECTURE.md), [RISKS_AND_ASSUMPTIONS.md](RISKS_AND_ASSUMPTIONS.md)

# Decision log

Newer approved decisions supersede older planning text. Model availability, credentials, prices, and hardware measurements are facts to verify, not decisions.

## DEC-0001 — MVP corpus: 75 cases across three families

- **Status:** Approved
- **Date:** 2026-07-31
- **Context:** `initialprompt.md` specified 75 cases while an older roadmap section proposed 250 across five categories.
- **Options considered:** 75/3; 250/5; 75 now with later expansion.
- **Chosen option:** 75 cases—25 each for extraction, classification/routing, and normalization—with broader categories deferred.
- **Reason:** Preserves the narrow MVP and yields 1,350 planned runs at six surfaces × three repetitions.
- **Consequences:** The 250-case/five-category text is removed from the living roadmap. Corpus quotas and acceptance use 75.
- **Revisit trigger:** Post-MVP validation demonstrates a specific additional family or larger suite is needed.

## DEC-0002 — Defer benchmark families beyond the three structured-task families

- **Status:** Approved
- **Date:** 2026-07-31
- **Context:** Historical planning included troubleshooting, coding, agent reliability, transformation, small-business, and multimodal work.
- **Options considered:** Broad launch; three-family launch.
- **Chosen option:** Three-family launch only.
- **Reason:** Faster credible delivery and deterministic scoring for the exact audience question.
- **Consequences:** Linux, coding, agent, IronWork, creative, research, and multimodal suites remain deferred.
- **Revisit trigger:** The initial benchmark meets validation criteria and a scoped expansion is approved.

## DEC-0003 — Deterministic scoring is authoritative

- **Status:** Approved
- **Date:** 2026-07-31
- **Context:** Structured automation tasks have schemas and explicit ground truth; LLM judges add cost and bias.
- **Options considered:** Deterministic primary; LLM judge co-primary; human primary.
- **Chosen option:** Deterministic scoring controls central pass/fail and verdicts. LLM judging is secondary only if added later.
- **Reason:** Reproducibility, low cost, and auditability.
- **Consequences:** Golden fixtures and deterministic money/scoring tests are release gates.
- **Revisit trigger:** A future approved task family cannot be evaluated credibly with deterministic or direct human rules.

## DEC-0004 — Exact model surfaces and opaque consumer assistants remain separate

- **Status:** Approved
- **Date:** 2026-07-31
- **Context:** Web assistants can have unknown routing, prompts, tools, and underlying models.
- **Options considered:** Strict separation; combined scores with disclosure.
- **Chosen option:** Only eligible exact API/local profiles enter the main leaderboard; web/import profiles use separate sections.
- **Reason:** Surface identity is foundational to benchmark credibility.
- **Consequences:** Direct provider, OpenRouter, CLI, web, and manual-import profiles never silently merge.
- **Revisit trigger:** None for opaque versus exact separation; CLI eligibility may receive a separate equivalence decision.

## DEC-0005 — Cost per accepted result is the primary economic metric

- **Status:** Approved
- **Date:** 2026-07-31
- **Context:** Token price alone ignores operational failure.
- **Options considered:** Cost per accepted result plus routing; token price only; blended value score.
- **Chosen option:** Publish cost per attempt, cost per accepted result, and offline routed-workflow economics.
- **Reason:** Directly answers the product’s model-selection question.
- **Consequences:** Dated pricing snapshots are required and prices never live in scoring logic.
- **Revisit trigger:** None for the core metric; workload models may expand after validation.

## DEC-0006 — Q4_K_M default and explicit local viability gates

- **Status:** Approved
- **Date:** 2026-07-31
- **Context:** Local comparisons require comparable quantization and a distinction between quality and hardware practicality.
- **Options considered:** Q4_K_M standard; provider defaults; multiple quantizations per model.
- **Chosen option:** Prefer Q4_K_M. A documented comparable equivalent gets a distinct profile. Viability requires no OOM, ≥1 GiB headroom, ≥2 output tokens/second median warm throughput, and ≤120-second median medium-case latency.
- **Reason:** Comparable, ordinary-hardware evidence without silently favoring one model.
- **Consequences:** Hardware-gate failure is labeled “Impractical on this hardware,” not a quality failure.
- **Revisit trigger:** TheImp measurements show a gate is systematically inappropriate; any change occurs before stable model runs.

## DEC-0007 — Six exact launch candidates

- **Status:** Approved
- **Date:** 2026-07-31
- **Context:** The first batch needs useful local/cloud diversity while staying narrow and inexpensive.
- **Options considered:** Six specified candidates; four candidates; add Claude immediately.
- **Chosen option:** Target Qwen 3.5 9B, Gemma 4 12B, Llama 3.1 8B, Gemini 3.5 Flash-Lite, direct DeepSeek V4 Flash, and GPT-5.6 Luna.
- **Reason:** Three local plus three inexpensive cloud ecosystems provide a credible first comparison.
- **Consequences:** Catalog identity is confirmed, but Phase 1 must verify access, exact profiles, prices, and viability. Failed candidates require documented substitutions. Claude is deferred.
- **Revisit trigger:** A candidate fails identity, access, hardware, or $25 budget gates.

## DEC-0008 — Local-first modular monolith architecture

- **Status:** Approved; supersedes the earlier proposed Supabase architecture
- **Date:** 2026-07-31
- **Context:** The MVP is a finite, solo-operated benchmark and static evidence product. A managed application backend adds work before demand exists.
- **Options considered:** Python/SQLite/filesystem/public JSON/static Next.js; Python/Supabase/dynamic Next.js; Redis/distributed workers; serverless runner.
- **Chosen option:** Python 3.10+, SQLite with tracked migrations, immutable filesystem artifacts, versioned public JSON, and statically exported TypeScript Next.js on Cloudflare Pages by default.
- **Reason:** Lowest operating cost, fastest reproducible build, and clean publication boundary.
- **Consequences:** Supabase/PostgreSQL, auth, Redis, payments, runtime database, and remote workers are deferred. Repository and artifact interfaces preserve later migration.
- **Revisit trigger:** Multiple concurrent operators, remote workers, paid authenticated projects, or artifact scale require a managed backend.

## DEC-0009 — Public benchmark before payment integration

- **Status:** Approved
- **Date:** 2026-07-31
- **Context:** Demand is unvalidated and custom reports can be sold manually.
- **Options considered:** Public benchmark plus manual invoicing; payment integration during site build.
- **Chosen option:** Build the public benchmark first; use manual qualification and invoicing for the first paid report.
- **Reason:** Tests willingness to pay without checkout/account complexity.
- **Consequences:** The custom page is a hosted-form intake only; no payments or accounts.
- **Revisit trigger:** A qualified customer accepts a paid engagement and repeated demand justifies automation.

## DEC-0010 — Documentation reconciliation precedes implementation

- **Status:** Approved
- **Date:** 2026-07-31
- **Context:** The historical brief and initial documents contained conflicting targets and unresolved policy choices.
- **Options considered:** Reconcile first; begin coding against unresolved documents.
- **Chosen option:** Complete the documentation audit and master plan before production code.
- **Reason:** Prevents architecture, corpus, and scoring rework.
- **Consequences:** `initialprompt.md` remains historical and unchanged; living documents govern implementation.
- **Revisit trigger:** None; completed.

## DEC-0011 — Two human passes on every benchmark case

- **Status:** Approved
- **Date:** 2026-07-31
- **Context:** Ground-truth defects would contaminate deterministic scores across all models.
- **Options considered:** Author-only review; sampled second review; independent second review for every case.
- **Chosen option:** The author completes a structured self-review and a different reviewer approves every current case version before freeze.
- **Reason:** The corpus is small enough for full review and central to public trust.
- **Consequences:** Case metadata stores both review outcomes; material expected-output changes invalidate both approvals until repeated.
- **Revisit trigger:** None for the 75-case MVP.

## DEC-0012 — Fixed collection, parsing, and manual run-review defaults

- **Status:** Approved
- **Date:** 2026-07-31
- **Context:** Timeout, order, JSON repair, and spot-check policies were undecided.
- **Options considered:** Provider-specific ad hoc policy; fixed documented defaults.
- **Chosen option:** Native strict schema mode where supported; reasoning disabled/minimized; 120-second local and 60-second cloud timeouts; three transient retries; one local warmup; one model at a time; seeded case order in separate repetition rounds; partial/fenced/repaired JSON fails parse scoring.
- **Reason:** Comparable, reproducible collection that preserves original evidence.
- **Consequences:** Review at least three scored runs per model/family cell (54 base), plus every critical invention, override, and published representative failure.
- **Revisit trigger:** Pilot evidence reveals a provider incompatibility; changes occur before stable suite runs and create a new protocol version.

## DEC-0013 — Cloud-only spending guardrail does not gate local work

- **Status:** Approved
- **Date:** 2026-07-31
- **Context:** The project starts with local models. An earlier plan made a $25 cloud projection a gate before runner implementation, which incorrectly allowed deferred cloud work to block local progress.
- **Options considered:** Keep the global pre-implementation gate; remove all cloud spending controls; apply a cloud-only guardrail immediately before cloud calls.
- **Chosen option:** Local implementation, corpus work, scoring, and local batches proceed without any cloud-budget gate. Before paid cloud calls, capture dated prices and a cloud-only estimate; the spending limit or approval is decided in that cloud-work context.
- **Reason:** No API spending occurs during local work, so cloud budget is irrelevant to local feasibility and sequencing.
- **Consequences:** Phase 1 is local-only. Cloud identity, pricing, and budget validation move to the cloud-adapter phase. A cloud cost issue pauses only cloud calls.
- **Revisit trigger:** Cloud adapter work is ready to start or the user changes the launch sequence.

## DEC-0014 — Static public application and form-only intake

- **Status:** Approved
- **Date:** 2026-07-31
- **Context:** Public evidence pages need cheap hosting but not mutable server state.
- **Options considered:** Static export; dynamic SSR/ISR over database; full account application.
- **Chosen option:** Next.js static export consumes only versioned public JSON and deploys to Cloudflare Pages by default. Intake posts to a configurable hosted form endpoint; analytics are privacy-safe.
- **Reason:** Minimal cost and attack surface with reproducible published data.
- **Consequences:** No backend database, auth, payment, subscription, or public API in MVP.
- **Revisit trigger:** Validated user need requires server-side state.

## DEC-0015 — Pilot strategy instead of a separate hidden holdout

- **Status:** Approved
- **Date:** 2026-07-31
- **Context:** A hidden holdout would reduce the already small public corpus and weaken reproducibility, while running all 75 before validation risks expensive benchmark defects.
- **Options considered:** Separate hidden holdout; no pilot; designated 15-case pilot subset within the 75.
- **Chosen option:** Designate a balanced 15-case pilot subset, fix defects under versioning, then freeze all 75 as `automation-mvp-v0.1.0`. No separate hidden MVP holdout.
- **Reason:** Finds runner/scorer/case defects while keeping the public suite transparent.
- **Consequences:** Pilot outputs are not stable leaderboard results. Generalization is tested through later private/custom workflows and future suite versions.
- **Revisit trigger:** Post-MVP maintenance introduces private challenge sets with explicit governance.

## DEC-0016 — Custom-benchmark intake and response policy

- **Status:** Approved
- **Date:** 2026-07-31
- **Context:** The intake fields and service response expectation were unspecified.
- **Options considered:** Minimal contact form; structured qualification form; account-based project intake.
- **Chosen option:** Hosted form collects task type, example count, target schema/categories, monthly volume, latency tolerance, local/cloud preference, structured-output requirement, sensitive-data flag, and contact details. Respond within three business days with fit, sanitization needs, scope, price, and delivery estimate.
- **Reason:** Enough information to qualify work without storing private examples on the public site.
- **Consequences:** Actual sensitive examples are requested only after manual qualification and agreed handling/deletion terms.
- **Revisit trigger:** Lead volume or first paid project shows different qualification needs.

## DEC-0017 — Default private-data limits and deletion

- **Status:** Approved
- **Date:** 2026-07-31
- **Context:** Custom benchmark leads may contain private or sensitive workflow data, but the static public site should not become a file store.
- **Options considered:** Upload through public form; manual qualified transfer with indefinite retention; manual qualified transfer with limits and default deletion.
- **Chosen option:** Public intake accepts metadata only. Qualified private transfers default to 10 MiB total, remain isolated, and are deleted with raw outputs/operational copies within 30 calendar days after final delivery or earlier withdrawal unless a written engagement specifies otherwise.
- **Reason:** Data minimization and a concrete, auditable default without building authentication/storage infrastructure.
- **Consequences:** Provider retention terms are disclosed before calls; deletion status is recorded; public reuse requires explicit written permission.
- **Revisit trigger:** Legal advice, provider requirements, or a written customer agreement requires a different policy.

## DEC-0018 — Tiered documentation loading for agents

- **Status:** Approved
- **Date:** 2026-07-31
- **Context:** The prior agent guidance required several broad planning documents before every substantial task, despite the repository having a task-routing index and a compact operational handoff. This added unnecessary context to bounded work and created inconsistent instructions between the Cursor bridge and `AGENTS.md`.
- **Options considered:** Keep the universal planning-document sequence; load only the project-state handoff; use durable constraints plus task-routed documentation.
- **Chosen option:** Agents read durable repository rules and the current project state for non-trivial work, then consult the Quick task routing section of `index.md` and load only the task's authoritative documents. The master plan, roadmap, and decision log are required for cross-cutting work, phase planning, priority changes, or ambiguity. Trivial strictly bounded edits require the rules and target file only unless their impact expands.
- **Reason:** Preserves scope and provenance safeguards while reducing irrelevant context and making the instructions consistent across agent surfaces.
- **Consequences:** `AGENTS.md`, the Cursor rule, and `index.md` use the same tiered policy. `initialprompt.md` remains historical and on-demand.
- **Revisit trigger:** Repeated agent errors show that a durable constraint or routing condition is being missed.

## Related documents

- [MVP_MASTER_PLAN.md](MVP_MASTER_PLAN.md)
- [MVP_SCOPE.md](MVP_SCOPE.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [RISKS_AND_ASSUMPTIONS.md](RISKS_AND_ASSUMPTIONS.md)
- [templates/DECISION_RECORD_TEMPLATE.md](templates/DECISION_RECORD_TEMPLATE.md)

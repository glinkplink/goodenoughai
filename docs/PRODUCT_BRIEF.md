> **Status:** Draft
> **Authority:** Supporting specification
> **Last reviewed:** 2026-08-01
> **Update when:** Product thesis, audience, or differentiation changes
> **Related:** [MVP_SCOPE.md](MVP_SCOPE.md), [MONETIZATION_AND_VALIDATION.md](MONETIZATION_AND_VALIDATION.md), [roadmap.md](../roadmap.md)

# Product brief — GoodEnough.ai

## Problem

Automation builders face a practical question that generic leaderboards do not answer well:

> *Which inexpensive model reliably completes **my specific production task** — and what does failure cost?*

Generic comparison sites optimize for broad quality, token price, latency, usage, or human preference. More direct products now benchmark structured extraction or route live requests, so the MVP must prove a narrower claim: whether exact local and cloud surfaces reliably satisfy defined automation contracts, what detectable failure costs, and when deterministic validation plus escalation is safe.

Builders using n8n, Make, Zapier, Python pipelines, and AI agents need to know:

- Does the model return valid structured output?
- Does it preserve source facts or invent unsupported information?
- How often does it fail, and what does failure look like?
- Can it run locally on ordinary hardware?
- Is cheap-model-plus-escalation cheaper than using a premium model for every request?

## Target audience

Initial audience (narrow):

- n8n, Make, and Zapier users
- Python automation and AI-agent developers
- Scraper and data-pipeline developers
- Solo developers and small agencies building repetitive AI workflows
- People deciding between local models and inexpensive cloud APIs

**Not** the initial audience: researchers seeking universal intelligence rankings, creative-writing users, or enterprise MLOps teams needing full observability platforms.

## Jobs to be done

1. **Choose a model** for a specific extraction, classification, or normalization task
2. **Understand failure modes** before putting a model in production
3. **Compare local vs cloud** on the same task with comparable evidence
4. **Calculate economics** — cost per attempt and cost per *accepted* result
5. **Design routing** — when deterministic validation and escalation beat premium-only processing
6. **Trust the evidence** — trace any public claim to raw prompts, responses, and scores

## Product thesis

Build a **practical model-selection database**, not another academic benchmark.

The valuable output is a recommendation like:

```text
Task: Convert messy field notes into an invoice-ready work summary

Best local: Qwen 9B — pass rate UNVERIFIED, marginal cost electricity only
Best cloud:  DeepSeek Flash — pass rate UNVERIFIED, cost per accepted result UNVERIFIED

Recommendation: Use local model for first pass; escalate invalid JSON or
missing critical fields to cloud model. Premium-only processing UNVERIFIED
as cost-effective for this workload.
```

*(Example structure only — no benchmark results exist yet.)*

## Existing alternatives

| Alternative | What it answers | Gap GoodEnough.ai fills |
|-------------|-----------------|-------------------------|
| Artificial Analysis | Broad quality, price, speed across hundreds of models | Not task-specific; no structured-output failure evidence |
| [Checkstack](https://checkstack.ai/compare) | Structured-extraction accuracy, task cost, raw outputs, and custom-dataset comparisons | GoodEnough must prove value across extraction, classification, and normalization with exact local/cloud provenance, cost per accepted result, and predeclared escalation economics |
| [LiteLLM Auto Routing](https://docs.litellm.ai/docs/proxy/auto_routing) and [RouteLLM](https://github.com/lm-sys/RouteLLM) | Live model selection using operational, heuristic, classifier, adaptive, or general-benchmark signals | Not evidence that a specific structured automation contract is safe on a tested surface |
| OpenRouter catalog/routing | Unified model access, metadata, and provider/model routing | Not deterministic reliability evidence for the project’s three task families |
| Hugging Face Open LLM Leaderboard | Academic benchmark scores | Not automation extraction/classification |
| Chatbot Arena | Human preference on open chat | Not production structured tasks |
| Provider docs / marketing | Best-case claims | No comparable failure data or cost-per-accepted-result |

This differentiation is a hypothesis, not a moat already proven. The Phase 4 pilot must test whether automation builders value a curated evidence database and recommendation report over an extraction-only benchmark, a generic router, or a tool that evaluates only their private workflow.

## Core differentiation

GoodEnough.ai answers:

- Which model **passes my task** (not which scores highest globally)
- What **failure looks like** (with raw evidence)
- Whether structured JSON is **actually valid**
- Whether source facts are **preserved**
- Whether the model **invents** unsupported fields or values
- **Cost per accepted result**, not just cost per token
- When **cheap + escalation** beats premium-only
- Whether a model runs on **ordinary local hardware**

## Why cost per accepted result matters

```text
cost_per_accepted_result = total_inference_cost / number_of_accepted_results
```

A model costing one-tenth as much but failing 30% of tasks may be **more expensive operationally** than a stronger model. For routed workflows:

```text
routed_workflow_cost = primary_model_cost + escalation_rate × escalation_model_cost
```

This is the central economic insight the MVP must demonstrate. See [SCORING_AND_EVALUATION.md](SCORING_AND_EVALUATION.md) for formulas.

## Why failure evidence matters

Anyone can query models and show successes. The moat is:

- Curated production-realistic task corpus with explicit ground truth
- Published **failure samples** and score breakdowns
- Longitudinal tracking of model and provider changes (deferred post-MVP)
- Reproducible prompts, versioning, and raw output retention

## Why exact model identity matters

Consumer web assistants (ChatGPT Free, free Gemini UI) are **different benchmark surfaces** from exact API models. System prompts, routing, tools, and rate limits differ. Mixing them destroys credibility.

Every run must record provider, surface, exact model ID when known, identity confidence, and source type. See [BENCHMARK_SPEC.md](BENCHMARK_SPEC.md) and [PROVENANCE_AND_REPRODUCIBILITY.md](PROVENANCE_AND_REPRODUCIBILITY.md).

## Long-term vision

A trusted database showing the **cheapest model that reliably completes specific business tasks**, including recommended fallback routing — expanded over time to industry-specific benchmark packs, historical drift tracking, API access, and workflow export.

Public database earns trust and search traffic; custom benchmarks, subscriptions, and API access generate revenue. See [MONETIZATION_AND_VALIDATION.md](MONETIZATION_AND_VALIDATION.md).

## Connection to Hermes

The founder's Hermes agent system already uses mixed-model routing (local Qwen, cheap cloud models, strong QA model). GoodEnough.ai is the empirical layer that answers:

- Which model should each agent use?
- Which tasks can run locally?
- Where does structured output break?
- What should each workflow cost?

The benchmark infrastructure supports informed Hermes configuration — not the reverse.

## Eventual IronWork benchmark pack

The public MVP is **not** contractor-specific, but the system should eventually support an **IronWork** pack:

- Field notes → structured work record
- Estimate → structured scope
- Customer message → intent and urgency
- Change request → approval classification
- Job record → invoice-ready summary
- Invoice → payment follow-up action
- Technician notes → labor and materials

IronWork-specific cases are **deferred**; MVP corpus uses generic automation scenarios. See [MVP_SCOPE.md](MVP_SCOPE.md).

## Explicit non-goals (MVP)

- Universal intelligence score or generic "best LLM" ranking
- General knowledge, creative writing, abstract mathematics
- Broad coding benchmark suites (full SWE-bench competition)
- Multimodal/image generation benchmarks
- Community voting as primary evaluation
- Enterprise observability platform
- Ads-driven business model at launch
- Sponsored rankings that alter scoring
- Mixing opaque web-assistant results with exact API/local results

## Related documents

- [MVP_SCOPE.md](MVP_SCOPE.md) — authoritative scope boundary
- [BENCHMARK_SPEC.md](BENCHMARK_SPEC.md) — what gets measured
- [MONETIZATION_AND_VALIDATION.md](MONETIZATION_AND_VALIDATION.md) — validation sequence
- [roadmap.md](../roadmap.md) — phased delivery
- [initialprompt.md](../initialprompt.md) — original founding specification (historical)

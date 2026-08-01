> **Document role:** Original founding specification (historical). Captures initial intent and detailed constraints.  
> **Not automatically current** — living docs and [docs/DECISION_LOG.md](docs/DECISION_LOG.md) supersede where approved.  
> **Navigation:** [index.md](index.md) · [AGENTS.md](AGENTS.md) · [docs/MVP_SCOPE.md](docs/MVP_SCOPE.md)

---

You are the principal product architect, benchmark engineer, data engineer, and technical product lead for a new public AI-model comparison product.

Your immediate task is to create a rigorous, implementation-ready MVP master plan.

Do not build the application yet.

You may create planning and specification documents inside the repository, but do not begin implementing production code, installing large dependencies, creating cloud infrastructure, or spending money.

# Product thesis

Build a public benchmark database that answers one question for one audience:

> Which inexpensive AI model should an automation builder use for structured extraction and classification?

The initial audience is:

* n8n users
* Make and Zapier users
* Python automation builders
* AI-agent developers
* scraper and data-pipeline developers
* solo developers
* small agencies building repetitive AI workflows
* people deciding whether a local model is good enough or whether they need a cloud model

This is not a universal intelligence leaderboard.

It must answer practical production questions:

* Does the model return valid structured output?
* Does it preserve the source facts?
* Does it omit required information?
* Does it invent unsupported information?
* How consistent is it across repeated runs?
* How fast is it?
* How much does each attempted result cost?
* How much does each accepted result cost?
* Is a cheap-model-plus-escalation workflow better than using a premium model for every request?
* Can the model run locally on ordinary hardware?
* What failures should users expect?

The eventual public product should help users find the cheapest model that is reliably good enough for their specific automation workload.

# Current constraints

The primary development machine and local benchmark worker is a Linux Mint server named TheImp.

Known facts:

* TheImp already runs local Qwen models around the 9B and 14B range.
* Ollama is available or is intended to be the initial local inference runtime.
* There is no large dedicated AI GPU available.
* Local tests must therefore focus on models that realistically run on TheImp.
* Cloud tests must initially use low-cost APIs, free API allowances, CLIs, OpenRouter routes, or manually imported web responses.
* The project cannot depend on expensive GPU rental during the MVP.
* The architecture must allow stronger local models and rented GPU workers to be added later without redesigning the system.
* The benchmark must remain credible despite the limited starting hardware.
* Development should be optimized for low operating cost and a fast public launch.

Before finalizing the plan, inspect the machine and repository where access is available.

Gather or request the equivalent of:

```bash
uname -a
lscpu
free -h
lsblk
lspci
nvidia-smi
ollama --version
ollama list
docker --version
node --version
python3 --version
git status
find . -maxdepth 3 -type f | sort
```

Do not assume a GPU exists.

Record:

* CPU
* logical and physical cores
* RAM
* swap
* GPU or lack of GPU
* available storage
* installed Ollama models
* current quantizations where visible
* current software versions
* observed limitations

If commands cannot be executed, list the unknowns explicitly instead of inventing answers.

# Initial model launch set

Treat these as candidates that must be verified before implementation.

## Local models

1. Qwen 3.5 9B
2. Gemma 4 12B
3. Llama 3.1 8B

Likely Ollama tags:

```text
qwen3.5:9b
gemma4:12b
llama3.1:8b
```

Verify exact tags and availability.

The plan must:

* Explain why each model belongs in the initial benchmark.
* Estimate whether TheImp can run an appropriate four-bit quantization.
* Establish a standardized quantization policy.
* Prefer comparable quantization levels such as Q4_K_M where available.
* Never silently compare radically different quantization quality levels.
* Record exact model file, quantization, runtime, context setting, memory use, and hardware.
* Define a minimum usable throughput threshold.
* Define what happens when a model runs successfully but is impractically slow.
* Include a fallback candidate if one of these models cannot run acceptably.
* Consider Qwen 3 14B or Gemma 3 4B only as explicit fallback or expansion candidates, not silent substitutions.

## Cloud models

1. Google Gemini 3.5 Flash-Lite
2. DeepSeek V4 Flash
3. OpenAI GPT-5.6 Luna

Expected identifiers to verify:

```text
gemini-3.5-flash-lite
deepseek/deepseek-v4-flash
gpt-5.6-luna
```

Use exact API model identifiers and pinned snapshots when providers support snapshots.

The plan must support:

* Google Gemini API or official CLI
* OpenRouter
* OpenAI Responses API
* Ollama
* Manual JSONL import
* Future direct provider adapters

Claude Haiku 4.5 should be identified as the first cloud expansion model, but it is not required for the first six-model benchmark.

# Critical model-identity rule

Never mix consumer web assistants with exact API models.

These are different benchmark surfaces:

```text
Exact model:
gpt-5.6-luna through the OpenAI API

Opaque assistant surface:
ChatGPT Free web experience
```

The same distinction applies to Gemini and Claude.

Every run must record:

* provider
* provider surface
* exact model ID when known
* displayed model name
* model-identity confidence
* API, CLI, local, or consumer-web source
* provider host
* model snapshot or alias
* run timestamp
* collection method

Required source types:

```text
local_exact
api_exact
cli_exact
web_declared
web_opaque
manual_import
```

Rules:

* `api_exact` and `local_exact` results may appear in the main production-model leaderboard.
* Consumer web results must appear in a separate “free assistant surfaces” section.
* Never label an opaque web response as an exact underlying model.
* Do not combine web and API results into one model score.
* Browser automation may be used to collect provisional experimental data, but it must not be the sole foundation of the benchmark.
* Design a clean import adapter for AutoGemini JSONL output.
* Do not make browser automation part of the trusted core benchmark runner.
* Record any system-prompt, routing, tool-access, and interface differences that may affect comparison.

# MVP benchmark scope

The MVP should evaluate inexpensive models on three tightly related production-task families.

## 1. Structured extraction

Examples:

* Messy technician notes into strict JSON
* Customer email into support-ticket fields
* Job listing into compensation and requirements
* Product description into normalized attributes
* Invoice text into invoice fields
* Review into complaint details
* Receipt text into an expense record
* Form submission into a CRM record

## 2. Classification and routing

Examples:

* Support-ticket category
* Customer intent
* Complaint category
* Urgency
* Lead qualification
* Invoice follow-up status
* Review sentiment and severity
* Record requiring human review
* Safe versus unsafe automation action

## 3. Structured normalization

Examples:

* Inconsistent customer records into one schema
* Technician notes into standardized work summaries
* Units into normalized units
* Dates into ISO format
* Product categories into a controlled taxonomy
* Duplicate or near-duplicate records
* Free text into valid enumerated values
* Messy source records into clean JSON without invented fields

Keep the benchmark narrow. Do not add:

* General knowledge
* creative writing
* abstract mathematics
* broad coding benchmarks
* long-form research
* image generation
* roleplay
* generic chatbot preference scoring
* a universal intelligence score

# Dataset size

Design an MVP corpus around:

```text
75 total benchmark cases
25 structured-extraction cases
25 classification-and-routing cases
25 structured-normalization cases
```

Each case should be run three times per model.

Initial expected volume:

```text
75 cases
× 6 models
× 3 repetitions
= 1,350 benchmark runs
```

The architecture must support increasing repetitions and adding cases later.

Design the corpus so that:

* Most scoring is deterministic.
* Ground truth is explicit.
* No private customer data is required.
* Synthetic examples remain realistic rather than cartoonishly simple.
* Examples vary in length, ambiguity, formatting, missing fields, and difficulty.
* Some records intentionally lack enough information.
* The correct model behavior is sometimes to return `null`, `unknown`, or `needs_review`.
* The corpus includes adversarial formatting and instruction-like text inside source data.
* Source text cannot override the benchmark system instructions.
* At least 15% of cases test hallucination resistance.
* At least 15% test missing or ambiguous information.
* At least 15% test strict enum or schema adherence.
* There are no cases where subjective prose judgment is the primary score.

Create a strategy for establishing and reviewing ground truth.

# Benchmark-case format

Design a versioned YAML or JSON format similar to:

```yaml
task_id: technician_notes_001
benchmark_version: 0.1.0
task_family: structured_extraction
difficulty: medium

input:
  text: |
    Arrived 8:15. Replaced bad patch cable on port 18.
    Used one 10-foot blue Cat6 cable. Link came back up.
    Left at 9:05. Customer asked about moving rack next week
    but no work was performed on that request.

output_schema:
  type: object
  required:
    - arrival_time
    - departure_time
    - work_performed
    - materials
    - future_request
  additionalProperties: false

expected:
  arrival_time: "08:15"
  departure_time: "09:05"
  work_performed:
    - "Replaced failed patch cable on port 18"
  materials:
    - description: "Blue Cat6 patch cable"
      quantity: 1
      length_ft: 10
  future_request:
    description: "Potential rack move next week"
    work_performed: false

acceptance_rules:
  allow_semantic_variants: true
  forbidden_inventions:
    - customer_name
    - cable_price
    - rack_move_completed
```

Specify how cases, schemas, expected results, and scorer versions are versioned.

# Prompting policy

Create a standardized prompting policy.

For each model, control as many variables as possible:

* same task instruction
* same source record
* same JSON schema
* same maximum output
* lowest practical randomness
* no tools
* no web search
* no retrieval
* no hidden external context
* no conversation history
* fresh request per case
* comparable reasoning settings where possible

Where providers do not expose identical controls, record the difference.

Do not pretend that provider parameters are equivalent when they are not.

Store:

* complete system prompt
* complete user prompt
* schema
* prompt hash
* provider parameters
* reasoning setting
* temperature or equivalent when supported
* maximum output tokens
* retry count
* rate-limit events

# Core metrics

The benchmark must prioritize production reliability.

Define formulas and implementation details for:

## Output integrity

* JSON parse success
* schema-valid output rate
* required-field completion
* unexpected-field rate
* enum compliance
* type correctness

## Accuracy

* exact field accuracy
* normalized field accuracy
* precision
* recall
* F1
* classification accuracy
* false-positive rate
* false-negative rate
* omission rate

## Trustworthiness

* unsupported-field rate
* hallucinated-value rate
* source-number preservation
* source-date preservation
* appropriate-null rate
* refusal rate
* false-confidence rate

## Reliability

* pass rate
* consistency across three runs
* variance by case
* malformed-output rate
* timeout rate
* provider-error rate

## Performance

* time to first token when available
* total latency
* output tokens
* input tokens
* tokens per second for local models
* peak RAM
* average RAM
* CPU utilization
* GPU utilization where applicable

## Economics

* input cost
* output cost
* total attempt cost
* accepted-output cost
* effective cost per 1,000 accepted results
* estimated monthly cost at several workload sizes
* escalation cost

The most important economic metric is:

```text
cost_per_accepted_result =
total_cost_for_all_attempts / number_of_accepted_results
```

For routed workflows:

```text
routed_workflow_cost =
primary_model_cost
+ primary_failure_or_uncertainty_rate × escalation_model_cost
```

All prices must be:

* associated with an effective date
* associated with a provider
* stored separately from benchmark run records
* updateable without rewriting historical results
* preserved historically
* clearly labeled when inferred or unavailable

Never hardcode pricing into scoring logic.

# Pass/fail policy

Design task-level acceptance thresholds.

Example:

```text
JSON valid: required
Schema valid: required
Required-field recall: at least 95%
Unsupported-field rate: no more than 1%
Critical-field accuracy: 100%
Overall normalized field accuracy: at least 95%
```

Thresholds may differ by task, but they must be explicit before running models.

Each model-task combination should receive one of these labels:

```text
Reliable
Usable with validation
Escalation recommended
Not suitable
Insufficient data
```

Do not create one meaningless universal score.

Show a multidimensional scorecard and task-specific verdict.

# Escalation simulation

The MVP must demonstrate the central product insight:

> A cheap model plus deterministic validation and selective escalation may outperform using an expensive model for every request.

Plan an offline routing simulation.

Examples of escalation triggers:

* invalid JSON
* schema failure
* missing critical field
* unsupported field
* low classification margin
* model-produced `needs_review`
* disagreement across repeated calls
* deterministic validation failure

Calculate:

* percentage handled by primary model
* escalation percentage
* final estimated pass rate
* total blended cost
* cost compared with premium-only processing
* latency tradeoff

The MVP does not need a live production router, but the data model and benchmark results must support the simulation.

# Required adapters

Plan a provider-neutral runner interface.

Suggested conceptual interface:

```python
class ModelAdapter:
    def run(self, request: BenchmarkRequest) -> BenchmarkResponse:
        ...
```

Initial adapters:

```text
OllamaAdapter
GeminiAdapter
OpenAIAdapter
OpenRouterAdapter
ManualImportAdapter
AutoGeminiImportAdapter
```

A normalized response must include:

```text
run_id
case_id
model_id
provider
provider_surface
source_type
model_identity_confidence
started_at
first_token_at
completed_at
latency_ms
input_tokens
output_tokens
raw_response
parsed_response
error_type
error_message
retry_count
estimated_cost
runtime_metadata
hardware_metadata
prompt_hash
scorer_version
```

Separate collection, parsing, scoring, and reporting.

A provider failure must not be scored as an incorrect model answer. Report availability and quality separately.

# Proposed technical architecture

Evaluate and recommend a minimal architecture.

Initial preference:

```text
Benchmark runner: Python
Local inference: Ollama
Public web app: Next.js
Database: PostgreSQL or Supabase
Local development: Docker Compose where useful
Artifacts/raw responses: local filesystem initially, object storage later
Charts: simple server-rendered or client charts
Hosting: inexpensive managed frontend and database
TheImp: local benchmark worker
```

Do not blindly accept this stack.

Compare at least two reasonable approaches and choose one based on:

* lowest operational cost
* fastest MVP build
* reproducibility
* ease of local development
* future public API support
* model-run volume
* easy schema migrations
* ability to add remote workers
* ease of publishing raw evidence
* maintainability by one developer

Avoid unnecessary microservices.

# Public MVP pages

Plan these pages:

## Home

Answer the core question immediately.

Show:

* best-value model by task
* cheapest reliable local model
* cheapest reliable cloud model
* cost per accepted result
* current benchmark version
* methodology link

## Task-family leaderboard

Examples:

```text
/benchmarks/structured-extraction
/benchmarks/classification
/benchmarks/normalization
```

Show:

* pass rate
* schema-valid rate
* hallucination rate
* consistency
* median latency
* cost per accepted result
* task-specific recommendation

## Model detail

Examples:

```text
/models/qwen-3-5-9b
/models/gemma-4-12b
/models/gpt-5-6-luna
```

Show:

* tested surface
* exact version
* hardware or provider
* task-level results
* representative successes
* representative failures
* speed
* cost
* reliability
* limitations

## Model comparison

Allow comparison of two or three models on one task family.

## Raw run evidence

Each public result should be traceable to:

* case definition
* exact prompt
* raw response
* parsed response
* score breakdown
* model and provider metadata
* run date

Redact secrets and internal API metadata.

## Methodology

Explain:

* case design
* ground truth
* scoring
* repetitions
* model configuration
* limitations
* web-versus-API separation
* local quantization
* pricing dates
* conflict-of-interest policy

## Custom benchmark page

The first monetization offer:

> Submit examples from your workflow and receive a private model comparison showing the cheapest reliable model and recommended routing strategy.

Suggested packages for validation:

```text
Quick comparison:
3 models
Up to 25 examples
Basic recommendation

Full comparison:
6–10 models
Up to 100 examples
Failure analysis
Cost projection
Routing recommendation
```

Do not implement payment during the first engineering phase, but plan the conversion path and required intake data.

# Product requirements

The public product must make it easy to answer:

* What should I use?
* Why?
* What will it cost?
* Where will it fail?
* Can I run it locally?
* What happens if I add validation and fallback?
* When was the model last tested?
* Has performance changed since the previous version?

Avoid:

* decorative AI-generated commentary
* unsupported claims
* hiding raw outputs
* vendor favoritism
* sponsored rankings
* one aggregate “intelligence” score
* comparing models under undisclosed prompts
* mixing different model surfaces
* implying a benchmark generalizes beyond its tasks

# Reproducibility requirements

Every published benchmark batch must have:

* benchmark-suite version
* dataset commit hash
* runner commit hash
* scorer version
* prompt version
* exact model identifier
* provider
* quantization
* hardware profile
* runtime version
* run date
* parameter configuration
* pricing snapshot
* result checksum

Create a command conceptually similar to:

```bash
python -m benchmark run \
  --suite automation-mvp-v0.1 \
  --models qwen3.5:9b,gemma4:12b,llama3.1:8b \
  --repetitions 3
```

And:

```bash
python -m benchmark score \
  --batch <batch-id>
```

And:

```bash
python -m benchmark export \
  --batch <batch-id> \
  --format json
```

# Security and privacy

Include:

* API keys only through environment variables or secret managers
* no secrets stored in run records
* log redaction
* safe handling of user-submitted private benchmark data
* clear separation between public and private datasets
* deletion policy
* no use of customer data for public benchmarks without explicit permission
* prompt-injection resistance when source text contains instructions
* file-size and input limits
* provider data-retention disclosures
* licensing review for benchmark datasets and model outputs

# Quality-control requirements

Plan automated tests for:

* schema validators
* scoring functions
* cost calculations
* model adapters
* retry handling
* malformed model output
* provider errors
* missing token counts
* pricing-version changes
* repeated-run aggregation
* web-versus-API separation
* quantization metadata
* public result generation

Create golden fixtures where scoring outputs are known in advance.

Money calculations must be deterministic and tested.

LLM-as-judge scoring should not be necessary for the central MVP metrics. If included later, it must be secondary, disclosed, versioned, and never the sole evaluator.

# Phased implementation plan

Create an implementation sequence at least as detailed as:

## Phase 0 — Product and hardware validation

* Inspect TheImp.
* Verify model tags.
* Run one representative prompt through each accessible model.
* Record approximate throughput and memory use.
* Verify API access.
* Estimate full benchmark cost.
* Confirm that the six-model launch set is practical.
* Establish fallbacks.

## Phase 1 — Benchmark specification

* Freeze MVP audience and question.
* Define task taxonomy.
* Define case format.
* Define run format.
* Define scoring.
* Define acceptance thresholds.
* Define provenance rules.
* Define pricing snapshots.

## Phase 2 — Runner and adapters

* Build normalized runner.
* Implement Ollama.
* Implement one cloud adapter first.
* Add remaining adapters.
* Add manual and AutoGemini import.
* Add error classification.
* Add raw artifact storage.

## Phase 3 — Corpus and scoring

* Create 75 reviewed cases.
* Implement deterministic scorers.
* Create scoring fixtures.
* Manually inspect sample outputs.
* Freeze benchmark suite v0.1.

## Phase 4 — Initial benchmark

* Run three repetitions.
* Identify failures in the benchmark itself.
* Correct benchmark defects without moving goalposts.
* Rerun invalidated batches.
* Produce first stable results.
* Simulate escalation workflows.

## Phase 5 — Public web MVP

* Build required pages.
* Publish raw evidence.
* Add model/task comparisons.
* Add methodology.
* Add basic search and filters.
* Add custom-benchmark interest form.

## Phase 6 — Validation launch

* Share with automation builders.
* Collect workflow submissions.
* Measure which pages and recommendations users value.
* Attempt to sell the first custom benchmark.
* Prioritize expansion from evidence.

For each phase provide:

* goal
* deliverables
* dependencies
* acceptance criteria
* major risks
* estimated implementation effort
* expected cash cost
* explicit out-of-scope items

# Initial success criteria

Define measurable MVP success.

Examples:

## Product completion

* Six model surfaces tested, or documented justification for substitutions.
* Seventy-five validated cases.
* Three runs per model-case combination.
* Full provenance for at least 95% of valid runs.
* Public pages traceable to raw evidence.
* Reproducible local reruns.

## Audience validation

Within the first 30–45 days after launch:

* At least 100 qualified visitors from automation-related communities.
* At least 10 people use the comparison views meaningfully.
* At least five people submit a workflow or request a model comparison.
* At least one person is willing to pay for a custom benchmark.
* At least three users state that the result changed or confirmed a model decision.

## Kill or pivot signals

* Users only want generic model rankings.
* Nobody submits real workflows.
* The benchmark results are too sensitive to prompt wording to remain useful.
* Cloud pricing and version churn make maintenance unmanageable.
* The dataset cannot distinguish models meaningfully.
* Users value raw test tools more than the published database.
* No one is willing to pay for custom evaluation after targeted validation.

# Expansion roadmap

Keep these out of the MVP but design for them:

* Claude Haiku
* additional Qwen and Gemma sizes
* GPT-5.4 nano comparison
* Mistral and GLM models
* stronger cloud models as escalation baselines
* GPU and VPS workers
* user-submitted private benchmark suites
* live workflow cost calculator
* historical model-drift tracking
* email alerts when a cheaper model surpasses a saved model
* downloadable datasets
* benchmark API
* router configuration export
* n8n workflow export
* community benchmark contributions
* human-reviewed benchmark packs
* contractor-operations benchmark suite for IronWork
* Linux troubleshooting suite
* coding microtasks
* multimodal extraction

# IronWork connection

Do not make the public MVP contractor-specific, but ensure the system can later support an IronWork benchmark pack:

```text
Field notes → structured work record
Estimate → structured scope
Customer message → intent and urgency
Change request → approval classification
Job record → invoice-ready summary
Invoice → payment follow-up action
Technician notes → labor and materials
```

The benchmark infrastructure should eventually tell IronWork:

* which tasks can run locally
* which tasks need a cloud model
* which model is cheapest
* which fields need deterministic validation
* which cases require escalation
* expected cost per completed contractor workflow

# Required planning documents

Create these files:

```text
docs/MVP_MASTER_PLAN.md
docs/PRODUCT_SCOPE.md
docs/BENCHMARK_SPEC.md
docs/DATA_MODEL.md
docs/ARCHITECTURE.md
docs/MODEL_LAUNCH_SET.md
docs/SCORING_SPEC.md
docs/IMPLEMENTATION_ROADMAP.md
docs/RISKS_AND_ASSUMPTIONS.md
docs/MONETIZATION_VALIDATION.md
docs/DECISION_LOG.md
```

The documents should cross-reference one another rather than repeat large sections.

`MVP_MASTER_PLAN.md` must serve as the primary living plan.

It must contain:

* executive summary
* exact audience
* exact question
* value proposition
* initial model set
* MVP scope
* architecture summary
* phased roadmap
* effort and cost estimate
* acceptance criteria
* monetization test
* risks
* unresolved decisions
* immediate next actions

`DECISION_LOG.md` must capture decisions in this format:

```text
Decision
Status
Date
Context
Options considered
Chosen option
Reason
Consequences
Revisit trigger
```

# Final response requirements

After creating the planning documents, respond with:

1. The recommended MVP architecture.
2. Whether the initial six-model set is viable on current constraints.
3. Any required substitutions.
4. The highest-risk assumption.
5. The cheapest credible path to the first published benchmark.
6. The expected benchmark-run count.
7. The expected direct cash cost range, clearly separating known costs from assumptions.
8. The first five implementation tasks in exact order.
9. The planning files created.
10. Any facts you could not verify.

Do not begin production implementation.

Do not pretend unavailable information was verified.

Do not broaden the MVP beyond:

> Which inexpensive model should an automation builder use for structured extraction and classification?

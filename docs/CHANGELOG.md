# Changelog

All notable repository and product changes documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/). Versioning will apply once product releases exist.

## Unreleased

### Added

- `docs/MVP_MASTER_PLAN.md` — primary living plan, cost/gate summary, and full historical-requirement crosswalk
- `AGENTS.md` — cross-agent mandatory repository instructions and source-of-truth hierarchy
- `CLAUDE.md` and `.cursor/rules/shared-context.mdc` — shared pointers to the root agent instructions
- `index.md` — documentation router for humans and agents
- `README.md` — human-facing repository introduction
- `.cursor/rules/00-project-foundation.mdc` — Cursor always-applied bridge to AGENTS.md
- `docs/PRODUCT_BRIEF.md` — strategic product definition
- `docs/MVP_SCOPE.md` — authoritative MVP scope boundary
- `docs/PROJECT_STATE.md` — operational session handoff
- `docs/BENCHMARK_SPEC.md` — benchmark methodology and surface separation
- `docs/MODEL_LAUNCH_SET.md` — catalog-confirmed candidate models and Phase 1 viability gates
- `docs/EXPERIMENT_PROTOCOL.md` — controlled-run procedure
- `docs/SCORING_AND_EVALUATION.md` — metrics, formulas, verdict labels
- `docs/PROVENANCE_AND_REPRODUCIBILITY.md` — metadata and reproducibility rules
- `docs/DATA_MODEL.md` — conceptual entity model
- `docs/ARCHITECTURE.md` — approved local-first system design and static publication boundary
- `docs/MONETIZATION_AND_VALIDATION.md` — validation sequence and pricing hypotheses
- `docs/RISKS_AND_ASSUMPTIONS.md` — risk register and document contradictions
- `docs/DECISION_LOG.md` — approved decision records (DEC-0001 through DEC-0019)
- `docs/templates/BENCHMARK_CASE_TEMPLATE.yaml`
- `docs/templates/DECISION_RECORD_TEMPLATE.md`
- `docs/templates/EXPERIMENT_REPORT_TEMPLATE.md`
- `docs/templates/MODEL_PROFILE_TEMPLATE.md`
- `scripts/phase1_local_probe.py` — local-only, one-off TheImp hardware/model evidence collector
- `scripts/phase1_install_ollama_runtime.sh` — checksum-pinned, rollback-capable Phase 1 Ollama runtime installer
- `scripts/validate_phase1_evidence.py` — structured invariant validator for the frozen local profiles
- `scripts/validate_markdown_links.py` — repository-local Markdown target validator
- `evidence/phase1-theimp-2026-07-31/` — raw hardware profile, model metadata, requests/responses, telemetry samples, pull failure, and Ollama service logs
- `evidence/phase1-theimp-2026-07-31-ollama-0.32.5/` — final runtime upgrade provenance, exact three-model profiles, probes, NVIDIA diagnosis, and checksums
- `pyproject.toml` and `src/goodenough_bench/` — Python 3.10+ package scaffold, standard-library CLI entrypoint, strict Pydantic lifecycle boundaries, tracked SQLite migrations, and repository for batches/planned runs
- `tests/` — focused unit coverage for valid construction, JSON serialization with explicit nulls, required provenance, invalid surface/identity combinations, collection/parse separation, migration integrity, repository idempotency, and placeholder CLI behavior
- `.gitignore` — Python build output plus operational SQLite and raw/private artifact exclusions

### Documentation

- Established documentation hierarchy: `AGENTS.md` → `index.md` → task-specific specs
- Labeled `initialprompt.md` as historical founding specification
- Labeled `roadmap.md` as living phased delivery plan
- Recorded and resolved the former `roadmap.md` vs `initialprompt.md` corpus-size contradiction in risks and DEC-0001
- Completed the documentation-to-MVP audit and reconciled all policy decision markers
- Confirmed official catalog listings for the six candidate identifiers while leaving access, pricing, and performance unverified
- Recorded X1-Carbon observations separately from the uninspected TheImp worker
- Captured the dated `theimp-2026-07-31` hardware/runtime profile and preserved the repository migration path caveat
- Ran one discarded warmup plus extraction, classification, and normalization probes for the installed Qwen and Llama candidates
- Classified Qwen and Llama as hardware-gate viable while preserving structured-output limitations as preliminary operational evidence, not benchmark scores
- Recorded the failed `gemma4:12b` pull without substitution: Ollama 0.17.4 returned HTTP 412 and requires a newer runtime
- Upgraded Ollama from 0.17.4 to 0.32.5 from the checksum-verified official archive while preserving all models, the model path, systemd configuration, and recoverable runtime backups
- Pulled exact `gemma4:12b` and froze Qwen, Gemma, and Llama profiles on one runtime; all three passed every local viability gate
- Preserved Ollama 0.32.5's `\d` grammar-conversion failure and verified the semantics-equivalent `[0-9]` schema pass 9/9 without output repair
- Diagnosed NVML precisely: loaded module 595.71.05 is stale while the installed module, DKMS build, and userspace library are 595.84; reboot remains deferred

### Changed

- Replaced the universal pre-work planning-document sequence with a tiered agent read policy: durable rules and current state for non-trivial work, task-routed authoritative documents by default, and master-plan/roadmap/decision-log reads for cross-cutting or ambiguous work
- Replaced the conflicting broad roadmap with approved Phases 0–7 and a 43–71 day planning estimate
- Approved 75 cases, three task families, six surfaces, three repetitions, and 1,350 planned runs
- Superseded the proposed Supabase architecture with Python, SQLite, filesystem artifacts, versioned public JSON, and static Next.js
- Approved two-pass case review, deterministic thresholds/verdicts, timeout/order/retry policies, local viability gates, and run-review sampling
- Clarified that cloud spending controls apply only before cloud calls and never block local implementation or local batches
- Deferred backend infrastructure, auth, payments, subscriptions, and remote workers
- Completed Phase 1, froze the three exact local profiles, and marked Phase 2 ready without starting the production runner
- Began Phase 2 with schema and CLI boundaries only
- Added tracked SQLite migrations (`0001_initial.sql`), a checksum-verified migration runner, `BenchmarkBatch` boundary validation, and an idempotent SQLite repository for benchmark batches and planned runs; artifacts, adapters, corpus, parsing/scoring behavior, cloud integrations, and the public application remain unimplemented
- Reframed Phase 3 as a reviewed, pilot-locked corpus/scoring candidate and moved the final `automation-mvp-v0.1.0` freeze after Phase 4 pilot correction and re-review
- Added an 8–12-participant pre-launch discovery track and a private pilot-report investment gate before the full stable batch and static-site investment
- Updated competitive positioning to treat structured-extraction benchmarks and modern live routers as direct pressure while preserving the narrower three-family, exact-provenance, cost-per-accepted-result, and escalation-evidence thesis
- Clarified that benchmark/suggestion APIs and MCP interfaces remain post-validation rather than Phase 6 deliverables
- Moved a bounded persistence-hardening task ahead of artifact storage: explicit batch purpose, parent/run provenance consistency, and statement-complete migration execution
- Hardened Phase 2 persistence with `BatchPurpose`, migration `0002_batch_purpose.sql`, parent-batch/planned-run provenance enforcement, and statement-complete migration execution; pre-0002 batches conservatively migrate to `diagnostic_pilot`
- Added tiered git workflow guidance (`docs/GIT_WORKFLOW.md`, DEC-0020) for when to use direct-to-`main` commits vs feature branches and pull requests; wired into `AGENTS.md`, `index.md`, Cursor rules, and `README.md`
- Added a contract-scoped PR review protocol (DEC-0021), mandatory agent rules, and a PR template: implementation PRs now declare their invariant, boundaries, non-goals, documentation impact, and verification matrix; relevant documentation remains in the same PR. Review-churn hard cuts now preserve the branch, close the incoherent PR, and require dependency-ordered replacement slices rather than further review-driven expansion
- Implemented immutable filesystem artifact store (`ArtifactStore` protocol, `FilesystemArtifactStore`, `ArtifactRef` boundary, SHA-256 checksums, run-scoped write-once semantics, corruption verification, and `parse_verified_artifact` write-before-parse integration) with focused unit tests; SQL migrations and batch-purpose/provenance invariants unchanged
- Implemented resumable deterministic batch planning (`RepositoryBatchPlanner`, `BatchPlanSpec`, stable planned-run IDs, seeded case order, `FakeProviderBatchPlanner` interruption/resume harness) with focused unit tests; repository conflict/provenance rules unchanged; no runner execution, adapters, corpus, or scoring yet
- Implemented strict model-profile and pricing-snapshot loaders (`profile_loaders.py` and packaged JSON under `src/goodenough_bench/config/`) with Pydantic catalog boundaries, cross-reference validation, fixed API-surface-to-provider-and-host bindings plus `ollama_local` → `ollama` and a required local host that preserve routed/direct/local provenance, MVP pricing currency restricted to `USD`, deterministic ordering, canonical JSON checksums, installation-target-safe default discovery, and synthetic fixtures explicitly marked as unverified placeholders; no migration, provider API calls, or verified prices
- Centralized profile identity validation in shared lifecycle boundaries; added immutable local artifact/context identity, pinned OpenRouter upstream identity with fallbacks disabled and route-matched pricing, source-bound identity confidence/environment constraints, and migration `0003_model_route_provenance.sql` so complete material identity survives planning and SQLite round trips while pre-0003 planned rows remain explicitly legacy-incomplete
- Added migration `0004_reproduction_checksum.sql` with nullable `reproduction_checksum` on `benchmark_batches`, conservative reclassification of legacy `frozen` rows to `completed` until an explicit verified freeze, and repository batch revalidation on `create_batch` before any insert
- Enforced forward-only batch lifecycle transitions through `completed`, stale-writer rejection on conditional status updates, atomic planning lock while status remains `planned`, and completion accounting that requires explicit run counts matching persisted planned runs
- Implemented frozen-batch persisted-metadata checksum calculation, read-only `batch reproduce --verify-checksum` verification against operational SQLite databases, and narrowed provenance documentation for Phase 2 fingerprint scope versus future corpus/scorer verification

### Fixed

- Removed unresolved scope, architecture, review, scoring, timeout, run-order, cost, and intake policy markers from living documents
- Corrected stale cloud-candidate fields that called deferred credential/pricing work "Phase 1 evidence," aligning them with DEC-0013 and the local-only Phase 1 boundary
- Corrected the roadmap contradiction that froze the suite before the approved pre-freeze pilot
- Restored five current actions in the operational handoff after the persistence commit left a "Next five actions" section with only four items
- Restored the five-action operational handoff after completing the loader action and relocating the packaged fixtures
- Required planning to resolve non-null pricing-snapshot references against a typed catalog and match provider, exact model, and routed-provider identity before marking provenance complete; preserved repository hydration for pre-0003 legacy-incomplete rows by applying only the identity rules that existed when those rows were written
- Closed repository write-boundary bypasses by fully revalidating copied planned runs before SQL and requiring direct API/priced writes to resolve their snapshot against a supplied typed catalog
- Closed the collected-response provenance bypass by prohibiting direct normalized-response construction and requiring a factory that binds to the planned run and resolves API/priced provenance against a typed catalog
- Merged [PR #3](https://github.com/glinkplink/goodenoughai/pull/3) — strict profile/pricing loaders, migration `0003_model_route_provenance.sql`, planning and repository provenance hardening, and `NormalizedAdapterResponse.from_planned_run`
- Documented deferred Codex review follow-ups from PR #3 (PB-001 nested mutability, PB-002 `model_construct` bypass) in provenance and risk registers; not merge blockers before the runner/adapter slice

### Removed

- *(none)*

## Related documents

- [index.md](../index.md)
- [DECISION_LOG.md](DECISION_LOG.md)
- [PROJECT_STATE.md](PROJECT_STATE.md)

# Changelog

All notable repository and product changes documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/). Versioning will apply once product releases exist.

## Unreleased

### Added

- `docs/MVP_MASTER_PLAN.md` — primary living plan, cost/gate summary, and full historical-requirement crosswalk
- `AGENTS.md` — cross-agent mandatory repository instructions and source-of-truth hierarchy
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
- `docs/DECISION_LOG.md` — approved decision records (DEC-0001 through DEC-0018)
- `docs/templates/BENCHMARK_CASE_TEMPLATE.yaml`
- `docs/templates/DECISION_RECORD_TEMPLATE.md`
- `docs/templates/EXPERIMENT_REPORT_TEMPLATE.md`
- `docs/templates/MODEL_PROFILE_TEMPLATE.md`
- `scripts/phase1_local_probe.py` — local-only, one-off TheImp hardware/model evidence collector
- `evidence/phase1-theimp-2026-07-31/` — raw hardware profile, model metadata, requests/responses, telemetry samples, pull failure, and Ollama service logs

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

### Changed

- Replaced the universal pre-work planning-document sequence with a tiered agent read policy: durable rules and current state for non-trivial work, task-routed authoritative documents by default, and master-plan/roadmap/decision-log reads for cross-cutting or ambiguous work
- Replaced the conflicting broad roadmap with approved Phases 0–7 and a 43–71 day planning estimate
- Approved 75 cases, three task families, six surfaces, three repetitions, and 1,350 planned runs
- Superseded the proposed Supabase architecture with Python, SQLite, filesystem artifacts, versioned public JSON, and static Next.js
- Approved two-pass case review, deterministic thresholds/verdicts, timeout/order/retry policies, local viability gates, and run-review sampling
- Clarified that cloud spending controls apply only before cloud calls and never block local implementation or local batches
- Deferred backend infrastructure, auth, payments, subscriptions, and remote workers
- Moved Phase 1 to blocked-at-profile-freeze pending approval to upgrade Ollama and rerun all three local candidates on one runtime

### Fixed

- Removed unresolved scope, architecture, review, scoring, timeout, run-order, cost, and intake policy markers from living documents
- Corrected stale cloud-candidate fields that called deferred credential/pricing work "Phase 1 evidence," aligning them with DEC-0013 and the local-only Phase 1 boundary

### Removed

- *(none)*

## Related documents

- [index.md](../index.md)
- [DECISION_LOG.md](DECISION_LOG.md)
- [PROJECT_STATE.md](PROJECT_STATE.md)

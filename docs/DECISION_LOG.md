> **Status:** Active  
> **Authority:** Source of truth for current approved decisions  
> **Last reviewed:** 2026-08-01  
> **Update when:** A decision is approved, superseded, rejected, or materially revised  
> **Historical records:** [DECISION_LOG_ARCHIVE.md](DECISION_LOG_ARCHIVE.md) (DEC-0001 through DEC-0017)  
> **Related:** [MVP_MASTER_PLAN.md](MVP_MASTER_PLAN.md), [MVP_SCOPE.md](MVP_SCOPE.md), [ARCHITECTURE.md](ARCHITECTURE.md), [RISKS_AND_ASSUMPTIONS.md](RISKS_AND_ASSUMPTIONS.md)

# Decision log

Newer approved decisions supersede older planning text. Load the archive when an older decision's exact rationale, consequence, or revisit trigger matters. Model availability, credentials, prices, and hardware measurements are facts to verify, not decisions.

## DEC-0018 — Tiered documentation loading for agents

- **Status:** Approved
- **Date:** 2026-07-31
- **Context:** The prior agent guidance required several broad planning documents before every substantial task, despite the repository having a task-routing index and a compact operational handoff. This added unnecessary context to bounded work and created inconsistent instructions between the Cursor bridge and `AGENTS.md`.
- **Options considered:** Keep the universal planning-document sequence; load only the project-state handoff; use durable constraints plus task-routed documentation.
- **Chosen option:** Agents read durable repository rules and the current project state for non-trivial work, then consult the Quick task routing section of `index.md` and load only the task's authoritative documents. The master plan, roadmap, and decision log are required for cross-cutting work, phase planning, priority changes, or ambiguity. Trivial strictly bounded edits require the rules and target file only unless their impact expands.
- **Reason:** Preserves scope and provenance safeguards while reducing irrelevant context and making the instructions consistent across agent surfaces.
- **Consequences:** `AGENTS.md`, the Cursor rule, and `index.md` use the same tiered policy. `initialprompt.md` remains historical and on-demand.
- **Revisit trigger:** Repeated agent errors show that a durable constraint or routing condition is being missed.

## DEC-0019 — Pre-freeze pilot and pre-launch investment gate

- **Status:** Approved
- **Date:** 2026-08-01
- **Context:** The roadmap froze the 75-case suite in Phase 3 even though DEC-0015 requires the 15-case pilot to find and correct defects before freeze. The full plan also commits 43–71 ideal engineering days before post-launch validation, while structured-extraction benchmarks and increasingly capable live routers narrow the assumed market gap.
- **Options considered:** Keep the Phase 3 freeze and wait until Phase 7 to validate demand; move the public site or an API/router ahead of evidence; treat Phase 3 as a reviewed candidate, freeze after the Phase 4 pilot, and run bounded discovery before the full stable batch/site investment.
- **Chosen option:** Phase 3 produces the reviewed, pilot-locked release candidate. Phase 4 runs the diagnostic pilot, versions corrections, repeats invalidated human reviews, and then freezes `automation-mvp-v0.1.0`. Interview 8–12 target builders during Phases 2–4 and privately test a clearly labeled sample pilot report after technical gates pass. Require an explicit continue/pivot/stop decision before Phase 5.
- **Reason:** Preserves evidence-first dependencies, resolves the pilot/freeze contradiction, and tests whether the narrower recommendation-and-evidence wedge is actionable before the most expensive execution and site work.
- **Consequences:** Pilot outputs are never public leaderboard claims. Continue evidence targets at least three actionable-decision or workflow signals and at least one credible willingness-to-pay signal. Missing the gate requires an explicit positioning, custom-report, self-service-evaluation, or stop decision; it does not silently expand the MVP. Live routing, public APIs, suggestion endpoints, and MCP interfaces remain post-validation.
- **Revisit trigger:** The Phase 4 investment decision is recorded, or the user explicitly changes the launch/validation sequence.

## DEC-0020 — Tiered git workflow: `main` vs branch + PR

- **Status:** Approved
- **Date:** 2026-08-01
- **Context:** The repository is solo-maintained in Phase 2 with no CI or protected `main`, but upcoming work (artifact store, runner, corpus, pilot) needs clear rules so agents and humans do not mix high-risk persistence or benchmark changes with low-risk doc edits. Agents also must not commit or open PRs without explicit user request.
- **Options considered:** Always use PRs; always commit to `main`; tiered rules with an authoritative routing document.
- **Chosen option:** Tiered workflow documented in `docs/GIT_WORKFLOW.md`. Direct commits to `main` are acceptable for trivial bounded edits and low-blast-radius Phase 2 docs/scaffold work. Feature branch + pull request is required when changes touch migrations, repository contracts, provenance, scoring, runner/adapters, artifact store, corpus cases, public export, multi-day work, or pilot-validity gates. Agents must classify and recommend the workflow before non-trivial work but wait for explicit user approval before `git commit` or `gh pr create`.
- **Reason:** Keeps solo iteration fast for documentation while isolating hard-to-revert benchmark and persistence work before CI and team scale force PR-only merges.
- **Consequences:** `AGENTS.md`, `index.md`, Cursor foundation rule, and `README.md` point to `docs/GIT_WORKFLOW.md`. Revisit when CI, branch protection, or a second regular contributor is added.
- **Revisit trigger:** GitHub Actions CI on PRs, `main` branch protection, or a second regular contributor on overlapping code.

## DEC-0021 — Contract-scoped PR review protocol

- **Status:** Approved
- **Date:** 2026-08-01
- **Context:** PR #3 became a multi-hour sequence of successive automated reviews and adjacent fixes. Its initial profile-loader scope expanded through pricing, planning, repository, and collected-response provenance boundaries, leaving documented adapter-hardening follow-ups. The repository needs a durable protocol that keeps review focused without separating the documentation needed to explain changed behavior.
- **Options considered:** Keep the existing one-logical-concern guidance; split implementation and documentation into separate PRs; enforce contract-scoped PRs with documentation and verification evidence in the same PR.
- **Chosen option:** Every PR declares one contract/invariant, affected boundaries, explicit non-goals, documentation impact, and a verification matrix before implementation. Documentation that describes changed behavior remains in that PR. Authors self-review and verify a final head before requesting review, batch feedback responses where practical, and do not expand a PR into an adjacent contract without explicit user approval. If review exposes a second successive contract expansion, an explicit non-goal, or a PR body that no longer honestly describes the diff, preserve the branch, close the PR, and re-slice it into dependency-ordered replacements. Current-slice P1 findings must be fixed before merge; valid, unreachable out-of-slice concerns require a triggered, owned, testable follow-up before deferral. A PR template and the mandatory agent rules enforce the protocol.
- **Reason:** Small, coherent contract boundaries make reviews decisive and prevent each validation fix from silently broadening a PR into a new persistence, provenance, or adapter design.
- **Consequences:** A code change may still update several documents when those documents describe the same contract. Deferred findings become explicit future acceptance gates rather than vague merge notes. Closing an over-broad PR preserves its history while preventing review-driven refactoring; replacement PRs must declare their dependency order. The first non-fake adapter slice must close PB-001 and PB-002 before collected responses become reachable.
- **Revisit trigger:** Repeated review churn despite this protocol, addition of CI/branch protection, or a material change to contributor/review tooling.

## DEC-0022 — Codex review only on high-impact PRs

- **Status:** Approved
- **Date:** 2026-08-01
- **Context:** PRs #5–#7 showed that requesting Codex on every contract-scoped slice produced stale threads, unnecessary P2 churn, and review fatigue without improving merge confidence on routine persistence work. Self-review plus the verification matrix was sufficient for merge on several slices.
- **Options considered:** Codex on every PR; Codex never; tiered Codex only for extremely dangerous or high-impact changes.
- **Chosen option:** Codex review is optional and requested only when a PR matches explicit high-impact triggers in `docs/GIT_WORKFLOW.md` (persistence semantics, provenance/scoring integrity, runner/adapters, public/export surfaces, corpus/suite freeze, or hard-to-revert blast radius). Routine contract-scoped PRs merge after self-review, tests, and user approval. Agents must not comment `@codex review` on routine PRs.
- **Reason:** Preserves review capacity for changes that can silently corrupt benchmark evidence or public claims; avoids treating automated review as a mandatory gate on every slice.
- **Consequences:** `AGENTS.md`, `docs/GIT_WORKFLOW.md`, and the PR template encode the tiered rule. Stale Codex threads on earlier commits are not merge blockers when Codex was not required for that PR.
- **Revisit trigger:** A high-impact PR merges with an undetected integrity defect attributable to skipping Codex, or CI/branch protection adds a mandatory external review gate.

## Related documents

- [DECISION_LOG_ARCHIVE.md](DECISION_LOG_ARCHIVE.md)
- [MVP_MASTER_PLAN.md](MVP_MASTER_PLAN.md)
- [MVP_SCOPE.md](MVP_SCOPE.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [RISKS_AND_ASSUMPTIONS.md](RISKS_AND_ASSUMPTIONS.md)
- [templates/DECISION_RECORD_TEMPLATE.md](templates/DECISION_RECORD_TEMPLATE.md)

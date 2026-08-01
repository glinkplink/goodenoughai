# GoodEnough.ai

> Find the cheapest AI model that reliably completes your automation task.

**GoodEnough.ai** is a public benchmark database that answers one practical question for automation builders:

> **Which inexpensive AI model should I use for structured extraction, classification, and normalization?**

This is not a universal intelligence leaderboard. It measures production reliability — valid JSON, preserved facts, failure rates, and **cost per accepted result** — for repeatable automation workloads.

## Intended audience

- n8n, Make, and Zapier users
- Python automation and AI-agent developers
- Scraper and data-pipeline builders
- Solo developers and small agencies
- People choosing between local models and inexpensive cloud APIs

## Current repository status

**Phase:** Documentation audit complete; hardware/model/budget validation next. No production application yet.

### What exists today

- Product vision and phased plan ([`roadmap.md`](roadmap.md))
- Primary implementation-ready plan and requirement crosswalk ([`docs/MVP_MASTER_PLAN.md`](docs/MVP_MASTER_PLAN.md))
- Original founding specification ([`initialprompt.md`](initialprompt.md))
- Agent navigation and governance docs ([`AGENTS.md`](AGENTS.md), [`index.md`](index.md))
- Technical specifications under [`docs/`](docs/)

### What is not built yet

- Benchmark runner, model adapters, or scoring engine
- Benchmark corpus (75-case MVP target)
- Public web application
- Database, infrastructure, or deployed services
- Verified model runs, pricing snapshots, or hardware inspection on TheImp

## Documentation entry points

| Start here | Purpose |
|------------|---------|
| [`index.md`](index.md) | Full documentation map for humans and agents |
| [`AGENTS.md`](AGENTS.md) | Mandatory rules for Cursor, Codex, and other coding agents |
| [`docs/MVP_MASTER_PLAN.md`](docs/MVP_MASTER_PLAN.md) | Approved end-to-end MVP plan |
| [`roadmap.md`](roadmap.md) | Phased delivery plan |
| [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md) | Current handoff state for each session |

## Working in this repository

Agents and contributors should read `AGENTS.md` before substantial work, use `index.md` to find relevant specs, and update living documentation when behavior or scope changes. Do not treat [`initialprompt.md`](initialprompt.md) as automatically current — check [`docs/DECISION_LOG.md`](docs/DECISION_LOG.md) and [`docs/MVP_SCOPE.md`](docs/MVP_SCOPE.md) for authoritative scope.

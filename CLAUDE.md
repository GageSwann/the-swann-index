# CLAUDE.md: The Swann Index (TSI)

Personal college football rating model + prediction engine + public read-only dashboard. One operator (the owner) runs the model; everyone else only views.

## Read before building
The plan lives in `docs/`. Before starting work, read the roadmap and the doc for the area you're touching:
- `docs/07-roadmap.md`: current phase and checklist. **Tick boxes as items are completed.**
- `docs/09-conventions.md`: modularity, secrets, workflow, which skills to use
- `docs/02-architecture.md`: repo layout, data flow, API contract
- `docs/03-data-sources.md`: CFBD endpoints and the API call budget
- `docs/04-model.md` / `docs/05-sportsbook.md`: model and odds math
- `docs/06-frontend.md`: page specs
- `docs/decisions.md`: append an entry when a meaningful decision is made or changed

## How we work
- **Step by step.** One roadmap item at a time: build → test → tick → commit. Stop for review between items; don't build ahead.
- **Small modules.** One responsibility per file (~200 lines target, split past ~300). Pure math in `model/`/`book/` has no I/O. See doc 09 §2.
- **Use existing skills** listed in doc 09 §5. Read a third-party skill before installing it.

## Repo layout
- `backend/`: Python package `tsi` (ingest, db, model, book, backtest, api). Managed with `uv`.
- `web/`: Next.js App Router + TypeScript + Tailwind.
- `docs/`: planning docs (source of truth for intent).
- `.github/workflows/`: scheduled model runs, CI.

## Non-negotiable rules
1. **No look-ahead.** Any rating, prediction, or backtest for a game may only use data available before that game's kickoff. Backtests are walk-forward.
2. **Published predictions are immutable.** Once a prediction snapshot is published, never update it in place; write a new snapshot. Grading uses the latest snapshot published before kickoff.
3. **No secrets in code.** Passwords, API keys, tokens and connection strings come from environment variables only: `backend/.env` (loaded by `tsi/config.py`) and `web/.env.local`, both gitignored. Never hard-code, log, or commit them; never prefix a secret with `NEXT_PUBLIC_`. Keep each `.env.example` current (names only).
4. **Cache API data.** Completed seasons are fetched once and stored; don't burn CFBD API calls re-fetching them. Free tier ≈ 1,000 calls/month; see the budget in doc 03.
5. **Division-agnostic schema.** FBS-only today, FCS later; never hard-code "FBS" into table design. Conference and division are **per season** (`team_seasons`).
6. Raw model output and manual adjustments are stored separately; the UI must be able to show both.

## Commands
```powershell
pre-commit install              # once per clone: enables gitleaks + ruff hooks
pre-commit run --all-files      # run every hook manually
```
Backend (run from `backend/`):
```powershell
uv sync                         # install/update deps into backend/.venv
uv run tsi --help               # CLI entry point (src/tsi/cli/)
uv run pytest                   # tests (tests/ mirrors src/tsi/)
uv run ruff check . ; uv run ruff format .
uv add <pkg>  /  uv add --dev <pkg>
```
_Web commands are added when `web/` is scaffolded (Phase 5)._

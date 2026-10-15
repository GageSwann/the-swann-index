# CLAUDE.md: The Swann Index (TSI)

Personal college football rating model + prediction engine + public read-only dashboard. One operator (the owner) runs the model; everyone else only views.

## Status
- **Phase 0–1 complete** (2026-10-14): 2014–2026 loaded into Neon `dev`; nightly GitHub Action refreshes the current season.
- **Phase 2 in progress:** Elo (val MAE 13.15), ridge `season` ratings, preseason prior + `predictive` blend done. **Predictive val MAE 12.84 vs. Vegas 12.00, SU 71.1%.** Next: SP+ comparison ingest, then the backtest harness (saved runs, calibration).
- No launch deadline: quality over speed (decision #27).

## Read before building
The plan lives in `docs/`. Before starting work, read the roadmap and the doc for the area you're touching:
- `docs/07-roadmap.md`: current phase and checklist. **Tick boxes as items are completed.**
- `docs/09-conventions.md`: modularity, secrets, workflow, which skills to use
- `docs/02-architecture.md`: repo layout, schema, data flow, API contract
- `docs/03-data-sources.md`: CFBD endpoints, caching/freshness, call budget, quality checks
- `docs/04-model.md` / `docs/05-sportsbook.md`: model and odds math
- `docs/06-frontend.md`: page specs
- `docs/decisions.md`: append an entry when a meaningful decision is made or changed (newest at bottom)

## How we work
- **Step by step.** One roadmap item at a time: build → test → tick → commit. Stop for review between items; don't build ahead. When the owner says "finish phase X", do the whole phase, then stop and discuss.
- **Small modules.** One responsibility per file (~200 lines target, split past ~300). Pure math/transforms have no I/O. Layering: `cli` → `services` → `ingest`/`model`/`book` → `db`.
- **Inspect before building:** for a new CFBD endpoint, fetch one season through the client, study the shape, save a trimmed fixture, then write transforms.
- **Verify with real data** after loading: counts, idempotent re-run, sanity metrics (e.g. closing-spread MAE ≈ 12).
- **Ask before:** applying migrations, anything public or outward-facing.
- **Use existing skills** (doc 09 §5). Read a third-party skill before installing it.

## Non-negotiable rules
1. **No look-ahead.** Any rating, prediction, or backtest for a game may only use data available before that game's kickoff. Backtests are walk-forward. (The Résumé ranking is a retrospective measure and intentionally uses opponents' *current* ratings; see doc 04 §7.)
2. **Published predictions are immutable.** Once a prediction snapshot is published, never update it in place; write a new snapshot. Grading uses the latest snapshot published before kickoff. A DB trigger enforces this.
3. **No secrets in code.** Passwords, API keys, tokens and connection strings come from environment variables only: `backend/.env` (loaded by `tsi/config.py`) and `web/.env.local`, both gitignored. Never hard-code, log, print, or commit them; never prefix a secret with `NEXT_PUBLIC_`. Keep each `.env.example` current (names only). When checking `.env`, print booleans/lengths only.
4. **Cache API data.** Free tier ≈ 1,000 calls/month (guard: 980). Finished seasons are cached forever; the in-progress season expires after 6h. Nightly job ≈ 4 calls/day.
5. **Division-agnostic schema.** FBS-only today, FCS later; never hard-code "FBS" into table design. Conference and division are **per season** (`team_seasons`).
6. Raw model output and manual adjustments are stored separately; the UI must be able to show both.

## Model decisions (doc 04)
- **Two rating sets (#23):** `season` = this season's games only and drives **Power + Résumé rankings**. `predictive` = adds a preseason prior that fades to zero by midseason and drives **predictions/Book**. Fewer than 4 games = *provisional* rank.
- **Résumé (#24):** strength of record vs. a typical **#12** team, recomputed daily with opponents' **current** ratings (dynamic SOS: a win loses value if that opponent collapses).
- **Daily (#25):** the nightly job refits ratings, so midweek games show up the next morning.
- **2020** treated normally (#26). **v1 = baseline as specified** in doc 04; refine later (#28).
- Tune on 2015–2022, validate on 2023–2025.

## Data conventions (learned in Phase 1)
- **Spread sign:** home team's view, **negative = home favored** (CFBD and TSI agree; verified).
- **`team_game_stats`** = one row per team per game = its **offense**; defense is the opponent's row. Efficiency stats are garbage-time filtered; plays/drives are full-game so points-per-drive matches full-game points.
- **Division values:** `fbs`, `fcs`, `ii`, `iii`, `unknown` (CFBD `classification`). Teams missing from CFBD `/teams` (mostly NAIA) get placeholder rows with slug `name-<id>`.
- **Times** are UTC, timezone-aware; `parse_utc` rejects naive timestamps. `games.start_time_tbd` marks date-only kickoffs.
- **Market lines** are change-only snapshots; `is_closing` = captured at/after kickoff.
- **Known gaps** (`tsi check` warns): 47 FBS games without advanced stats (mostly 2014–16), no talent before 2015, some new-FBS teams without returning production.
- CFBD identifies teams by **school name** in stats/talent/returning, so match through our tables.

## Gotchas
- **SQLAlchemy 2.1:** don't `dict(session.execute(...))`; unpack rows in a comprehension. Use `.ext(postgresql.distinct_on(...))`, not `.distinct(cols)`.
- **Upserts:** always go through `db/upsert.py` (batched executemany, skips unchanged rows). Never send the same primary key twice in one batch (Postgres error); de-duplicate first.
- **Neon latency** is ~43ms per round trip. Performance means fewer round trips and transactions, not faster Python.
- **Deploy order:** when a migration drops or renames a column, apply it **before** pushing code. The nightly job runs whatever is on `main`.
- **Alembic** autogenerate misses primary-key changes; hand-write those. With our naming convention, pass the short constraint name (e.g. `"basis"`), never the full `ck_table_name`.
- **gitleaks** flags realistic-looking fake keys in tests: use low-entropy values like `"fakekey"`.
- **Windows shell:** PowerShell here-strings mangle inline Python; write scripts to the scratchpad. `sed` replacements containing `#` need another delimiter.
- **GitHub Actions:** `astral-sh/setup-uv` has no floating major tag; pin the exact version (e.g. `v10.3.0`).
- The nightly job writes to the Neon **dev** branch until Phase 6 (#19).

## Commands
```powershell
pre-commit install              # once per clone: enables gitleaks + ruff hooks
pre-commit run --all-files      # run every hook manually
```
Backend (run from `backend/`):
```powershell
uv sync                         # install/update deps into backend/.venv
uv run tsi --help               # CLI entry point (src/tsi/cli/)
uv run pytest                   # tests (tests/ mirrors src/tsi/); DB tests use a throwaway schema
uv run pytest -m "not db"       # skip DB-backed tests (offline)
uv run tsi check                # data quality rules; exit 1 on any `fail` (--season, --details)
uv run tsi model elo            # Elo baseline vs. closing line, by season (train/validate split)
uv run tsi model ratings        # walk-forward season + predictive vs. Elo + Vegas (--lam, --ppd-weight, --prior-games, --cutoff-games)
uv run ruff check . ; uv run ruff format .
uv add <pkg>  /  uv add --dev <pkg>
uv run tsi ingest daily         # refresh current season (also runs nightly in GitHub Actions)
uv run tsi ingest season --season 2014 --through 2026   # all loaders in order (~9 calls/season if not cached)
uv run tsi ingest teams --season 2024     # single loaders: venues, teams, calendar, games, stats, lines, priors
uv run alembic upgrade head     # apply migrations (uses DATABASE_URL_DIRECT)
uv run alembic revision --autogenerate -m "msg"   # after changing models; review before applying
uv run alembic check            # models and DB in sync?
```
Migrations target the Neon **dev** branch locally. Ask before applying to any database.
GitHub: `gh workflow run daily-refresh.yml` triggers the nightly job manually.
_Web commands are added when `web/` is scaffolded (Phase 5)._

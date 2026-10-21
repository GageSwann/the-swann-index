# CLAUDE.md: The Swann Index (TSI)

Personal college football rating model + prediction engine + public read-only dashboard. One operator (the owner) runs the model; everyone else only views.

## Status
- **Phase 0–1 complete** (2026-10-14): 2014–2026 loaded into Neon `dev`.
- **Phase 2 complete:** model **v1.2**. Rankings = learned PPD+success blend (val MAE 13.37); predictions = stacked margin (**val 12.40 vs. Vegas 12.00, SU 71.7%**); stacked totals (val 12.87 vs. 12.68); Résumé/SOS; report card published (private artifact `AEndkhJAt49YQNJcWC2i7v`, refresh with `tsi backtest export`; last refreshed 2026-10-20).
- **Phase 3 built** (2026-10-20): score distribution, pricing, consensus + shrunk edges, picks, publishing/grading/CLV, Book backtest, `tsi run`. **The nightly job (10:00 UTC) runs `tsi run`:** ingest → rate → grade → publish. "Done when" = first fully graded live week: week 8 (games Oct 20–25, 5 published totals picks, all overs) is graded by the Oct 26 run.
- **Phase 4 complete** (2026-10-21): read-only API with all v1 endpoints (`api/`, read models in `services/read/`), CORS + cache headers + ETag/304 + gzip, seeded-DB tests, spec at `docs/api/openapi.json`.
- **Phase 5 in progress:** skills installed (`.claude/skills/`: `frontend-design`, `webapp-testing`, `react-best-practices`). Next: scaffold `web/`. Week 8 review once graded (Oct 26).
- No launch deadline: quality over speed (decision #27).

## Read before building
The plan lives in `docs/`. Before starting work, read the roadmap and the doc for the area you're touching:
- `docs/07-roadmap.md`: current phase and checklist. **Tick boxes as items are completed.**
- `docs/09-conventions.md`: modularity, secrets, workflow, which skills to use
- `docs/02-architecture.md`: repo layout, schema, data flow, API contract
- `docs/03-data-sources.md`: CFBD endpoints, caching/freshness, call budget, quality checks
- `docs/04-model.md` / `docs/05-sportsbook.md`: model and Book math, with backtest results
- `docs/06-frontend.md`: page specs
- `docs/decisions.md`: append an entry when a meaningful decision is made or changed (newest at bottom; #1–#59 so far)

## How we work
- **Step by step.** One roadmap item at a time: build → test → tick → commit → push. Stop for review between items; don't build ahead. When the owner says "finish phase X", do the whole phase, then stop and discuss.
- **Small modules.** One responsibility per file (~200 lines target, split past ~300). Pure math/transforms have no I/O. Layering: `cli` → `services` → `ingest`/`model`/`book`/`backtest` → `db`. The CLI never queries the DB directly; services return what it prints (e.g. `Board.names`).
- **Experiment before adopting.** Try ideas in a scratchpad script first (walk-forward, fit on TRAIN, score VALIDATE), then build the winner into `src/`. Adopt only if train improves and validation doesn't get worse; log rejected ideas in `decisions.md` too.
- **Verify, don't assume.** After a refactor, results must be identical (re-run `tsi backtest run` and `tsi backtest book`). After touching the live path, check it reproduces the backtest's features for already-played games (parity was exact: 0 difference).
- **Inspect before building:** for a new CFBD endpoint, fetch one season through the client, study the shape, save a trimmed fixture, then write transforms.
- **Ask before:** applying migrations, changing the nightly workflow, anything public or outward-facing. Committing and pushing finished items to `main` is the normal workflow.
- **Use existing skills** (doc 09 §5). Read a third-party skill before installing it.

## Non-negotiable rules
1. **No look-ahead.** Any rating, prediction, or backtest for a game may only use data available before that game's kickoff. Backtests are walk-forward and mirror the 10:00 UTC daily refit. (Résumé intentionally uses opponents' *current* ratings; doc 04 §7.)
2. **Published predictions are immutable.** Never update a snapshot; insert a new one. The **locked** snapshot is derived: the latest `raw` prediction with `published_at < kickoff`; only its picks are graded. A DB trigger rejects updates. **Never back-date `published_at`** and never "replay" past weeks as live snapshots (#57).
3. **No secrets in code.** Passwords, API keys, tokens and connection strings come from environment variables only: `backend/.env` (loaded by `tsi/config.py`) and `web/.env.local`, both gitignored. Never hard-code, log, print, or commit them; never prefix a secret with `NEXT_PUBLIC_`. Keep each `.env.example` current (names only). When checking `.env`, print booleans/lengths only.
4. **Cache API data.** Free tier ≈ 1,000 calls/month (guard: 980). Finished seasons are cached forever; the in-progress season expires after 6h. Nightly job ≈ 4 calls/day.
5. **Division-agnostic schema.** FBS-only today, FCS later; never hard-code "FBS" into table design. Conference and division are **per season** (`team_seasons`). The rated division is named once, in `tsi/divisions.py`.
6. Raw model output and manual adjustments are stored separately; the UI must be able to show both.
7. **Market lines are never model inputs.** They are evaluation points, and in the Book they only size edges (#52).

## Model (doc 04)
- **Two rating sets (#23, #37, #38):** `season` = this season's games only (0.726·PPD + 0.635·success rate, HFA 3.24) → **Power + Résumé rankings**. `predictive` = **stacked** margin (site, PPD, success, prior, Elo; ridge per season-stage bucket) → **predictions/Book**. Fewer than 4 games = *provisional*.
- **Components** (`model/ratings/components.py`): opponent-adjusted ridge fits of PPD, success rate, pace (drives) and tempo (plays), each with a `level`. Non-FBS opponents pool into FCS (−1) and lower (−2). EPA is not fitted (#49).
- **Totals (#50):** stacked game total (league level shrunk to last season, PPD/success sums, pace + tempo, prior, last season's pace/tempo). Scores = (total ± margin) / 2.
- **Distribution (#51):** bivariate normal. σ_margin 15.4, σ_total 16.4 + 0.12·(total − 55), ρ = 0.0074 × home margin. Production fits σ and the edge shrink on **leave-one-season-out** stack predictions (in-sample ones are too sharp, #53).
- **Résumé (#24):** strength of record vs. a typical **#12** team with opponents' current ratings (dynamic SOS).
- Tune on 2015–2022, validate on 2023–2025 (`backtest/splits.py`). 2020 treated normally (#26).
- **New FBS teams in 2026:** North Dakota State (Mountain West) and Sacramento State (MAC) are FBS this season and rated individually; don't mistake them for pooled FCS teams.

## TSI Book (doc 05)
- **TSI has no edge against closing lines.** Its spread disagreements don't predict covers (fitted trust k_spread ≈ 0); it *does* predict line moves (positive CLV every season) and beats **opening totals**.
- **Shrunk edges (#52):** P(cover/over) = Φ(k · (TSI − line)/σ), k learned vs. the median opener: production **k_spread 0.07, k_total 0.32**. Moneyline edge = TSI's win-probability *shift* added to the market's no-vig probability (#55); never compare Φ(margin/σ) with ML prices directly. No intercept/base-rate term (#56: it turned the Book into an under-only bettor).
- **Picks (#54):** ★/★★/★★★ at 1.5/3/5 probability points of edge (ML 3/5/8, EV > 0); flat 1u + ¼ Kelly on 100u (cap 3u). In practice: totals picks, spreads almost never.
- **Book backtest** (`tsi backtest book`, totals at the median opener, CLV vs. closing consensus): validation 2023–25 **104-75-2, +10.8% ROI, CLV +0.93**; train 2021–22 about break-even. Openers only exist 2021+, so samples are small; CLV is the steadiest signal.
- **Consensus everywhere = median across sportsbooks, aggregators excluded** (#53, #59): openers, closing lines (backtests) and live lines all use it.
- **Publishing (#55):** a new snapshot is inserted only when a game's forecast, prices or picks change; window = next 8 days; `live` model run with `params.job = "publish"`.

## Data conventions
- **Spread sign:** home team's view, **negative = home favored** (CFBD and TSI agree; verified).
- **`team_game_stats`** = one row per team per game = its **offense**; defense is the opponent's row. Efficiency stats are garbage-time filtered; plays/drives are full-game.
- **Division values:** `fbs`, `fcs`, `ii`, `iii`, `unknown` (CFBD `classification`). Teams missing from CFBD `/teams` (mostly NAIA) get placeholder rows with slug `name-<id>`.
- **Times** are UTC, timezone-aware; `parse_utc` rejects naive timestamps. `games.start_time_tbd` marks date-only kickoffs.
- **Market lines** are change-only snapshots; `is_closing` = captured at/after kickoff. History has closing snapshots plus openers (`spread_open`/`total_open`, 2021+; some single-book openers are stale, hence medians). CFBD lines carry no spread/total prices: assume −110.
- **Known gaps** (`tsi check` warns): 47 FBS games without advanced stats (mostly 2014–16), no talent before 2015, some new-FBS teams without returning production.
- CFBD identifies teams by **school name** in stats/talent/returning, so match through our tables.

## Gotchas
- **SQLAlchemy 2.1:** don't `dict(session.execute(...))`; unpack rows in a comprehension. Use `.ext(postgresql.distinct_on(...))`, not `.distinct(cols)`.
- **Upserts:** always go through `db/upsert.py`. Never send the same primary key twice in one batch; de-duplicate first.
- **Neon latency** is ~43ms per round trip. Performance means fewer round trips, not faster Python. The nightly `tsi run` takes ~35 s in Actions; backtests ~5 s.
- **numpy threads:** `tsi/__init__.py` caps BLAS at 1 thread (multithreading made our small solves ~40× slower). Scratch scripts must `import tsi` before numpy.
- **DB tests** build the schema from the ORM, so the immutability trigger is loaded from the initial migration file (`tests/db_integration/conftest.py`). Shared test builders live in `tests/factories.py`. **API tests** seed a tiny 2026 season (`tests/db_integration/api_seed.py`) and override `get_session` + `get_now` (clock pinned) on `create_app(...)`; the test client needs the `httpx2` dev dependency (Starlette 1.9).
- **Deploy order:** when a migration drops or renames a column, apply it **before** pushing code. The nightly job runs whatever is on `main`.
- **Alembic** autogenerate misses primary-key changes; hand-write those. Pass the short constraint name (e.g. `"basis"`), never the full `ck_table_name`.
- **API changes:** run `tsi openapi` and commit `docs/api/openapi.json`, or `tests/api/test_openapi.py` fails. Response shapes are the dataclasses in `services/read/`.
- **Model changes:** rerun `tsi backtest run` (+ `tsi backtest book` for Book changes), then `tsi model fit`, and commit the new artifact. The artifact is written with LF, so an unchanged refit leaves git clean.
- **gitleaks** flags realistic-looking fake keys in tests: use low-entropy values like `"fakekey"`.
- **Windows shell:**
  - PowerShell here-strings mangle inline Python: write scripts to the scratchpad and run them with `python -I` from a neutral directory (a local `types.py` once shadowed the stdlib).
  - Shell heredocs turn `\n` inside Python strings into real newlines: write edit scripts with the Write tool, or use the Edit tool.
  - Commit messages: bash heredoc + `git commit -F` (PowerShell `Set-Content` adds a BOM). `sed` replacements containing `#` need another delimiter.
  - The console is cp1252: set `PYTHONIOENCODING=utf-8` (or write to a file) to print ★/–; use `%#I`, not `%-I`, in `strftime`.
  - The artifact tools reject the short `GAGESW~1` temp path as `out_dir`; use the full `C:\Users\Gage Swann\...` path.
- **GitHub Actions:** `astral-sh/setup-uv` has no floating major tag; pin the exact version (e.g. `v10.3.0`). The nightly job writes to the Neon **dev** branch until Phase 6 (#19).

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
uv run ruff check . ; uv run ruff format .
uv add <pkg>  /  uv add --dev <pkg>

# Live (the nightly job runs `tsi run`)
uv run tsi run                  # ingest -> rate -> grade -> publish (--dry-run, --no-ingest, --week N, --postseason)
uv run tsi rate                 # today's ratings + rankings -> live model_run (--dry-run)
uv run tsi book publish        # board for the next 8 days -> new snapshots + picks (--dry-run, --days, --show)
uv run tsi book grade          # grade locked-snapshot picks of finished games, record closing lines
uv run tsi model rankings       # current Power + Résumé rankings (--season, --top, --by resume)
uv run tsi serve               # read-only API at http://127.0.0.1:8000 (docs at /docs; --reload, --port)
uv run tsi openapi             # regenerate docs/api/openapi.json after any API change (a test checks it)

# Model + backtests
uv run tsi backtest run         # walk-forward backtest: margins, totals, calibration, ATS, edge shrink (--no-save, --lam, ...)
uv run tsi backtest book        # Book record at the opener by market/tier: W-L-P, ROI, Kelly, CLV (--seasons)
uv run tsi backtest export --out-dir DIR   # report CSVs (model + Book tables) for the report card
uv run tsi model fit            # refit production artifact on all completed seasons (commit model/artifacts/current.json)
uv run tsi model elo            # Elo baseline vs. closing line, by season
uv run tsi model compare-sp     # sanity check: TSI final ratings vs. SP+ final (correlation)

# Data
uv run tsi check                # data quality rules; exit 1 on any `fail` (--season, --details)
uv run tsi ingest daily         # refresh current season (part of `tsi run`)
uv run tsi ingest season --season 2014 --through 2026   # all loaders in order (~9 calls/season if not cached)
uv run tsi ingest teams --season 2024     # single loaders: venues, teams, calendar, games, stats, lines, priors, roster
uv run alembic upgrade head     # apply migrations (uses DATABASE_URL_DIRECT)
uv run alembic revision --autogenerate -m "msg"   # after changing models; review before applying
uv run alembic check            # models and DB in sync?
```
Migrations target the Neon **dev** branch locally. Ask before applying to any database.
GitHub: `gh workflow run daily-refresh.yml` triggers the nightly job manually; `gh run list --workflow daily-refresh.yml` shows recent runs.
_Web commands are added when `web/` is scaffolded (Phase 5)._

# 02 – Architecture

## System overview

```
CollegeFootballData API ──► Ingest (Python) ──► PostgreSQL (Neon)
                                                   │
                     Model run (Python): ratings ──┤
                     Prediction engine / book ─────┤
                     Backtests ────────────────────┘
                                                   │
                                              FastAPI (read-only JSON)
                                                   │
                                     Next.js (Vercel, ISR-cached pages)
                                                   │
                                               Public viewers

GitHub Actions (cron) ── runs ingest + model ── triggers Next.js revalidation
```

The Python side owns **all** data and math. The frontend never calculates odds or ratings; it only renders what the API returns. The one exception is the hypothetical matchup tool, which calls an API endpoint that computes on demand.

## Repo layout (monorepo)

```
the-swann-index/
├── backend/
│   ├── pyproject.toml          # uv-managed
│   ├── alembic/                # DB migrations
│   ├── .env.example            # variable names only (real .env is gitignored)
│   ├── src/tsi/
│   │   ├── config.py           # pydantic-settings; the ONLY place env is read
│   │   ├── db/                 # SQLAlchemy models, session, repositories
│   │   ├── ingest/             # CFBD client wrappers, loaders, cache
│   │   ├── model/              # features, priors, ratings fit, résumé
│   │   ├── book/               # score distributions, odds, edges, ledger
│   │   ├── sim/                # season / playoff Monte Carlo (later)
│   │   ├── backtest/           # walk-forward evaluation
│   │   ├── api/                # FastAPI app + routers + schemas
│   │   ├── services/           # orchestration: weekly run, publish, grade
│   │   └── cli/                # `tsi ingest`, `tsi run`, `tsi backtest`... (one file per command group)
│   └── tests/                  # mirrors src/tsi; fixtures/ holds saved CFBD JSON
├── web/
│   ├── .env.example
│   ├── app/                    # Next.js App Router routes (thin)
│   ├── components/<area>/      # one component per file
│   ├── lib/api/                # typed API client + generated types
│   └── ...
├── docs/
├── .github/workflows/
├── CLAUDE.md
└── README.md
```

Module size and layering rules are in [09-conventions.md](09-conventions.md) §2.

## Tech choices

| Concern | Choice | Notes |
|---|---|---|
| Python env | `uv` | Fast installs, lockfile |
| Data | pandas + NumPy + SciPy + scikit-learn | Ridge regression, distributions |
| DB access | SQLAlchemy 2.x + Alembic + psycopg | Migrations from day one |
| API | FastAPI + Pydantic | OpenAPI schema → generate TS types |
| Lint/test (py) | ruff, pytest | |
| Frontend | Next.js (latest stable, App Router), TypeScript | Server Components fetch API |
| Styling | Tailwind CSS + shadcn/ui | |
| Charts | Recharts | visx if something needs more control |
| Tables | TanStack Table | Sortable/filterable rankings |
| Lint (web) | ESLint + Prettier | |
| DB host | Neon Postgres (free tier) | `production` (Neon's default) and `dev` branches, no local Docker needed |
| Web host | Vercel | |
| API host | Render or Fly.io | Cold starts are hidden by ISR caching |
| Scheduling | GitHub Actions cron | |

## Database schema (initial)

All tables include `created_at`. Seasons/weeks follow CFBD conventions (`season_type`: regular/postseason).

| Table | Key columns |
|---|---|
| `teams` | id (CFBD id), school, slug, mascot, abbreviation, color, alt_color, logo_url, venue_id (stable identity only) |
| `team_seasons` | team_id, season, conference, **division** (fbs/fcs/…). Membership changes by year (realignment, FCS→FBS moves), so it never lives on `teams` |
| `venues` | id, name, city, state, latitude, longitude, elevation_m, dome |
| `games` | id, season, week, season_type, start_time (UTC), home_id, away_id, venue_id, neutral_site, conference_game, home_points, away_points, completed |
| `team_game_stats` | game_id, team_id, points, plays, drives, yards, epa_per_play, rush/pass epa_per_play, success_rate, explosiveness, havoc_rate, garbage_time_filtered. **Offense only:** a team's defense for a game is its opponent's row |
| `market_lines` | game_id, provider, spread, spread_open, total, total_open, home_ml, away_ml, fetched_at, is_closing |
| `ingest_log` | endpoint, params (jsonb), season, week, fetched_at, from_cache, row_count, status. Powers frozen-week skipping and the monthly CFBD call budget (cache hits don't count) |
| `priors` | season, team_id, last_season_rating, returning_ppa, talent, prior_rating |
| `model_runs` | id, **kind** (`live`/`backtest`), season, week, season_type, run_at, model_version, params (jsonb), git_sha |
| `team_ratings` | run_id, team_id, **variant** (`raw`/`adjusted`), rating, off_rating, def_rating, pace, rank_power, sor, rank_resume |
| `predictions` | id, run_id, game_id, **variant** (`raw`/`adjusted`), published_at, proj_home, proj_away, spread, total, home_win_prob, sigma_margin, sigma_total, rho, fair/book ML, book spread/total odds. **Insert-only, enforced by a DB trigger** (no UPDATE; DELETE only for backtest runs). The "locked" snapshot is derived (latest `published_at` < `start_time`) |
| `picks` | prediction_id, market (spread/total/ml), side, line_taken, odds_taken, edge, tier (1–3), stake_units, kelly_units, closing_line, closing_odds, result, units_won, graded_at |
| `adjustments` (later) | team_id, points, reason, start_week, end_week, active |
| `sim_results` (later) | run_id, team_id, exp_wins, win_dist (jsonb), conf_title_prob, cfp_prob |

## API (read-only, v1)

| Method | Path | Returns |
|---|---|---|
| GET | `/meta/current` | current season, week, last model run time |
| GET | `/rankings?season&week&type=power\|resume` | ranked team list |
| GET | `/teams` | all teams (slug, name, colors, logo) |
| GET | `/teams/{slug}?season` | team profile, rating history, schedule + win probs |
| GET | `/weeks/{season}/{week}/games` | matchup board with TSI vs. market |
| GET | `/games/{id}` | full game center payload (odds board, distribution, comparison, result/grade) |
| GET | `/book/ledger?season` | picks + running record, ROI, CLV |
| GET | `/model/report?season` | accuracy, calibration, comparison data |
| GET | `/matchup?home&away&neutral` | on-demand hypothetical prediction |

Responses are Pydantic models; the OpenAPI spec generates TypeScript types for `web/lib/api.ts`.

## Data flow per week (in season)

1. **Sunday ~10:00 UTC:** ingest completed games and stats → refit ratings → grade last week's picks → write new `model_run` → revalidate site.
2. **Tuesday & Thursday:** ingest latest market lines → generate predictions for upcoming games → publish snapshots → revalidate.
3. **Lock:** the locked prediction is the latest snapshot published before kickoff (a query, not a scheduled job); picks are graded against it and the closing line.

## Caching & revalidation
- Next.js pages use ISR with tags (`rankings`, `week-{n}`, `team-{slug}`, `game-{id}`).
- After a model run, the workflow calls a protected `/api/revalidate` route on Vercel with a secret token.
- Result: nearly every page view is served from Vercel's cache, and the API is only hit on revalidation and for the matchup tool.

## Environments & secrets
All secrets come from environment variables; none are in code. See [09-conventions.md](09-conventions.md) §3.

| Var | Secret? | Where |
|---|---|---|
| `CFBD_API_KEY` | yes | `backend/.env`, GitHub Actions secret |
| `DATABASE_URL` | yes | `backend/.env` (Neon dev branch), GH secret + API host (production branch) |
| `CFBD_MONTHLY_CALL_BUDGET` | no | `backend/.env` (default 1000); ingest refuses to exceed it |
| `TSI_CORS_ORIGINS` | no | API host (the Vercel URL); `http://localhost:3000` locally |
| `TSI_API_URL` | no | `web/.env.local`, Vercel env |
| `REVALIDATE_TOKEN` | yes | `web/.env.local`, Vercel env + GH secret (server-only; never `NEXT_PUBLIC_`) |

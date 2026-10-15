# 07 – Roadmap

Each phase ends with a working, committed state. **Work one item at a time** (build → test → tick → commit; see [09-conventions.md](09-conventions.md) §1). Tick boxes as items are done. **Timing note:** the 2026 season is in progress (planning began 2026-10-14, ~Week 7). Phases 0–6 are prioritized so TSI is live before bowl season and the CFP.

---

## Phase 0: Environment & repo setup
See [08-setup-windows.md](08-setup-windows.md).
- [x] Install Git
- [x] Install Node.js LTS, uv, Python 3.12 (via uv), GitHub CLI, pre-commit
- [x] Configure git identity; `gh auth login`
- [x] Add `.gitignore`, `.gitattributes`, `.editorconfig`, `backend/.env.example`, `web/.env.example`
- [x] Pre-commit hooks with gitleaks secret scanning (doc 09 §3); verified a fake key is blocked
- [x] Create GitHub repo `the-swann-index`, push these docs as the first commit
- [x] Get CFBD API key; create Neon project; fill in local `.env` files (both verified live)
- [x] Create Neon `dev` branch (child of `production`); point local `DATABASE_URL` at it
- [x] Create `.claude/skills/SOURCES.md` (skill install log; skills are installed per phase, doc 09 §5)

**Done when:** docs are on GitHub, all tools respond to `--version`, and a test commit containing a fake key is blocked by the hook.

## Phase 1: Data foundation
- [x] Scaffold `backend/` (uv, ruff, pytest, `tsi` package, Typer CLI skeleton)
- [x] `tsi/config.py` (pydantic-settings) + test that a missing variable fails clearly without echoing values
- [x] SQLAlchemy models + first Alembic migration (schema in doc 02, incl. `team_seasons`, `ingest_log`)
- [x] CFBD client wrapper with raw-response disk cache + call-budget guard
- Ingest, one loader module per endpoint (pure transforms + idempotent upserts):
  - [x] 5a. venues, teams, team_seasons (`tsi ingest venues`, `tsi ingest teams --season`)
  - [x] 5b. calendar, games (`calendar_weeks`, placeholder teams for unknown opponents)
  - [x] 5c. advanced stats → `team_game_stats` (`tsi ingest stats --season`; `/drives` not needed: drive counts come from the full-game stats)
  - [x] 5d. lines (change-only snapshots + closing flag), talent, returning production (`tsi ingest lines` / `priors`)
- [ ] Test-season ingest (2024); confirm the call count matches the doc 03 budget
- [x] Current-season freshness: finished seasons cached forever, in-progress season expires after 6h (`ingest/freshness.py`)
- [x] Daily refresh: `tsi ingest daily` + GitHub Actions cron at 10:00 UTC (pulled forward from Phase 6). Later phases add stats, rating refit, and publish to this job
- [ ] Backfill 2014–2025 + 2026 to date (spread across sessions if needed). _Done so far: everything for 2024–2026 (teams, calendar, games, stats, lines, priors)._
- [ ] Data quality checks (doc 03) as `tsi check`. Fail on problems in FBS-involved games; only warn on lower divisions (2024–26 has 5 completed D-II/III/NAIA games with no score, and some small-college games never marked final). Also report FBS games missing advanced stats (2024: Army–Rice, Sam Houston–NMSU, Miami (OH)–Kent State, WMU–EMU); the model must handle them
- [ ] Unit tests for loaders (fixtures, no live API in tests). Transforms are covered; the DB half of loaders is still only checked by live runs (a SQLAlchemy 2.1 `dict(result)` bug slipped through in 5d). Add DB-backed loader tests against a throwaway Neon branch or local Postgres

**Done when:** `tsi ingest --season 2026` is idempotent and quality checks pass for all seasons.

## Phase 2: Model v1 + backtest
- [ ] Elo baseline
- [ ] Opponent-adjusted ridge ratings (PPD + EPA), HFA, pooled FCS team
- [ ] Preseason prior + in-season blending (handle missing inputs: teams new to FBS lack returning production, e.g. NDSU and Sacramento State in 2026; 4 FBS games in 2024 lack advanced stats)
- [ ] Walk-forward backtest harness + metrics + saved runs
- [ ] Tune on 2015–2022, validate on 2023–2025
- [ ] Résumé (SOR) and SOS calculations
- [ ] Notebook or report summarizing results vs. closing line / SP+ / Elo

**Done when:** validation MAE and calibration meet the targets in doc 01 (or the gap is understood and documented).

## Phase 3: Prediction engine & book core
- [ ] Score projection with pace
- [ ] Bivariate-normal distribution; fit σ/ρ from backtest
- [ ] Market pricing: fair + vigged spread, total, ML, team totals, alt ladders
- [ ] Consensus market lines + no-vig implied probabilities + edges
- [ ] Pick rules, ★ tiers, flat + ¼ Kelly staking
- [ ] Snapshot publishing, locking, grading, CLV
- [ ] Backtest the book: historical ATS/O-U/ROI/CLV by tier
- [ ] `tsi run --season --week` does ingest → rate → predict → publish end to end

**Done when:** one command produces a full, graded week, and calibration checks (doc 05 §8) pass.

## Phase 4: API
- [ ] FastAPI app, routers, Pydantic schemas for all v1 endpoints (doc 02)
- [ ] CORS for the web origin; response caching headers
- [ ] API tests against a seeded test DB
- [ ] Export OpenAPI spec

**Done when:** every endpoint returns real data locally and tests pass.

## Phase 5: Frontend MVP
- [ ] Review + install Phase 5 skills (`frontend-design`, `nextjs`, `webapp-testing`; doc 09 §5)
- [ ] Scaffold `web/` (Next.js, TS, Tailwind, shadcn/ui, Recharts, TanStack Table)
- [ ] Generate TS types from OpenAPI; typed API client
- [ ] Layout, nav, theme, `UpdatedFooter`
- [ ] Rankings page
- [ ] Matchup board
- [ ] Game center
- [ ] Team page
- [ ] Responsive pass on phone widths

**Done when:** all four core pages work against the local API with real 2026 data.

## Phase 6: Deploy & automation (go live)
- [ ] Deploy API (Render/Fly) against Neon `production`
- [ ] Deploy web to Vercel; env vars set
- [ ] `/api/revalidate` route with secret token
- [ ] GitHub Actions: Sunday ratings run, Tue/Thu lines + predictions, CI (ruff, pytest, lint, typecheck, build)
- [ ] Failure alerting (workflow failure email is fine)
- [ ] `security-review` pass; confirm no secrets in repo history; all secrets set in GH/Vercel/API host
- [ ] Project skill `tsi-weekly-run` (via `skill-creator`) documenting the operator runbook

**Done when:** the public URL updates on its own for a full week without manual intervention.

## Phase 7: Polish & secondary pages
- [ ] TSI Book page
- [ ] Model/methodology + report card page (calibration chart)
- [ ] Hypothetical matchup tool
- [ ] Dynamic OG images; SEO metadata
- [ ] README screenshots/GIF, architecture diagram, live link
- [ ] Lighthouse ≥ 90

## Phase 8: Season simulation & playoff
- [ ] Monte Carlo season sim with rating uncertainty
- [ ] Projected wins, conference title odds
- [ ] CFP selection approximation + bracket page (verify current format first)
- [ ] Futures fair odds

## Phase 9: Manual adjustments
- [ ] `adjustments` table + CLI (`tsi adjust add/list/expire`)
- [ ] Raw vs. adjusted predictions stored and displayed
- [ ] Report card: adjusted vs. raw accuracy

## Phase 10: FCS expansion
- [ ] Backfill FCS games/stats
- [ ] Individual FCS ratings (replace pooled FCS team), cross-division linking
- [ ] FCS rankings view + division filter across the site

## Phase 11: Stretch
- [ ] Monte Carlo score sim with key numbers & push probabilities
- [ ] First-half markets
- [ ] Live odds + line movement (The Odds API)
- [ ] Team-specific HFA, travel, rest
- [ ] Model v2: gradient-boosted ensemble on top of ratings
- [ ] AI-written game previews

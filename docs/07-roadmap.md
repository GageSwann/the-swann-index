# 07 – Roadmap

Each phase ends with a working, committed state. **Work one item at a time** (build → test → tick → commit; see [09-conventions.md](09-conventions.md) §1). Tick boxes as items are done. **Timing note:** the 2026 season is in progress (planning began 2026-10-14, ~Week 7). There's no launch deadline (decision #27): quality over speed, and Phase 2 gets full tuning before go-live.

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
- [x] Test-season ingest (2024); confirm the call count matches the doc 03 budget (9 calls per season: teams, calendar, games, 2× stats, lines, talent, returning, plus 1 for venues once. That's under the 10–25 estimate)
- [x] Current-season freshness: finished seasons cached forever, in-progress season expires after 6h (`ingest/freshness.py`)
- [x] Daily refresh: `tsi ingest daily` + GitHub Actions cron at 10:00 UTC (pulled forward from Phase 6). Later phases add stats, rating refit, and publish to this job
- [x] `tsi ingest season --season X [--through Y]`: every loader in dependency order
- [x] Backfill 2014–2026 (all 13 seasons; 2014–2023 took 81 calls). 31,200 games, 27,368 team-game stat rows, 37,403 line snapshots
- [x] Data quality checks as `tsi check` (14 rules, `quality/checks.py`): 7 `fail` rules (look-ahead, integrity, FBS scores/stats) and 7 `warn` rules for known CFBD gaps. All seasons: **0 failures**. Warnings: 47 FBS-vs-FBS games without advanced stats (mostly 2014–16), 16 FBS team-seasons without returning production (new FBS members, 2021 ODU/UConn), App State–Liberty 2024 cancelled, small-college missing scores
- [x] Loader tests: transforms on saved fixtures, plus DB-backed tests (`tests/db_integration/`) that load fixtures through a fake CFBD into a throwaway schema in the dev database. These caught a real bug: an unknown venue would have crashed the games loader

**Done when:** `tsi ingest --season 2026` is idempotent and quality checks pass for all seasons. ✅ **Phase 1 complete (2026-10-14).**

**Phase 2 data notes:** 2014 has no talent (247 composite starts 2015); 2020 is COVID-shortened (534 FBS-vs-FBS games; FBS teams played 0–13, avg 8.6, and some programs sat out entirely); the prior needs fallbacks for missing returning production.

## Phase 2: Model v1 + backtest
Baseline exactly as doc 04 (decision #28). Key decisions: two rating sets (`season` for rankings, `predictive` for predictions, #23), dynamic Résumé vs. a #12 benchmark (#24), daily refits (#25), 2020 treated normally (#26).
- [x] Elo baseline (`model/elo.py`, `tsi model elo`). Tuned on train: K=45, HFA=55, carryover 0.90. **Validation 2023–25: MAE 13.15 vs. Vegas 12.00; straight-up 70.5% vs. 72.7%.** The main model must clearly beat this
- [x] Opponent-adjusted ridge ratings (PPD + EPA), HFA, pooled FCS team (`model/ratings/`, `tsi model ratings`). Walk-forward, this season only, refit daily like production. Preliminary λ=2, PPD weight 0.75. **Validation, both teams 4+ games: MAE 12.72 vs. Elo 12.94 vs. Vegas 12.06.** Early-season games (<4) are weak at 15.55; the prior is meant to fix that for `predictive`. The 47 games without advanced stats have no drive counts, so v1 excludes them
- [x] `season` ratings (this season only) + `predictive` ratings (prior fading to zero by a cutoff; `model/blend.py`, `services/walk_forward.py`); migration 4 adds `basis`, `games_played`, `provisional` to `team_ratings` (applied)
- [x] Preseason prior with fallbacks (`model/prior.py`): a separate least-squares model for every subset of inputs (last FBS rating, talent, returning production), fit on 2015–22 targets. Re-tuned for maximum accuracy (#33): prior worth 6 games, gone after 14. **Validation: predictive MAE 12.79 vs. Elo 13.15 vs. Vegas 12.00 (within the ~1 pt target); SU 71.0%** (target 72%)
- [x] SP+ sanity check (`tsi model compare-sp`): TSI final `season` ratings vs. SP+ final, 2015–25. No table needed (finished seasons are cached on disk forever). **Mean correlation 0.948 (ranks 0.939); 2021+ 0.96–0.98; 2020 0.82.** TSI consistently rates option teams (Army, Air Force) higher; to investigate. Comparison only, never a model input
- [x] Model improvements round 1 (doc 04 §12): stacking B1 + success rate B5 + learned rankings blend B14 adopted; recency B2 rejected. **v1.1 validation: predictions 12.47 vs. Vegas 12.00 (SU 72.2% ✅), rankings 13.37**
- [x] B8 richer prior: returning passing PPA, 4-year recruiting average, net transfer portal (2021+), new-head-coach flag (`tsi ingest roster`; migration 5 applied; backfilled 2014–26). **Validation 12.47 → 12.40; early season 12.74 → 12.55**
- [x] Model improvements round 2: B7 split pooled FCS / lower divisions (kept: no MAE change, fixes Résumé SOS); option teams checked (no bias: +1.18 ±1.70, Vegas +1.83); B6 context σ rejected (no Brier/log-loss gain); λ re-checked (2 still best). B11 rating uncertainty deferred to the API/frontend phases (display only)
- [x] Production model: `tsi model fit` fits the prior model, stack, Elo scale and σ on all completed seasons (2015–25) → `model/artifacts/current.json` (committed, versioned)
- [x] Walk-forward backtest harness + metrics + saved runs: `tsi backtest run` (season/predictive/Elo/Vegas tables, calibration bins, ATS by edge size), saved to `model_runs` (kind `backtest`, config + metrics + git SHA). σ fit by log loss (#34) → calibration within ±3 in 4 of 5 bins. ATS vs. closing 50.8%; no edge yet
- [x] Tune on 2015–2022, validate on 2023–2025 (λ, rankings blend weights, stack weights and penalty, σ; the prior fade is now learned by the stack)
- [x] Résumé (SOR) vs. a #12 benchmark using opponents' **current** ratings, plus SOS (`model/resume.py`, `services/rankings.py`, `tsi model rankings`). σ 15.7 (log-loss fit of `season` margins, 4+ games). Stored daily with the nightly ratings (next item)
- [x] Daily job: `tsi rate` after ingest → a `live` model_run + `team_ratings` (`season` with Power/Résumé ranks, `predictive` per team); ~2 s. CFBD client now retries transient failures (an Oct 18 timeout failed one nightly run)
- [x] Report summarizing results vs. closing line / SP+ / Elo: **TSI model report card** (claude.ai artifact https://claude.ai/artifact/AEndkhJAt49YQNJcWC2i7v, private until shared), data from `tsi backtest export`

**Done when:** validation MAE and calibration meet the targets in doc 01 (or the gap is understood and documented), and the daily job produces fresh 2026 rankings.

## Phase 3: Prediction engine & book core
- [x] Score projection with pace (totals stack, v1.2: val total MAE 12.87 vs. Vegas 12.68)
- [x] Bivariate-normal distribution; fit σ/ρ from backtest (σ total grows with total; ρ ∝ margin; cover/over calibration at the close fails, see doc 05 §8)
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

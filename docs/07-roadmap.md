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
- [x] Résumé (SOR) vs. a #12 benchmark using opponents' **current** ratings, plus SOS (`model/resume.py`, `services/compute_rankings.py`, `tsi model rankings`). σ 15.7 (log-loss fit of `season` margins, 4+ games). Stored daily with the nightly ratings (next item)
- [x] Daily job: `tsi rate` after ingest → a `live` model_run + `team_ratings` (`season` with Power/Résumé ranks, `predictive` per team); ~2 s. CFBD client now retries transient failures (an Oct 18 timeout failed one nightly run)
- [x] Report summarizing results vs. closing line / SP+ / Elo: **TSI model report card** (claude.ai artifact https://claude.ai/artifact/AEndkhJAt49YQNJcWC2i7v, private until shared), data from `tsi backtest export`

**Done when:** validation MAE and calibration meet the targets in doc 01 (or the gap is understood and documented), and the daily job produces fresh 2026 rankings.

## Phase 3: Prediction engine & book core
- [x] Score projection with pace (totals stack, v1.2: val total MAE 12.87 vs. Vegas 12.68)
- [x] Bivariate-normal distribution; fit σ/ρ from backtest (σ total grows with total; ρ ∝ margin; cover/over calibration at the close fails, see doc 05 §8)
- [x] Market pricing: fair + vigged spread, total, ML, team totals, alt ladders (`book/pricing.py`)
- [x] Consensus market lines + no-vig implied probabilities + edges (shrunk toward the line, #52/#53)
- [x] Pick rules, ★ tiers, flat + ¼ Kelly staking (`book/picks.py`; #54)
- [x] Snapshot publishing, locking, grading, CLV (`tsi book publish` / `tsi book grade`; #55)
- [x] Backtest the book: historical ATS/O-U/ROI/CLV by tier (`tsi backtest book`; #56)
- [x] `tsi run` does ingest → rate → grade → publish end to end, live only (`--week` limits publishing; no past-week replays, #57); runs nightly

**Done when:** one command produces a full, graded week, and calibration checks (doc 05 §8) pass.

## Phase 4: API
- [x] FastAPI app, routers, schemas for all v1 endpoints (doc 02; read models in `services/read/`, `tsi serve`; #60)
- [x] CORS for the web origin; response caching headers (+ ETag/304, gzip; `api/caching.py`; #61)
- [x] API tests against a seeded test DB (`tests/db_integration/test_api.py` + `api_seed.py`; #62)
- [x] Export OpenAPI spec (`tsi openapi` → `docs/api/openapi.json`, drift-tested; #63)

**Done when:** every endpoint returns real data locally and tests pass.

## Phase 5: Frontend MVP
- [x] Review + install Phase 5 skills (`frontend-design`, `webapp-testing`, `react-best-practices` in place of `nextjs`; `.claude/skills/SOURCES.md`; #66)
- [x] Scaffold `web/` (Next.js 16.4, TS, Tailwind 4, shadcn/ui, Recharts, TanStack Table, ESLint + Prettier; #67)
- [x] Generate TS types from OpenAPI; typed API client (`web/lib/api/`: openapi-typescript + openapi-fetch, cached + tagged reads; #68)
- [x] Layout, nav, theme, `UpdatedFooter` (design tokens in doc 06; #69)
- [x] Rankings page (Power/Résumé, Top 25/all, conference filter, sortable table, weekly Δ arrows, off/def ranks; #70, #79)
- [x] Matchup board (`/week` → current week; cards, filters, sort, TSI vs. Vegas, plays, finals; #71)
- [x] Game center (header, plays, odds board, margin chart, alt ladders, tale of the tape, rating trends, prediction history; #72)
- [x] Team page (header, rank profile, rating trend, schedule with published or "if played today" odds; #73)
- [x] TSI Book page (season record, units chart, record by market + tier, filterable pick history, how it works; #75)
- [x] Model page (backtest report served by the API; report card, by-season chart, calibration, market checks, Book replayed, method, versions; #76)
- [x] Responsive pass on phone widths (360/390 px audit: no page overflow, phone layouts for odds board + schedule, pinned rankings columns, ≥ 24 px targets; #74)

**Done when:** all core pages (rankings, board, game, team, Book, Model) work against the local API with real 2026 data.

## Phase 6: Deploy & automation (go live)
- [x] Deploy API (Render/Fly) against Neon `production` (Render free web service `tsi-api`, Ohio, Docker; live data verified identical to a fresh copy; #78, #82)
- [x] Deploy web to Vercel; env vars set (https://the-swann-index.vercel.app, root `web`, `TSI_API_URL` + `REVALIDATE_TOKEN`; #83)
- [x] `/api/revalidate` route with secret token (POST, bearer token, `revalidateTag("tsi", "max")`; #80)
- [x] GitHub Actions: keep the nightly `tsi run` (10:00 UTC) and revalidate the site after each run; CI (ruff, pytest, lint, typecheck, build) (#75, #80; end-to-end run verified 2026-10-28, #83)
- [x] Failure alerting (GitHub email on failed workflows, enabled by the owner; #83)
- [x] `security-review` pass; confirm no secrets in repo history; all secrets set in GH/Vercel/API host (#81; GH: CFBD_API_KEY, DATABASE_URL, REVALIDATE_TOKEN; Render: DATABASE_URL; Vercel: REVALIDATE_TOKEN)
- [x] Project skill `tsi-weekly-run` (via `skill-creator`) documenting the operator runbook (`.claude/skills/tsi-weekly-run/`: daily check, re-run/refresh, weekly review script, deploys/rollbacks, Neon branches + migrations, secret rotation, troubleshooting; #84)

**Done when:** the public URL updates on its own for a full week without manual intervention. ✅ **Phase 6 complete (2026-11-03):** the scheduled nightly job succeeded on 7 consecutive days (Oct 28 – Nov 3) and the site showed each day's run; the one manual run in that span (Oct 29) only filled the new season sim early.

## Phase 7: Polish & secondary pages
- [x] TSI Book page (built in Phase 5 at the owner's request; #75)
- [x] Model/methodology + report card page (calibration chart) (built in Phase 5; #76)
- [x] Hypothetical matchup tool (`/matchup`: shareable GET form, scoreboard, TSI's line, margin chart, alt lines, tale of the tape; #85)
- [x] Dynamic OG images; SEO metadata (link previews for the site, teams, games and matchups; titles + descriptions; robots/sitemap with indexing off until `ALLOW_INDEXING=1`; #86)
- [x] README screenshots, architecture diagram (Mermaid), live link (#92)
- [x] Lighthouse ≥ 90 (performance: desktop 100 everywhere, mobile medians 88–97 with 98–99 on every page in runs without the local harness stall; accessibility + best practices 100; SEO capped by the deliberate noindex; #87)
- [x] Rankings side widget: biggest risers/fallers over the past week (#88)
- [x] Résumé drill-down: on the team page (Résumé card + "#12 team wins" schedule column, linked from the rankings' SOR), not a separate page (#89)

## Phase 8: Season simulation & playoff
- [x] Monte Carlo season sim with rating uncertainty (`tsi sim season`: published forecasts + a per-team shift τ(week) fit on 2015–22, better win-total log score than independent games on 2023–25; #94)
- [x] Projected wins, conference title odds (`tsi sim season`: simulated standings with simplified tiebreakers, Sun Belt divisions, neutral-site title games that count as wins; #96)
- [x] Store the sim nightly (`sim_results`, part of `tsi run`) and show projected wins, win out and title odds on the rankings and team pages (#98; CFP odds come with the projector)
- [x] CFP selection approximation + bracket page (2026–27 format verified by the owner: doc 05 §7.2, #95; Résumé as the committee stand-in, #100; stored nightly + `/playoff` page with a projected bracket and odds table, #101)
- [x] Futures fair odds (playoff, conference title and national title chances as fair American odds in `/playoff`; title odds on the page, #101)

✅ **Phase 8 complete (2026-11-03):** stored by every nightly run since Oct 29; live API and site checked (field odds sum to 12, title odds to 1, all pages load cleanly).

## Phase 9: Manual adjustments
- [x] `adjustments` table + CLI (`tsi adjust add/list/expire`): offense/defense points per game, a reason and a kickoff window; expiring closes the window, rows are never deleted (#103)
- [x] Raw vs. adjusted predictions stored and displayed: adjusted games publish a `raw` and an official `adjusted` row (picks on the adjusted one); the Book and season sim use adjusted, rankings stay raw; "Adjusted" note with the reason and the raw numbers on game cards, the game center and team pages (#104)
- [x] Report card: adjusted vs. raw accuracy: raw and adjusted rows of each finished adjusted game scored against the result (margin, total, winners, closer/further), overall and per adjustment, on the Model page and in `tsi adjust report` (#105)

✅ **Phase 9 complete (2026-11-03):** adjustments recorded with `tsi adjust`, applied to predictions, the Book and the season sim (rankings stay raw), shown with the raw numbers, and judged on the Model page.

## Phase 10: FCS expansion
Scoped 2026-11-03 (decision #107). **No backfill or new CFBD calls needed:** every FCS game since 2014 is loaded; FCS-vs-FCS advanced stats (drives, plays, success rate: complete) and betting lines exist from **2022** on (~500–700 games a season). Before 2022 only scores exist, so FCS stays pooled for 2014–21. FCS priors: recruiting yes, talent only 2015–23, returning production none.
- [x] **Data readiness:** `tsi check` warns on FCS games (2022+) missing stats for a side (`fcs_game_missing_stats`: 265, all whole games, 126 in 2022 → 22 in 2025); FCS coverage table in doc 03; `FCS_STATS_FROM = 2022` in `tsi/divisions.py`
- [x] **Model experiment (scratchpad first):** adopted variant "Cp" (#109): FBS validation 12.403 → 12.394, FCS-vs-FCS 14.37 → 12.46 (close 11.93), FBS-vs-FCS 25.85 → 14.37 (close 11.80). Planned: individual FCS ratings from 2022 with an FCS division level (teams shrink toward the FCS mean, not the FBS mean), pooled before 2022; FCS priors from last season's rating + recruiting (division mean when missing). Adopt only if FBS train doesn't get worse and FBS validation stays ≤ 12.40; also report FCS-game MAE vs. the closing line (2023–25) and FBS-vs-FCS games
- [x] **Build it in:** ratings, priors and stack features for FCS; walk-forward backtest saved; `tsi model fit` (v1.3); FBS Book backtest checked (moved up: validation 110-68-1, +17.9%); live-vs-backtest parity exact on 500 games incl. FCS (#110)
- [ ] **Nightly run:** store FCS `team_ratings` (no schema change), Power and Résumé ranks within each division (FCS Résumé vs. a typical **#10 FCS team**, #91); publish predictions for FCS games with no picks; the season sim stays FBS
- [ ] **FCS Book backtest** (2023–25, median opener, CLV): FCS picks are turned on only if it earns it, as a separate owner decision
- [ ] **API:** `division` (fbs default / fcs / all) on rankings and the team list; FCS games on the week board; FCS team profiles; cross-division matchups
- [ ] **Site:** FBS / FCS / All toggle on rankings (FBS default; ranks within division, "All" on one scale); division filter on the week board and team list; FCS team pages with every section (the projection card shows the record and says FCS projections come later); the Playoff page stays FBS
- [ ] Résumé breakdown (#89, #90) for the expansion: opponents use their own stored rating whenever one exists (pooled rating only as a fallback, `services/read/resume_view.py`); FCS teams get the Résumé card; FCS résumés are measured against a typical **#10 FCS team** (owner, #91); the "SOR rebuilt = stored SOR" check must still hold for every rated team

## Phase 11: Stretch
- [ ] FCS season simulation: projected wins, conference titles, the 24-team FCS playoff (moved from Phase 10, #107)
- [ ] Monte Carlo score sim with key numbers & push probabilities
- [ ] First-half markets
- [ ] Live odds + line movement (The Odds API)
- [ ] Team-specific HFA, travel, rest
- [ ] Model v2: gradient-boosted ensemble on top of ratings
- [ ] AI-written game previews

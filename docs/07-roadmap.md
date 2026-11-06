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
- [x] **Nightly run:** store FCS `team_ratings` (no schema change), Power and Résumé ranks within each division (FCS Résumé vs. a typical **#10 FCS team**, #91); publish predictions for FCS games with no picks; the season sim stays FBS (#111: 128 FCS teams ranked, ~60 FCS-vs-FCS games a week published, 0 picks)
- [x] **FCS Book backtest** (2023–25, median opener, CLV): FCS picks are turned on only if it earns it, as a separate owner decision (#112: not earned yet: FCS-vs-FCS has almost no openers; FCS totals show no CLV; FBS-vs-FCS spreads show CLV +0.91 with an FCS-fit trust, on thin training data. Recommendation: keep off, revisit after 2026 with live snapshots)
- [x] **API:** `division` (fbs default / fcs / all) on rankings and the team list; FCS games on the week board; FCS team profiles; cross-division matchups (#113: also on the week board; `all` is Power only)
- [x] **Site:** FBS / FCS / All toggle on rankings (FBS default; ranks within division, "All" on one scale); division filter on the week board and team list; FCS team pages with every section (the projection card shows the record and says FCS projections come later); the Playoff page stays FBS (#115: separate cached routes per division)
- [x] Résumé breakdown (#89, #90) for the expansion: opponents use their own stored rating whenever one exists (pooled rating only as a fallback, `services/read/resume_view.py`); FCS teams get the Résumé card; FCS résumés are measured against a typical **#10 FCS team** (owner, #91); the "SOR rebuilt = stored SOR" check must still hold for every rated team (#114: FCS breakdown vs. the #10 FCS team; opponent ranks shown within the team's own division; SOR rebuilt = stored for all 266 ranked teams (138 FBS, 128 FCS))

✅ **Phase 10 complete (2026-11-04):** FCS teams rated individually from 2022 (model v1.3), ranked within their division nightly, FCS games published (no picks; FCS Book backtest not earned yet), and shown on the site with FBS / FCS / All views.

## Phase 11: Stretch
- [x] FCS season simulation: projected wins, conference titles, the 24-team FCS playoff (moved from Phase 10, #107; #125: one simulation for both divisions, FCS champions from the standings, 24-team bracket by the FCS Résumé, which picked 88/96 real playoff teams 2022–25; `/playoff/fcs`)
- [x] Key numbers & push probabilities (#118: whole-number margin/total tables with learned key-number weights instead of a Monte Carlo; margin log loss 4.168 → 4.027 on validation; pushes priced on whole-number lines; picks unchanged)
- [x] Team-specific HFA, travel, rest (#120: rest / bye / short-week adjustment adopted, model v1.4; travel, time zones, altitude and team-specific home field tested and rejected)
- [x] Model v2: gradient-boosted ensemble on top of ratings (#121: tested, rejected: worse than the linear stack out of sample; leftover error has no pattern)
- [x] New box-score signals from the cached advanced stats (#122: second-level rushing yards + power success adopted, model v1.5: validation 12.390 → 12.349; others rejected)
- [x] Found while scoping the FCS sim: FBS-vs-FCS margins overshot by ~30% and totals ran low (#124: margin scale + total offset, model v1.6; validation margin MAE 14.34 → 12.56, totals 12.62 → 12.31)

✅ **Phase 11 complete (2026-11-05):** FCS season sim and 24-team FCS playoff (#125), key numbers and push prices (#118, #119), rest / bye / short week (model v1.4, #120), second-level yards + power success (v1.5, #122), FBS-vs-FCS margin scale (v1.6, #124); boosting (#121) and totals signals (#123) rejected. First-half markets and live odds were dropped (#128), AI game previews too (#130).

## Phase 12: Fixes from the owner's review (planned 2026-11-05, nothing built yet)
Found by the owner on the live site. Ordered by impact: the first two cause most of the "the site didn't update" reports. Each item follows the usual loop (build → test → tick → commit → push) and stops for review. Items marked **ask** need the owner's OK first (workflow, outward-facing, or a product choice).

**Before Phase 12:** ~~finish #125's site push (`/playoff/fcs`) once the live API serves `seeds`~~ done 2026-11-05 (the bracket is drawn from `rounds`; CI had been red since `32baf0d`, so the API only deployed then); the old `Playoff.format` field was dropped the same day.

- [ ] **12.1 Run the nightly job at 6–7 AM Eastern** (owner chose cron-job.org, #126).
  - *Problem:* the job is meant to run at 5–6 AM Eastern but lands around noon.
  - *Cause (checked):* the cron is `0 10 * * *` (10:00 UTC), but GitHub started the last seven scheduled runs **5½–10 hours late** (15:38–20:06 UTC). Scheduled workflows aren't guaranteed to start on time, and the top of the hour is the busiest slot.
  - *Plan:* trigger the run from an outside scheduler at **11:00 UTC** (6 AM EST / 7 AM EDT, inside the window all year) through GitHub's `workflow_dispatch` API, using a fine-grained token that can only start this repo's workflows. Options:
    - **cron-job.org** (free, on time to the minute; recommended);
    - **Vercel Cron** (Hobby plan: once a day, fires anywhere in the hour, so 7–8 AM during daylight time).
  - Keep the GitHub schedule as a later backup (e.g. 14:23 UTC) that skips itself when today's run already happened.
  - *Done when:* a week of runs all start between 6 and 7 AM Eastern.
  - *Built 2026-11-05:* the workflow takes `workflow_dispatch` from cron-job.org and keeps GitHub's schedule at 14:23 UTC as a backup that skips itself after a successful run that UTC day (`gate` job). The owner's fine-grained token (Actions read/write, this repo only) and the cron-job.org job (daily 11:00 UTC) were set up the same day; its test run started a full nightly run that succeeded. Left: a week of on-time runs.
- [x] **12.2 The site shows each run's results right away.** (verified 2026-11-05 on the 22:28 UTC run: Merrimack's team page, cached before the run and not pre-visited, showed "Proj. 0 – 53" before and "Proj. 2 – 55" on its first visit after (Vercel `REVALIDATED`, 1.15 s), matching the API; pre-visited pages served from cache in ~0.2 s; 60 pages rebuilt in 64 s, all 200)
  - *Problem:* team pages kept old schedules after a run, and the FCS rankings took a long time to appear.
  - *Cause (checked):* after a run, `/api/revalidate` calls `revalidateTag("tsi", "max")`. That only marks pages stale: the **first visit after a run still gets yesterday's page** while the new one builds in the background, and only the 7 pages the job pre-visits get past that. Team pages are never pre-visited, so the first person to open one sees the old schedule.
  - *Plan:* switch to `revalidateTag("tsi", { expire: 0 })`, the Next.js 16 setting for refreshes triggered from outside the site, so the next visit waits for fresh data instead of showing old data.
  - Measure how long a team page takes to build fresh on Render's free tier (0.1 CPU).
  - Pre-visit a few more pages: `/playoff/fcs`, `/rankings/all`, `/week/{week}/all`, plus the Top 25 team pages if the run time allows. Changing the pre-visit list changes the nightly workflow, so **ask**.
  - *Done when:* right after a run, every page (a team page nobody has opened yet included) shows the new data.
  - *Built 2026-11-05:* `revalidateTag("tsi", { expire: 0 })`; a team page builds fresh in 0.8-1.4 s on the live site. The job pre-visits 60 pages once each (owner: "all of them"): the 10 main pages (`/playoff/fcs`, `/rankings/all`, this week's All view added) and the FBS and FCS Power Top 25 team pages, with 2 retries per page; one pass measured 43 s, no failures. Confirmed on the next run (above).
- [x] **12.3 No negative projected points.** (#132, model v1.7: FCS-mismatch total bump + underdog floor ≥ 1 point on every forecast; site never shows a score below 0; validation FBS vs. FCS totals 12.335 → 12.005, 0 negative projections, Book unchanged at a fixed shrink)
  - *Problem:* Wake Forest–Merrimack showed a 57.5-point margin with a 48.7 total, so Merrimack was projected at −4.4 points. v1.6 (#124) shrank the margin to 53.4, but it's still −2.4.
  - *Cause:* scores are (total ± margin) / 2, and the totals model doesn't know that a lopsided game still has a floor for the underdog. In the #124 data, FBS-vs-FCS totals ran low by **+0.25 points per point of predicted margin** (2023–25).
  - *Plan (experiment first):* let the total grow with the size of the predicted margin in lopsided games. Candidates:
    - a |margin| term in the totals correction;
    - a learned floor on the underdog's expected points.
  - Fit on 2015–22, score totals MAE and the Book on 2023–25, for FBS-vs-FCS games and FBS blowouts.
  - Separately, the displayed score never goes below 0 even if a projection would.
  - *Done when:* no projected score is negative and totals in lopsided games are no worse (ideally better).
- [x] **12.4 FCS Résumé measured against a typical #24 FCS team.** (#133: from the 2026-11-06 run; breakdown = stored SOR exactly for all 128 FCS teams; selection check #24 84/96 + 24/32 seeds vs. #10 83/96 + 24/32, same rebuilt rules)
  - *Why:* the bar should match the 24-team FCS field, like the FBS #12 for the 12-team CFP. This reverses #91 (#10).
  - *Plan:* change `FCS_BENCHMARK_RANK` from 10 to 24. That moves stored SOR from the next run, the Résumé breakdown text ("#24 FCS team") and the FCS playoff projection.
  - Rerun the FCS selection check (with #10: 88 of 96 real playoff teams, 2022–25) and report the number with #24.
  - *Done when:* the FCS Résumé and its breakdown use #24, the breakdown still adds up to the stored SOR for every FCS team, and the selection check is recorded.
- [ ] **12.5 Arrows and biggest movers compare with the previous Sunday** (owner's rule, #126).
  - *Problem:* movement compares with "the newest run at least 7 days earlier" (`run_and_week_ago`), which can be any weekday.
  - *Rule:* Sunday's rankings are the official weekly poll (the Sunday run comes after Saturday's games). Rankings still update daily, but arrows and biggest movers always compare with the **most recent Sunday before today** (Eastern date):
    - **on Sunday**, the change since the previous Sunday (the week's official move);
    - **Monday–Saturday**, the change since that Sunday, moving with midweek results.
  - *Owner's example:* Central Michigan is #91 on Sunday and wins Tuesday to #75: ▲16. Saturday's results shuffle it to #81: ▲10. That Sunday shows ▲10 and #81 becomes the baseline. It wins again the next week to #61: ▲20, not ▲30.
  - *Plan:* pick the baseline run by date (the last run on that Sunday) in the rankings and movers queries.
  - *Edge cases:* the season's first weeks, before there are two Sundays; a Sunday with no run (use the latest run before that Sunday ended); FBS and FCS lists alike.
  - *Done when:* the example above reproduces in a test with fixed run dates, and on the live site Sunday's arrows match the previous Sunday's ranks.
  - *Built 2026-11-05 (#134):* `run_and_baseline` + `baseline_cutoff` (`db/queries/runs.py`); the example passes step by step in `tests/db_integration/test_run_queries.py`. Left: check the live site on Sunday Nov 8.
- [x] **12.6 The All view of This week shows FCS ranks.** (#135: muted "FCS 8" chip, contrast 5.3:1 light / 5.5:1 dark; checked at 1440/390/360 px in both themes)
  - *Problem:* only FBS Top 25 ranks appear.
  - *Plan:* show FCS Top 25 ranks too, marked as FCS ("FCS #3") in a distinct, contrast-checked style of our choosing (owner has no preference, #126), as the FCS tab already ranks them.
  - Check desktop and 360/390 px.
- [x] **12.7 Biggest movers: long names overlap the rank change.** (2026-11-05: the name's wrapper is a flex box, so `TeamLink` shrinks and truncates, with the full name on hover; the playoff bracket had the same pattern and got the same fix, plus `min-w-0` on its grid columns. Reproduced first: "Florida International" overlapped at 1280/1536 px; after: no overlap and no sideways scroll at 1536/1280/1024/390/360 px, also with a 45-character stress name in every bracket slot)
  - *Example:* Florida International.
  - *Plan:* let the name truncate (a flex container with `min-w-0` around `TeamLink`, the same fix as the playoff bracket) or wrap. Check at desktop and phone widths.

**Owner's answers (2026-11-05, #126):** 12.1 cron-job.org; 12.5 compare with the most recent Sunday before today, as written above; 12.6 no preference on the FCS rank style. Still to set up with the owner when 12.1 starts: a fine-grained GitHub token that can only start this repo's workflows, stored in cron-job.org (never in the repo).

## Phase 13: Frontend overhaul (requested 2026-11-05, planned only)
Starts after Phase 12. A full redesign of the public site; the Book becomes the owner's private tool. Design work uses the `frontend-design` skill (plan → review against the brief → build → screenshot critique), charts the `dataviz` skill, checks the `webapp-testing` skill at desktop and 360/390 px, and keeps Lighthouse ≥ 90 (#87).

**Look and feel**
- [x] **13.1 Neon-inspired lighting, used sparingly.** (#137, built 2026-11-06 after two specimen rounds: black-and-white palette ("black swan" / "white swan"), Instrument Sans, team-colored glows and a border light on the scoreboard; sweeps dropped, #1 lit on hover only; games of the week and the champion path get their light in 13.4 / 13.6)
  - *Brief:* the behavior of light, not a retro neon theme:
    - soft layered glows and bloom around key elements;
    - light sweeps across buttons and cards on hover;
    - highlights that travel around borders.
  - *Where:* only as accents on interactive states (hover, focus, the selected tab) and focal points (game of the week, the playoff champion path, #1). Everything else stays calm.
  - *Colors:* the existing brand tokens (doc 06) and team colors only; no new hues.
  - *Rules:*
    - CSS only (gradients, `box-shadow`/`filter` bloom, a conic-gradient border sweep), no heavy libraries;
    - every animation off under `prefers-reduced-motion`;
    - focus rings stay visible and contrast-checked;
    - full support in both light and dark mode: every effect designed and checked in each theme (#127).
  - Write the design plan into doc 06 first and review it with the owner before building.
- [x] **13.2 Team colors: correct for 2026, and never white (or invisible).** (#138, built 2026-11-06: CFBD 2026 matched production; 26 sourced corrections in `tsi/team_colors.py` (18 brand guides, 8 references); display rule skips white/black/gray and lifts a too-dark or too-light team color to 2.5:1 in its own hue; all 266 FBS + FCS teams checked in both themes on the contact sheet, 0 left gray)
  - *Current:* every team's colors must be its **current (2026) official colors**. Steps:
    - refresh colors and logos from CFBD's 2026 `/teams` (cached; 1–2 calls) and list what changed;
    - spot-check against each school's athletics brand guide wherever CFBD looks stale: recent rebrands, teams that moved up to FBS or FCS, new programs;
    - corrections go in a small override table in the repo (team, color, alt color, source, date checked).
  - *Visible:* pick each team's display color from its corrected colors. Skip near-white and near-black and anything below a contrast floor against the card background **in each theme**; fall back to the next team color, then a neutral brand tone.
  - *Done when:* every FBS and FCS team is checked in both themes (a contact sheet of all teams' chips, light and dark), no white or invisible colors remain, and every override is sourced.

**Pages**
- [x] **13.3 Remove the TSI Book and Model pages; the Book becomes owner-only** (owner, #127). (#139, built 2026-11-06: `/book/*` and `/model/report` need `OWNER_API_KEY`, 404 otherwise and out of the public spec; public responses carry no picks or Book prices; Book and Model pages, plays filter, edge sort and pick badges removed; weekly review reads the ledger with the key)
  - *Site:* remove the Book and Model pages, their nav links and link previews, and the TSI plays on This week (13.5). No "How TSI works" page.
  - *API:* `/book/*` and `/model/report` answer only requests carrying the owner's key (an `Authorization` header checked against an `OWNER_API_KEY` environment variable on Render). The key lives in Render's settings and the owner's local `.env` (used by the weekly review script, which reads `/book/ledger`), never in the code or the site; wrong or missing key → 404.
  - Any pick or Book data inside public responses (week board, game pages) is removed from those responses.
  - Picks keep being published and graded nightly; the owner works with them through the CLI and the weekly review.
  - *Done when:* the public API and site expose no Book or Model data; the weekly review still works with the key; API tests cover key / no key.
- [ ] **13.4 New home page at `/`.**
  - *Layout:* the rankings tucked into a side rail, with an **FBS game of the week** and an **FCS game of the week** in the middle. The full rankings move to `/rankings` (`/rankings/fcs`, `/rankings/all` stay).
  - *Toggle:* **Power / Résumé** switches both the rail and the games of the week. Power answers "who's best"; Résumé is "who has earned it" (it favors undefeated teams with good schedules).
  - *Game-of-the-week score (experiment first),* combining:
    - **quality:** both teams' ranks in the chosen ranking, so a weak team pulls the score down;
    - **competitiveness:** how close TSI's win probability is to 50%;
    - **stakes:** how much the result moves both teams' conference-title and playoff odds in the season sim.
  - Tune it on past seasons so obvious marquee games (#1 vs #2, rivalry top-10 games) come out on top.
  - *When:* picked on Sunday with the poll (#126, #127) from the coming weekend's games, and held all week.
- [ ] **13.5 This week.**
  - *Kickoff:* once a game has kicked off, show "—" for the score with an "In progress" label instead of "Kicked off" plus TSI's predicted score. Show the final score once the nightly run records it; TSI's prediction stays visible as a "TSI predicted" line.
  - *Picks:* remove the TSI plays.
- [ ] **13.6 Playoff tab: a real bracket.**
  - *Plan:* a proper bracket drawing, rounds left to right with connector lines between games, for both the 12-team CFP and the 24-team FCS (from the API's generic rounds, #125).
  - The projected champion path is highlighted (a focal point for 13.1).
  - On phones it scrolls sideways inside its own frame, or switches to a round-by-round view; the page itself never scrolls sideways.
- [ ] **13.7 Team page header:** `| Logo | #5 Miami` instead of `#5 | Logo | Miami` (rank between the logo and the name; "#5 FCS" for FCS teams).

**Ideas to tinker with (owner, "maybe"; prototype before committing to them)**
- [ ] **13.9 Team-spirit team pages.** Each team page dressed in its school's identity: its colors through the page's accents and glows (13.1), its logo used more boldly (a large faded mark in the header, logo details in section headers), maybe its alternate logos and wordmarks where CFBD provides them. Keep it readable: data first, decoration behind it, in both themes. Use only the logos and colors we already get from CFBD (no copied photos or fan art). Prototype on two or three teams, review with the owner, then roll out.
- [ ] **13.10 "TSI's Pick" on This week.** Next to spread, total and moneyline, a small college-football picket sign with a swan logo on the side of the team TSI expects to win (straight up, with its win chance). This is the model's prediction, not a Book bet, so it fits the Book being private (#127). Needs an original swan mark for the sign (SVG, our own artwork, in brand colors), sized for phones. Prototype a few designs and pick one with the owner.

**Data**
- [ ] **13.8 Fill in all of 2026 before the nightly job started** (owner, #127). *Neon transfer (#140): run the replay on a local copy and write only its results to Neon.*
  - *Goal:* every table filled from week 1: TSI's line and win chance for every 2026 game, and every team's daily ratings and ranks, exactly as if the model had been running and adjusting itself from week 1.
  - *Plan:* replay the season day by day (each day's 10:00 UTC cutoff, the same live code path, data before the cutoff only), from the first day of the season to the first nightly run. That means storing:
    - a rating run per day (rankings, rating trend, movement);
    - a forecast for every game from the last replayed day before its kickoff;
    - a season sim per Sunday, if cheap enough.
  - Use the current artifact (the only model there is). Note in decisions that early-2026 numbers come from a model fit through 2025, the same as live.
  - *Rule #2 / #57 still holds:* rebuilt forecasts are stored apart from published snapshots (their own run kind and table or flag), never back-date `published_at`, and their picks are never made or graded. The site shows them like any other number, with a small "rebuilt" footnote marker.
  - *Done when:* no 2026 team page or week board shows dashes where TSI numbers belong; the replay reproduces the backtest's features for those games (parity check); the published-snapshot tables are untouched.

**Operations (found 2026-11-06, #140): Neon network transfer**
- [ ] Local Postgres copy of the data on the home PC; backtests, experiments and refits run against it. Build it with `tsi ingest season --season 2014 --through 2026` against local Postgres from the CFBD disk cache (no Neon reads; finished seasons cost no CFBD calls), not `pg_dump` (reads the whole database out of Neon). Live-only tables (snapshots, picks, model runs) don't come along; backtests don't need them.
- [ ] Transfer meter: log how much the nightly job and the API read per run or request. Neon gives no per-query bytes; per-branch totals come from the branch details API (`data_transfer_bytes`) and the heaviest queries from `pg_stat_statements` (rows per call; cleared whenever the compute scales to zero).
- [ ] "Save backtest to production" without reading the history from production (compute from a copy; upload only the saved run).
- [ ] Cut reads per site build or nightly run if the meter shows they matter.

**Owner's answers (2026-11-05, #127):**
1. Book data behind a private owner key (more practical than deleting the routes, since the weekly review reads `/book/ledger`).
2. Remove the Model page entirely.
3. Rebuild all of 2026 (lines, win chances, daily ratings), as in 13.8.
4. Every effect and color must work **fully in both light and dark mode**: each glow, sweep and border light gets its own light-mode version, contrast-checked, not a weaker copy.
5. Games of the week: the coming weekend's games, picked on Sunday with the poll (#126).

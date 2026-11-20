# 07 – Roadmap

Work one item at a time: build → test → tick → commit, then stop for review (doc 09 §1). There's no launch deadline (decision #27): quality over speed. Finished phases are summarized at the bottom; their details are in `decisions.md`.

---

## Now: confirm the Neon cuts hold (Nov 20 – Dec 1)

**Where things stand (2026-11-20):** back online. Neon suspended the project on 2026-11-09 for going over its 5 GB monthly transfer (that period froze at 5.6 GB; doc 10 §1). On Nov 20 the owner added Neon's $5 limit increase (25 GB) for one period instead of waiting for Dec 1 (#151); the new period runs **Nov 20 – Dec 1** and started at 0 GB. The cuts (#144–#148) are live but not yet measured on production. **Goal:** show from real daily figures that the free 5 GB fits (target **under 80 MB a day**, half the free budget), then remove the add-on before the next period's bill.

- [x] **Back online (2026-11-20, all checked):** API answers; Render manual deploy of `34e5cf8` (#146–#148, `kickoff_tbd`); nightly job re-enabled and run at 21:25 UTC (clean, Elo carry fingerprint matches production, 182 games published, Nov 9–20 picks graded, 60 pages refreshed); site redeployed after fixing Vercel's skip-build check (#151) with 13.5–13.7 and the logo widths (Playoffs nav and bracket, `/matchup` 404, This week, Navy's Dec 12 game with its "Not yet published" forecast); CI green.
- [ ] **Neon transfer per day:** the owner sends the project's Network transfer figure each morning; record it below. Expected ~10–50 MB a day (the night's ~6.4 MB, visitors, ~18 MB per site build); it was ~300 MB. If a day runs high, measure with the transfer meter and check Vercel's ISR writes and Render's response volume.

  | Date (morning) | Project total | That day |
  |---|---|---|
  | Nov 20 (period start) | 0 GB | — |

- [ ] **Vercel:** ISR writes grow ~60–100 a day (31K on Nov 20; were ~1,000 a day); image transformations stay under 5K (4.7K on Nov 20) until Vercel's period resets.
- [ ] **12.1:** a week of nightly runs that start at 11:0x UTC from cron-job.org with no 14:23 backup run (built #126; three morning runs failed on a slow CFBD before #144 fixed the client). First: Nov 21.
- [ ] **12.5:** on Sunday Nov 22, ranking arrows and biggest movers match the previous Sunday's ranks (built #134; never checked live).
- [x] **Games of the week:** Kentucky at Missouri (FBS Résumé, 0.00) is the rule working: no game this week has two Résumé Top 25 teams, so the tiebreakers pick it; the replayed Sunday chose the same games (#152). The score now counts every rank in the division (#153; picks from Sunday Nov 22 on; this week's stored rows keep their old, unshown score).
- [ ] **By Nov 30: keep or remove the Neon add-on.** If the daily figures fit (under ~80 MB a day on average), remove it so the Dec 1 period is free; if not, find the cause first.

## Next

**Neon: cheaper still** (each on the local copy with the transfer meter, outputs identical)
- [x] Re-measure since #148 and the rebuild (2026-11-20, local copy, ~90 runs): nightly run 2.14 MB without ingest (~3 MB with), a full site build **9.95 MB** (was 17.6), the nightly ~60-page refresh ~4 MB, a team page 42 KB (was 8: its rating history reads both sets' full rows for every run), rankings 265 KB, `/playoff` 152 KB. **Untouched month:** ~7 MB a night (~210 MB) plus first visits; even a crawler opening every team, week and game page daily adds ~22 MB a day, so ~0.9 GB a month at worst, well under 5 GB. Each web push adds ~10 MB.
- [x] Trim the two heavy reads found (#154): team page 41 → 20 KB (one compact history row per run), rankings 265 → 200 KB (the Sunday baseline reads only ranks); every response byte-identical. Also Next.js 16.4.2 → 16.4.6 for 7 moderate advisories (`npm audit --omit=dev` back to 0).
- [ ] The home page (764 KB) and week boards (~350 KB) in the nightly refresh.
- [ ] Save last season's fitted stats like the Elo carry (~0.5 MB a run).
- [ ] "Save backtest to production" without reading the history from production (compute on a copy; upload only the saved run).
- [ ] *Maybe (ask: changes the nightly workflow, needs a Neon API key secret):* the nightly job reads production's transfer from Neon's API and warns when the month is on pace to go over.

**13.8 Fill in every day of 2026** (owner, #127; widened 2026-11-20 to the outage, #152)
*Goal:* the site as if it had run every day since the season started: a rating run for every day (the rating trend, daily ranks and Sunday movement baselines), a TSI line and win chance for every game, and the games of the week for each poll week. Two gaps: **B** = the Neon outage (Nov 10–19) first, then **A** = the season's start to the first nightly run.
- [x] **1. Replay engine** (`services/rebuild.py`, #152): a day = that day's nightly computation at its 11:00 UTC cutoff through the live code (`rebuild_day`), no ingest, publish or grading; forecasts kept for games before the next cutoff; Sundays add the season sim and the games of the week. Checked on the local copy: replaying the stored Nov 9 runs reproduces all 532 ratings and all 24 forecasts published then, to the last digit; Aug 27 (no games yet) gives forecasts but no ranks; ~1 s a day.
- [x] **2. Storage** (migration `2ea5f908b00b`, `services/rebuild_store.py`; was: migration, ask first): a `rebuilt_forecasts` table (one row per game: the run, the forecast's score distribution and fair prices; never picks), and rating runs stored as `kind = 'live'` with `params.job = "rebuild"` and the time they were rebuilt. Days without a rated team store no rating run. Replacing a poll week's games of the week (Nov 15, owner) deletes its late picks first.
- [x] **3. API + site** (`snapshots_for_games` adds a never-published game's rebuilt forecast with `rebuilt: true`; the Book's `snapshots_for_season` never does; shown like any published number (markings removed, owner, #153); `tsi rebuild verify` / `season` and the manual **Rebuild missing days** workflow; local copy: 83 days, 1,274 games, none left without a forecast): finished and upcoming games without a published snapshot show the rebuilt forecast (team schedules, week boards, game center) with a small "rebuilt" marker; published snapshots always win.
- [x] **4. Run it** (2026-11-20, `rebuild.yml` on production): verify replayed the newest nightly run (79, Nov 20 21:25 UTC) exactly: 532 ratings and 182 published forecasts, 0 differ. Then 68 days: 63 rating runs (Aug 27 – Oct 18 and Nov 10–19; ranks from Aug 30), 985 games given a rebuilt forecast (incl. games the Oct 20 – Nov 9 board never published), a sim and games of the week every rebuilt Sunday (Nov 15's late picks replaced; the Sunday run chose the same four games). The site refreshed once Render served `rebuilt`. Notre Dame: rating history every day from Sep 7, a TSI line and win chance on every game.

## Later: ideas to prototype first (owner, "maybe")
- [ ] **13.9 Team-spirit team pages.** Each team page dressed in its school's identity: its colors through the page's accents and glows (13.1), its logo used more boldly (a large faded mark in the header, logo details in section headers), maybe alternate logos and wordmarks where CFBD provides them. Data first, decoration behind it, in both themes. Only the logos and colors we already get from CFBD. Prototype on two or three teams, review with the owner, then roll out.
- [ ] **13.10 "TSI's Pick" on This week.** Next to spread, total and moneyline, a small college-football picket sign with a swan logo on the side of the team TSI expects to win (straight up, with its win chance). The model's prediction, not a Book bet, so it fits the Book being private (#127). Needs an original swan mark (SVG, our own artwork), sized for phones. Prototype a few designs and pick one with the owner.

---

## Done

| Phase | Finished | What it delivered | Decisions |
|---|---|---|---|
| 0 Setup | 2026-10-14 | Tools, repo, gitleaks hook, CFBD key, Neon `production` + `dev` (doc 08) | #1–#10, #14, #15 |
| 1 Data | 2026-10-14 | CFBD client with disk cache and call budget, loaders, 2014–2026 backfill, `tsi check` (0 failures), daily ingest | #11–#13, #16–#22, #29 |
| 2 Model v1 | 2026-10-20 | Elo baseline, opponent-adjusted ridge components, `season` + `predictive` sets, prior, stacked margin and totals, Résumé/SOS, walk-forward backtest, `tsi model fit`, report card. Validation 12.40 vs. Vegas 12.00 | #23–#28, #30–#50 |
| 3 Book | 2026-10-20 | Score distribution, pricing, consensus and shrunk edges, picks and staking, publishing/grading/CLV, Book backtest, `tsi run` | #51–#59 |
| 4 API | 2026-10-21 | FastAPI read-only API, caching headers, seeded-DB tests, OpenAPI spec | #60–#65 |
| 5 Frontend | 2026-10-21 | Next.js site: rankings, week board, game center, team pages (Book and Model pages later removed in 13.3), phone layouts | #66–#77 |
| 6 Go live | 2026-11-03 | Render API, Vercel site, nightly job + site refresh, alerting, security pass, `tsi-weekly-run` skill; 7 unattended nights | #78–#84 |
| 7 Polish | 2026-10-28 | Link previews and SEO (indexing off), Lighthouse ≥ 90, biggest movers, Résumé drill-down, README (matchup tool later removed, #145) | #85–#92 |
| 8 Season sim | 2026-11-03 | Monte Carlo season sim, conference title odds, CFP projector, `/playoff`, fair title odds, stored nightly | #93–#101 |
| 9 Adjustments | 2026-11-03 | `tsi adjust`, raw vs. adjusted predictions shown side by side, adjusted-vs-raw report | #103–#105 |
| 10 FCS | 2026-11-04 | FCS rated individually from 2022 (v1.3), ranked within its division, published without picks, FBS / FCS / All views | #107–#117 |
| 11 Stretch | 2026-11-05 | Key numbers (#118), rest/bye (v1.4), second-level yards + power success (v1.5), FBS-vs-FCS scale (v1.6), FCS sim + 24-team playoff; boosting and totals signals rejected; first-half markets, live odds, AI previews dropped | #118–#125, #128–#130 |
| 12 Owner's review | 2026-11-06 (12.1, 12.5 await live checks above) | Nightly run at 11:00 UTC via cron-job.org (12.1), pages refresh right after a run (12.2), no negative scores (v1.7, 12.3), FCS Résumé vs. #24 (12.4), Sunday-based arrows (12.5), FCS ranks on This week (12.6), long names in movers (12.7) | #126, #131–#136 |
| 13 Frontend overhaul | 2026-11-10 (13.8–13.10 open) | Black-and-white look with team-colored light (13.1), sourced team colors (13.2), Book owner-only and Model page removed (13.3), home page with games of the week (13.4), game state by the viewer's clock (13.5), real playoff bracket (13.6), schedule rank after the logo (13.7) | #127, #137–#143, #149, #150 |
| Neon cuts | 2026-11-10 | CFBD retries, web-only site builds, 31-day logo cache (#144); daily page cache, matchup removed, stored sim forecasts (#145); Elo carry (#146); one read per season (#147); Résumé context cache (#148); transfer meter; local Postgres copies on both PCs | #140, #144–#148 |

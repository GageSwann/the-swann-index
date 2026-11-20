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
- [ ] **Games of the week:** the Nov 20 run picked Kentucky at Missouri for the FBS Résumé view with a score of 0.00 (picked late because the outage left the poll week empty). Look at why before Sunday's pick.
- [ ] **By Nov 30: keep or remove the Neon add-on.** If the daily figures fit (under ~80 MB a day on average), remove it so the Dec 1 period is free; if not, find the cause first.

## Next

**Neon: cheaper still** (each on the local copy with the transfer meter, outputs identical)
- [ ] Re-measure a full site build since #148 (17.6 MB before; it decides how freely we can push).
- [ ] The home page (764 KB) and week boards (~350 KB) in the nightly refresh.
- [ ] Save last season's fitted stats like the Elo carry (~0.5 MB a run).
- [ ] "Save backtest to production" without reading the history from production (compute on a copy; upload only the saved run).
- [ ] *Maybe (ask: changes the nightly workflow, needs a Neon API key secret):* the nightly job reads production's transfer from Neon's API and warns when the month is on pace to go over.

**13.8 Fill in all of 2026 before the nightly job started** (owner, #127)
- [ ] *Goal:* every table filled from week 1: TSI's line and win chance for every 2026 game, and every team's daily ratings and ranks, as if the model had been running from week 1.
  - *Plan:* replay the season day by day (each day's cutoff, the same live code path, data before the cutoff only), from the first day of the season to the first nightly run, storing a rating run per day, a forecast for every game from the last replayed day before its kickoff, and a season sim per Sunday if cheap enough. Use the current artifact; note in decisions that early-2026 numbers come from a model fit through 2025, the same as live.
  - *Rule 2 / #57 still hold:* rebuilt forecasts are stored apart from published snapshots (own run kind and table or flag), `published_at` is never back-dated, and their picks are never made or graded. The site shows them with a small "rebuilt" footnote.
  - *Neon:* run the replay on a local copy (bring it current first) and write only its results to production.
  - *Done when:* no 2026 team page or week board shows dashes where TSI numbers belong; the replay reproduces the backtest's features for those games (parity); the published-snapshot tables are untouched.

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

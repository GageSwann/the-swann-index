# 07 – Roadmap

Work one item at a time: build → test → tick → commit, then stop for review (doc 09 §1). There's no launch deadline (decision #27): quality over speed. Finished phases are summarized at the bottom; their details are in `decisions.md`.

---

## Now: back online after the Neon reset

**Where things stand (2026-11-20):** Neon suspended the project on 2026-11-09 for going over its 5 GB monthly transfer (the period's total froze at 5.6 GB; doc 10 §1). The live API's data endpoints answer 500, the site serves its Nov 9 pages, the nightly job is paused (`daily-refresh.yml` disabled), and CI's web job is red because it builds against the live API. The period resets on **Dec 1**. The causes were found and cut before then (#144–#148: the hourly page re-check first; a night's reads went from ~14.5 MB to ~6.4 MB), but none of it has been measured on production yet. Waiting to go live: the API from #146–#148 and 13.5 (`kickoff_tbd`), and the site from 13.5–13.7 (built on the local copy Nov 10, pushed during the outage, their builds failed).

**Reset day, in order** (confirm each step before the next):
- [x] Neon answers: `curl -s -o /dev/null -w "%{http_code}" https://tsi-api-44wx.onrender.com/meta/current` → 200. Note the project's network transfer on the Neon Overview (should be ~0). *(2026-11-20: the owner added Neon's $5 limit increase for one period (25 GB) to come back before Dec 1; the new period runs Nov 20 – Dec 1 and started at **0 GB**. Remove the add-on only after a new period starts, once the daily figures show the free 5 GB fits.)*
- [x] Production's Elo fingerprint matches `elo_carry.json` (`completed_games_fingerprint(s, 2025)`, ~32 bytes). If not, runs log "replaying all seasons" and lose the #146 saving: rebuild the file on a local copy.
- [x] Deploy the API: Render **Manual Deploy** of the latest `main` (CI was red, so nothing deployed since `6713d3f`). Confirm `/matchup` → 404, and `/teams/notre-dame` schedule rows carry `kickoff_tbd` and `forecast`. *(2026-11-20: Manual Deploy of `34e5cf8`; confirmed.)*
- [x] Turn the nightly job back on (`gh workflow enable daily-refresh.yml`) and run it once (`gh workflow run daily-refresh.yml`): success, no `ingest FAILED`, no "replaying all seasons". *(2026-11-20 21:25 UTC: both clean, so the fingerprint matches; 182 games published, the Nov 9–20 picks graded, 60 pages refreshed.)*
- [ ] Redeploy the site, only after the API serves `kickoff_tbd` (Vercel → Deployments → Redeploy, or push the pending web change below). Check: no Matchup in the nav, the Playoffs bracket, This week, a team schedule with forecasts for games beyond 8 days (marked "not yet published").
- [ ] CI green again.

**Pending web change for that redeploy:** `images.imageSizes: [64, 128]` in `web/next.config.ts`, so each team's logo is 2 image transformations instead of ~5 (Vercel Hobby: 4.7K of 5K used by Nov 20; doc 10 §9). Built 2026-11-20 (owner: ship with the redeploy).

**The days after:**
- [ ] **Neon transfer per day** (the point of #144–#148): note the project total each morning. Expected ~10–50 MB a day (the night's ~6.4 MB, visitors, ~18 MB per site build); it was ~300 MB. If it runs high, measure with the transfer meter and check Vercel's ISR writes and Render's response volume.
- [ ] **Vercel:** ISR writes should grow ~60–100 a day (were ~1,000); image transformations should stay under 5K until Vercel's period resets.
- [ ] **12.1:** a week of nightly runs that start at 11:0x UTC from cron-job.org with no 14:23 backup run (built #126, 2026-11-05; three morning runs failed on a slow CFBD before #144 fixed the client).
- [ ] **12.5:** on the first Sunday, ranking arrows and biggest movers match the previous Sunday's ranks (built #134, 2026-11-05; never checked live).

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

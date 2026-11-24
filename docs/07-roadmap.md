# 07 – Roadmap

Work one item at a time: build → test → tick → commit, then stop for review (doc 09 §1). There's no launch deadline (decision #27): quality over speed. Finished phases are summarized at the bottom; their details are in `decisions.md`.

---

## Now: confirm the Neon cuts hold (Nov 20 – Dec 1)

**Update 2026-11-23:** first reading 0.48 GB (Nov 20–22, see the table). The day's design work (#156–#176, ~16 web pushes) cost ~160 MB in site builds, so the Nov 24 reading will run high; from then on, batch web pushes and screenshot locally first (doc 10 §1, §9). **Check on Nov 24 after the 11:00 UTC run:** `/playoff/fcs` shows the official bracket; the FCS game of the week is a first-round playoff game; the rank arrows still show the move since Nov 15; the iPhone status-bar strip matches the header in both themes; the tab icon follows the browser's mode.

**Where things stand (2026-11-20):** back online. Neon suspended the project on 2026-11-09 for going over its 5 GB monthly transfer (that period froze at 5.6 GB; doc 10 §1). On Nov 20 the owner added Neon's $5 limit increase (25 GB) for one period instead of waiting for Dec 1 (#151); the new period runs **Nov 20 – Dec 1** and started at 0 GB. The cuts (#144–#148) are live, and on the local copy an untouched month measures ~0.9 GB at worst (#154); since then the team pages, rankings, home page and week boards read less (#154, #155). Production's daily figures are still to come. **Goal:** show from real daily figures that the free 5 GB fits (target **under 80 MB a day**, half the free budget), then remove the add-on before the next period's bill.

- [x] **Back online (2026-11-20, all checked):** API answers; Render manual deploy of `34e5cf8` (#146–#148, `kickoff_tbd`); nightly job re-enabled and run at 21:25 UTC (clean, Elo carry fingerprint matches production, 182 games published, Nov 9–20 picks graded, 60 pages refreshed); site redeployed after fixing Vercel's skip-build check (#151) with 13.5–13.7 and the logo widths (Playoffs nav and bracket, `/matchup` 404, This week, Navy's Dec 12 game with its "Not yet published" forecast); CI green.
- [ ] **Neon transfer per day:** the owner sends the project's Network transfer figure each morning; record it below. Expected ~10–50 MB a day (the night's ~6.4 MB, visitors, ~18 MB per site build); it was ~300 MB. If a day runs high, measure with the transfer meter and check Vercel's ISR writes and Render's response volume.

  | Date (morning) | Project total | That day |
  |---|---|---|
  | Nov 20 (period start) | 0 GB | — |
| Nov 23 | 0.48 GB | Nov 20–22 together (no daily readings sent Nov 21–22): ~250–300 MB of one-offs on Nov 20 (rebuild + verify, ~5 site builds) leave ~180–230 MB for ~2.5 normal days, **~70–90 MB a day** |
| Nov 24 | 0.96 GB (nightly API reading at 11:04 UTC also 0.96) | Nov 23: **~480 MB**, a design day: ~29 Vercel builds **plus 38 CI site builds** (CI's web job prerenders the site from the live API on every push to `main`, docs- and backend-only pushes too; not counted in the ~10 MB-per-push estimate), so ~67 builds at roughly 7 MB each; two nightly runs (Nov 23 11:01 and a 14:23 backup that GitHub started 11 h late, at 01:44 Nov 24, and that ran in full because the gate checks the UTC day) |

  *Expect Nov 21 to be high:* it includes the one-off rebuild (~250 MB, #152), the rebuild's verify, today's pushes' site builds (~10 MB each) and the migrations. Nov 22 onward is the normal pattern.

- [ ] **Vercel:** ISR writes grow ~60–100 a day (31K on Nov 20; were ~1,000 a day); image transformations stay under 5K (4.7K on Nov 20; logos stopped using them on Nov 23, #169) until Vercel's period resets.
- [ ] **12.1:** a week of nightly runs that start at 11:0x UTC from cron-job.org with no 14:23 backup run (built #126; three morning runs failed on a slow CFBD before #144 fixed the client). First: Nov 21. So far: Nov 21, 22, 23 started 11:01 UTC; the 14:23 backup skipped itself each day (3/7).
- [ ] **12.5:** on Sunday Nov 22, ranking arrows and biggest movers match the previous Sunday's ranks (built #134; never checked live). Nov 22 showed the move since Nov 15 as intended; on Monday the arrows reset to the move since Nov 22 (all 0), so the owner changed the rule: the week's move stays up until the next Sunday (#156). Check live on Tuesday Nov 24 (arrows still vs. Nov 15).
- [x] **Games of the week:** Kentucky at Missouri (FBS Résumé, 0.00) is the rule working: no game this week has two Résumé Top 25 teams, so the tiebreakers pick it; the replayed Sunday chose the same games (#152). The score now counts every rank in the division (#153; picks from Sunday Nov 22 on; this week's stored rows keep their old, unshown score).
- [x] **Official FCS bracket + playoff games of the week (#157, 2026-11-23):** the FCS playoff page draws the announced bracket, played out nightly with real results; a better game added after Sunday's pick replaces it. Check live Tuesday Nov 24: `/playoff/fcs` shows "Bracket" with win chances, and the FCS game of the week is a first-round game.
- [x] **Mobile pass (owner, 2026-11-23: cluttered, too long, hard to navigate, unpolished):** one area at a time, pushed for the owner's review on a phone.
  - [x] 1. Header, bottom navigation, home (#163)
  - [x] 2. Rankings (table, toggles, movers) (#164)
  - [x] 3. Week board (#165)
  - [x] 4. Game center (#165)
  - [x] 5. Team pages (reviewed: already clean; stale FCS text fixed, #165)
  - [x] 6. Playoffs (bracket, odds) (#165)
  - [x] iPhone safe areas: edge to edge under the island and home bar (#165). Check on a real iPhone (newer and older).
- [ ] **Each November, selection Sunday:** enter that season's FCS bracket in `sim/fcs_brackets.py` (seeds 1-16, the unseeded teams by the seed they visit) and confirm the quarterfinal pairings; push before the next nightly run.
- [ ] **By Nov 30: keep or remove the Neon add-on.** If the daily figures fit (under ~80 MB a day on average), remove it so the Dec 1 period is free; if not, find the cause first.

**Check on Nov 24 after the 11:00 UTC run (evening work of Nov 23):** the run's summary shows the first Neon transfer reading from the new `transfer` job (#179): compare it with the console's project Overview; the run's log has no "saved component fit ... no longer matches" warning (#177: the carry was built on the work PC's copy); the page warm-up visits `/cfb/...` pages with 200s (#184); the live cards show TSI's odds under each line, one-decimal chances and conference records (#188, #190). The Nov 24 Neon reading also carries ~13 more site builds from that evening (~130 MB on top of the ~160 MB design day).

## Next

**Open from the owner (2026-11-23):**
- [ ] Phones: the sport menus (CFB, CBB, CBASE) in the phone header; phones keep the bottom bar for now (owner: "fix mobile later").
- [ ] The site's own home for every sport at `/` (it redirects to `/cfb` for now, #182).
- [ ] 13.10's sign on the Schedule cards (the home page's Game of the Week cards have it, #180).
- [ ] "CBASE" is a placeholder abbreviation for college baseball (#181).

**Sport namespaces (owner, #183):** everything college football lives under `/cfb`, on the site and in the API, so college basketball (CBB) and baseball (CBASE) can sit beside it later without rewiring. Backend code and database stay as they are (see #183 for how another sport fits in).
- [x] **1. API under `/cfb`** (old paths still served, `legacy_` ids; spec + types; the owner's `/cfb/book` and `/cfb/model` never cached). Ship first.
- [x] **2. Site under `/cfb`** (#184), once the live API serves `/cfb/meta/current`: pages at `/cfb/rankings`, `/cfb/schedule/{season}/{week}`, `/cfb/playoffs`, `/cfb/teams/{slug}`, `/cfb/games/{id}` (link previews move with them); permanent redirects from every old address (`/rankings`, `/week/...`, `/playoff`, `/teams/...`, `/games/...`); one place builds every link (`lib/routes.ts`); the site calls the `/cfb` API paths; sitemap; the sport menu and bottom bar; the nightly job's page warm-up list (`daily-refresh.yml`, the owner asked for this rewiring).
- [x] **3. Cleanup** (#185), once the live site calls only `/cfb` paths: drop the old API paths and their `legacy_` ids; the nightly job's API calls (`/meta/current`, `/rankings`) and the weekly review script move to `/cfb`.

**Neon: cheaper still** (each on the local copy with the transfer meter, outputs identical)
- [x] Re-measure since #148 and the rebuild (2026-11-20, local copy, ~90 runs): nightly run 2.14 MB without ingest (~3 MB with), a full site build **9.95 MB** (was 17.6), the nightly ~60-page refresh ~4 MB, a team page 42 KB (was 8: its rating history reads both sets' full rows for every run), rankings 265 KB, `/playoff` 152 KB. **Untouched month:** ~7 MB a night (~210 MB) plus first visits; even a crawler opening every team, week and game page daily adds ~22 MB a day, so ~0.9 GB a month at worst, well under 5 GB. Each web push adds ~10 MB.
- [x] Trim the two heavy reads found (#154): team page 41 → 20 KB (one compact history row per run), rankings 265 → 200 KB (the Sunday baseline reads only ranks); every response byte-identical. Also Next.js 16.4.2 → 16.4.6 for 7 moderate advisories (`npm audit --omit=dev` back to 0).
- [x] The home page and week boards (#155): home rankings ~0.8 MB → ~22 KB (`/rankings/top`), week boards 82 → 55 KB this week and 168 → 54 KB an older one (division filter in SQL, only the shown snapshot); every response byte-identical.
- [x] Save last season's fitted stats like the Elo carry (#177, 2026-11-23): `model/artifacts/component_carry.json` + `tsi model carry`; nightly read **2.15 → 1.56 MB** (local copy, `tsi run --no-ingest`), inputs and the week's forecasts `repr`-identical. Check the first production run's log for no "saved component fit ... no longer matches" warning (the carry was built on the work PC's copy).
- [x] ~~"Save backtest to production" without reading the history from production (compute on a copy; upload only the saved run).~~ Measured and closed (#178, owner): a save reads ~13 MB, a few times a season; not worth a workflow change.
- [x] The nightly job reads production's transfer from Neon's API and warns when the month is on pace to go over (#179, owner OK'd the workflow change): `tsi neon transfer`, the nightly `transfer` job (summary, warning over 80 MB a day, one GitHub issue per period when on pace to pass 5 GB or 80% used).
  - [x] **Owner:** create a Neon API key (console → Account settings → API keys), add it as the repo secret `NEON_API_KEY`, and add the variable `NEON_PROJECT_ID` (`nameless-morning-73071395`). Until then the job skips with a notice. (Set 2026-11-23.)
  - [x] First reading (2026-11-24, 11:04 UTC): 0.96 GB, the same as the console that morning; "above target" warning (268 MB a day so far), pace 2.71 GB. Compare the run summary's GB with the console's project Overview the same morning (Neon calls the API figure "not intended for billing").

**13.8 Fill in every day of 2026** (owner, #127; widened 2026-11-20 to the outage, #152)
*Goal:* the site as if it had run every day since the season started: a rating run for every day (the rating trend, daily ranks and Sunday movement baselines), a TSI line and win chance for every game, and the games of the week for each poll week. Two gaps: **B** = the Neon outage (Nov 10–19) first, then **A** = the season's start to the first nightly run.
- [x] **1. Replay engine** (`services/rebuild.py`, #152): a day = that day's nightly computation at its 11:00 UTC cutoff through the live code (`rebuild_day`), no ingest, publish or grading; forecasts kept for games before the next cutoff; Sundays add the season sim and the games of the week. Checked on the local copy: replaying the stored Nov 9 runs reproduces all 532 ratings and all 24 forecasts published then, to the last digit; Aug 27 (no games yet) gives forecasts but no ranks; ~1 s a day.
- [x] **2. Storage** (migration `2ea5f908b00b`, `services/rebuild_store.py`; was: migration, ask first): a `rebuilt_forecasts` table (one row per game: the run, the forecast's score distribution and fair prices; never picks), and rating runs stored as `kind = 'live'` with `params.job = "rebuild"` and the time they were rebuilt. Days without a rated team store no rating run. Replacing a poll week's games of the week (Nov 15, owner) deletes its late picks first.
- [x] **3. API + site** (`snapshots_for_games` adds a never-published game's rebuilt forecast with `rebuilt: true`; the Book's `snapshots_for_season` never does; shown like any published number (markings removed, owner, #153); `tsi rebuild verify` / `season` and the manual **Rebuild missing days** workflow; local copy: 83 days, 1,274 games, none left without a forecast): finished and upcoming games without a published snapshot show the rebuilt forecast (team schedules, week boards, game center) with a small "rebuilt" marker; published snapshots always win.
- [x] **4. Run it** (2026-11-20, `rebuild.yml` on production): verify replayed the newest nightly run (79, Nov 20 21:25 UTC) exactly: 532 ratings and 182 published forecasts, 0 differ. Then 68 days: 63 rating runs (Aug 27 – Oct 18 and Nov 10–19; ranks from Aug 30), 985 games given a rebuilt forecast (incl. games the Oct 20 – Nov 9 board never published), a sim and games of the week every rebuilt Sunday (Nov 15's late picks replaced; the Sunday run chose the same four games). The site refreshed once Render served `rebuilt`. Notre Dame: rating history every day from Sep 7, a TSI line and win chance on every game.

## Later: ideas to prototype first (owner, "maybe")
- [ ] **13.9 Team-spirit team pages** (skipped for now, owner, 2026-11-23). Each team page dressed in its school's identity: its colors through the page's accents and glows (13.1), its logo used more boldly (a large faded mark in the header, logo details in section headers), maybe alternate logos and wordmarks where CFBD provides them. Data first, decoration behind it, in both themes. Only the logos and colors we already get from CFBD. Prototype on two or three teams, review with the owner, then roll out.
- [ ] **13.10 "TSI's Pick" on This week.** Next to spread, total and moneyline, a small college-football picket sign with a swan logo on the side of the team TSI expects to win (straight up, with its win chance). The model's prediction, not a Book bet, so it fits the Book being private (#127). Needs an original swan mark (SVG, our own artwork), sized for phones. Prototype a few designs and pick one with the owner.
  - [x] Prototypes and the swan mark (https://claude.ai/artifact/6u4D4JDPiwqwHMFA3W18Qn); owner: home page first (#180).
  - [x] **Home page, Game of the Week cards** (#180): the sign beside the predicted winner's logo, leaning outward; stays after the final.
  - [ ] Schedule's cards (the board, formerly This week; later, owner: perfect the home page first).

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

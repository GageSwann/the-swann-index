# 06 – Frontend

## Design direction
- **Feel:** a sportsbook board crossed with a TV broadcast stats package. Dark theme by default, with a light theme available.
- **Team colors** are used as accents (card edges, chart lines, header gradients) and are always checked for contrast against the background.
- **Data-dense but readable:** tabular numbers (`font-variant-numeric: tabular-nums`), clear hierarchy, no clutter.
- **Mobile-first:** board and rankings must work on a phone (cards collapse, tables scroll horizontally inside their container only).
- **Phone pass (decision #74):** checked at 360 and 390 px. The page itself never scrolls sideways. Wide tables either get a phone layout (odds board: one block per market; team schedule: two-line rows) or pin their identity columns while the stats scroll (rankings: Rank + Team pinned below `sm`, Δ moved next to Team). Tap targets are at least 24 px (sort headers, filter labels and game-center links are 32 px tall). The header drops the week label on phones so the theme toggle shares the first row.
- Every number links to where it came from (e.g. a rating links to the team page, a line to the game center).
- Footer on every page: "Model updated {time} · TSI {version}".

### Design system (decision #69)
- **Palette, a stadium at night** (`web/app/globals.css`): Night `#0E1923` background, Sideline `#162532` panels, Hashmark `#2A3C4B` lines, Chalk `#E6EDF2` text, **Scoreboard amber `#F2B33D`** as the single brand accent (header rule, active nav, key numbers). Up `#3CC2A9` / Down `#F07A6A` for movement and edges. Light "press box" theme: `#F2F5F7` / ink `#13212C`, amber deepened to `#9A6400` for contrast. Team colors are the other source of color.
- **Type:** one family, Archivo (variable, width axis): condensed widths (`font-stretch-condensed`) for page titles, team names and big numerals; normal width for reading; tabular figures everywhere. No monospace data labels, no all-caps eyebrows.
- **Layout:** the "score bug" header (amber TSI block, wordmark, week context, nav, theme toggle, 2 px amber rule) is the one bold element; content left-aligned, max ~1150 px; flat panels with 1 px rules and a 4 px radius, no shadows or gradient washes. On phones the nav becomes its own scrollable row (no hamburger).
- **Shell:** `components/layout/` (`SiteHeader`, `MainNav`, `ThemeToggle`, `ThemeProvider`, `PageHeading`, `UpdatedFooter`); times in US Eastern, formatted on the server (`lib/format/time.ts`); skip link, visible focus rings, reduced motion respected. Header/footer degrade to a plain message if the API is down.

## Routes

| Route | Page |
|---|---|
| `/` | **Rankings** (Power/Résumé toggle) |
| `/week` → `/week/[season]/[week]` | **Matchup board** for the week (defaults to current week) |
| `/games/[id]` | **Game center** |
| `/teams/[slug]` | **Team page** |
| `/book` | **TSI Book** ledger |
| `/model` | **Methodology + report card** |
| `/matchup` | **Hypothetical matchup tool** (#85) |
| `/playoff` | **CFP projections + bracket** (later) |
| `/conferences/[slug]` | Standings + title odds (later) |

## Page specs

### Rankings `/`
- Toggle: Power | Résumé. Filters: conference, Top 25 / all.
- Columns: Rank, Δ (movement arrow), Team (logo + name), Record, TSI rating, Off (rank), Def (rank), SOS, SOR, Proj. wins (later), CFP % (later).
- Sortable (TanStack Table). Sticky header. Clicking a row opens the team page.
- Side widget: biggest risers/fallers over the past week. **Built (#88):** "Biggest movers", top 5 each way for the active ranking and conference (ignores Top 25/All), "#52 → #37" with the Δ arrow; beside the table from `xl`, below it otherwise; hidden without a week-ago run.
- **This season only:** both rankings use the `season` ratings (no preseason prior). A one-line note under the toggle says so.
- **Provisional:** teams with fewer than 4 games show a *provisional* tag next to their rank.
- **Updated daily:** the header shows "Updated {date}". Δ arrows compare to the previous day's run and to a week ago.
- **Résumé tab:** a short explainer: "How hard would it be for a typical #12 team to match this record against this schedule? Re-evaluated daily as opponents' seasons play out." Clicking a team's SOR opens its team page at the **Résumé** section (#89): the rank, record, what a typical #12 team would expect from the same games, and how often it would match the record; the schedule's "#12 team wins" column shows each game's difficulty against the opponent's current rating (muted until the game counts).
- **Built (decision #70):** Power/Résumé toggle, Top 25 / all, conference filter (client-side over both rankings, rendered once on the server); TanStack Table v9 sorting with a sticky header inside the table's own scroll area; Δ = movement over the past week (`previous_rank` from the newest run at least 6 days older, `previous_as_of`; the intro names its date; no Δ column without one; #79), offense/defense ranks (`off_rank`/`def_rank`) from the API; row click and team-name links go to the team page; logos on a light chip so dark marks stay visible.

### Matchup board `/week/[season]/[week]`
- Week selector + filters: Top 25 only, conference, "TSI plays only", sort by kickoff / edge / win prob.
- **Matchup card:** logos & ranks, kickoff/TV, win-probability bar in team colors, projected score, a TSI line vs. market line row (spread, total, ML), edge badge (★ tier) when it's a TSI play.
- After games: final score, ✔/✘ for each market, CLV.
- **Built (decision #71):** `/week` redirects to the current week; `generateStaticParams` prerenders it and other weeks render on first visit (params awaited inside `<Suspense>`). Filters: Top 25 only, TSI plays only, conference; sort: kickoff (grouped by day), biggest edge, closest game. Card: kickoff (ET), Top-25 ranks, projected score (final score once over, with TSI's projection beside it), win-probability bar, TSI vs. Vegas for spread / total / moneyline (favorite named), ★ play badges with ✔/✘ and CLV once graded. ✔/✘ is shown for official picks only (grading stays in the API). No TV listings (CFBD media not ingested).
- **Team colors** go through `lib/format/color.ts`: primary color if its contrast with the theme's card background is ≥ 2:1, else the alternate color, else a neutral; chosen per theme via CSS variables (`--team-dark` / `--team-light`).

### Game center `/games/[id]`
- **Header:** both teams, records, TSI ranks, kickoff, venue, projected score, win probability.
- **Odds board:** spread / total / moneyline / team totals, with **Fair** vs. **TSI Book** vs. **Market** columns and edge highlighted.
- **Alt-line ladder:** cover/over probability at each number around the line.
- **Margin distribution chart:** histogram/density of predicted margin with the market spread marked (and key numbers marked in v2).
- **Tale of the tape:** mirrored bar chart of off/def ratings, EPA/play, success rate, explosiveness, pace (ranks shown).
- **Rating trends:** both teams' TSI rating by week on one chart.
- **Post-game:** final score, how each market graded, snapshot history ("line moved from X to Y").
- **Built (decision #72):** this week's games are prerendered and others render on first visit (inside `<Suspense>`; an unknown id streams the not-found page with `noindex`). Sections: score-bug header (final score once over), ★ play badges (✔/✘ once graded), odds board (TSI fair / TSI Book / Vegas, with the play's cell outlined; team totals have no market data yet), margin density with Tie and Vegas lines (whole-point hover; cover chance from the API's alt-spread ladder, never computed in the browser), alt spread and total ladders with the Vegas rung highlighted, tale of the tape (ranks, rating, off/def, SOS, record; the better side bold), rating trends (home solid, away dashed, direct end labels, neutral away color when the team colors look alike) and prediction history. EPA, success rate, explosiveness and pace in the tape wait for an API addition. Games without a snapshot say why (before Oct 20, 2026, or not yet within eight days).

### Team page `/teams/[slug]`
- Header gradient in team colors, logo, record, Power rank, Résumé rank, rating.
- **Rating trend** line chart (season, with the preseason prior shown as the starting point).
- **Efficiency profile:** off/def percentile bars (or radar) vs. FBS.
- **Schedule table:** each game with opponent, TSI win prob (pre-game for played games, current for upcoming), result, spread result.
- **Projected record** (later): win distribution histogram, conference title %, CFP %.
- If manually adjusted (later): badge + reason.
- **Built (decision #73):** the current Top 25 is prerendered and every other team renders on first visit (`<Suspense>`; unknown slug → not found). Header: a solid team-color band (flat per #69, instead of a gradient), logo, mascot, conference, record, Power/Résumé rank, rating, predictive rating (rank), SOS. Profile: power/résumé/offense/defense rank bars among rated FBS teams (ranks from `/rankings`). Rating trend: the shared `components/charts/rating-trend-chart.tsx` (one or two teams; y ticks every 2/5/10 points with ≥ 2 points of padding). Schedule: date, opponent (with Top-25 rank and site), result or projected score (links to the game center), TSI line and win chance from the team's side: the published snapshot when there is one, else the API's `/matchup` with today's ratings, marked * "if played today". Non-FBS teams show their schedule with "no rating". Not yet: preseason prior as the trend's starting point (live history starts Oct 19, 2026), percentiles for EPA/success/explosiveness, spread result per game (needs market lines in the team endpoint), projected record.

### Matchup `/matchup`
- **Built (decision #85):** pick any two FBS teams (away/home, neutral-site checkbox) in a plain GET form grouped by conference: works without JavaScript, and results are shareable URLs (`/matchup?away=auburn&home=alabama&neutral=1`); "Swap home and away" is a link. Result: the shared `ScoreBoard` (projected score, win probability), TSI's fair and Book prices (no Vegas column: books only post scheduled games), the margin chart (from `sigma_margin`), alternate spread/total ladders and the tale of the tape. Labeled hypothetical: not saved, graded or in the Book. Empty state suggests three top-6 pairings on neutral fields; same team twice or an unknown slug get a plain message.

### TSI Book `/book`
- KPI tiles: record (ATS / O/U / ML), units, ROI, avg CLV.
- Cumulative units line chart; record by ★ tier.
- Pick history table with filters (season, market, tier, result).
- **Built (decision #75):** season record panel (W-L-P, units flat + ¼ Kelly, ROI, CLV with beat-the-close share, one line per market), units-over-time chart (flat solid amber, ¼ Kelly dashed), record by market then ★ tier, pick history (market / tier / result filters; table from `sm`, stacked rows on phones; open → locked → graded status), and a short "how the Book picks" list. Before any pick is graded it shows "No graded picks yet" and the open picks. No season filter yet (2026 is the only live season); the backtest Book record belongs on the Model page.

### Model `/model`
- Plain-English methodology (based on docs 04/05), with formulas.
- **Report card:** this season + backtest: MAE, straight-up %, ATS %, Brier; vs. closing line, SP+, Elo.
- Calibration chart (reliability diagram).
- Model version history.
- **Built (decision #76):** validation headline (TSI vs. Vegas vs. Elo error, winners), report card by period (live row once games are graded; Games/Elo/Vegas-winners columns hidden on phones), error by season chart (TSI, Vegas, Elo; validation marker; current season marked partial), reliability diagram (dot size = games), spreads vs. the close (ATS by disagreement) and totals accuracy, the Book replayed (record by period and season, cumulative units with one tick per year), plain-English method with the key formulas, and version history. All numbers come from the latest saved `tsi backtest run`. SP+ agreement stays in the CSV export (needs a refit per season plus CFBD data).

## Shared components
`TeamBadge`, `WinProbBar`, `OddsCell` (American odds formatting), `EdgeBadge`, `RatingDelta`, `StatBar` (mirrored), `TrendChart`, `DistributionChart`, `KpiTile`, `SeasonWeekPicker`, `UpdatedFooter`.

## Data fetching
- Server Components call the FastAPI service through a typed client (`web/lib/api.ts`, types generated from OpenAPI).
- ISR with tag-based revalidation (see [02-architecture.md](02-architecture.md)).
- Loading skeletons and empty states (e.g. "Lines not posted yet").
- SEO/OG: dynamic Open Graph images for game and team pages (makes shared links look great).

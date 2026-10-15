# 06 – Frontend

## Design direction
- **Feel:** a sportsbook board crossed with a TV broadcast stats package. Dark theme by default, with a light theme available.
- **Team colors** are used as accents (card edges, chart lines, header gradients) and are always checked for contrast against the background.
- **Data-dense but readable:** tabular numbers (`font-variant-numeric: tabular-nums`), clear hierarchy, no clutter.
- **Mobile-first:** board and rankings must work on a phone (cards collapse, tables scroll horizontally inside their container only).
- Every number links to where it came from (e.g. a rating links to the team page, a line to the game center).
- Footer on every page: "Model updated {time} · TSI {version}".

## Routes

| Route | Page |
|---|---|
| `/` | **Rankings** (Power/Résumé toggle) |
| `/week` → `/week/[season]/[week]` | **Matchup board** for the week (defaults to current week) |
| `/games/[id]` | **Game center** |
| `/teams/[slug]` | **Team page** |
| `/book` | **TSI Book** ledger |
| `/model` | **Methodology + report card** |
| `/matchup` | **Hypothetical matchup tool** (later) |
| `/playoff` | **CFP projections + bracket** (later) |
| `/conferences/[slug]` | Standings + title odds (later) |

## Page specs

### Rankings `/`
- Toggle: Power | Résumé. Filters: conference, Top 25 / all.
- Columns: Rank, Δ (movement arrow), Team (logo + name), Record, TSI rating, Off (rank), Def (rank), SOS, SOR, Proj. wins (later), CFP % (later).
- Sortable (TanStack Table). Sticky header. Clicking a row opens the team page.
- Side widget: biggest risers/fallers this week.

### Matchup board `/week/[season]/[week]`
- Week selector + filters: Top 25 only, conference, "TSI plays only", sort by kickoff / edge / win prob.
- **Matchup card:** logos & ranks, kickoff/TV, win-probability bar in team colors, projected score, a TSI line vs. market line row (spread, total, ML), edge badge (★ tier) when it's a TSI play.
- After games: final score, ✔/✘ for each market, CLV.

### Game center `/games/[id]`
- **Header:** both teams, records, TSI ranks, kickoff, venue, projected score, win probability.
- **Odds board:** spread / total / moneyline / team totals, with **Fair** vs. **TSI Book** vs. **Market** columns and edge highlighted.
- **Alt-line ladder:** cover/over probability at each number around the line.
- **Margin distribution chart:** histogram/density of predicted margin with the market spread marked (and key numbers marked in v2).
- **Tale of the tape:** mirrored bar chart of off/def ratings, EPA/play, success rate, explosiveness, pace (ranks shown).
- **Rating trends:** both teams' TSI rating by week on one chart.
- **Post-game:** final score, how each market graded, snapshot history ("line moved from X to Y").

### Team page `/teams/[slug]`
- Header gradient in team colors, logo, record, Power rank, Résumé rank, rating.
- **Rating trend** line chart (season, with the preseason prior shown as the starting point).
- **Efficiency profile:** off/def percentile bars (or radar) vs. FBS.
- **Schedule table:** each game with opponent, TSI win prob (pre-game for played games, current for upcoming), result, spread result.
- **Projected record** (later): win distribution histogram, conference title %, CFP %.
- If manually adjusted (later): badge + reason.

### TSI Book `/book`
- KPI tiles: record (ATS / O/U / ML), units, ROI, avg CLV.
- Cumulative units line chart; record by ★ tier.
- Pick history table with filters (season, market, tier, result).

### Model `/model`
- Plain-English methodology (based on docs 04/05), with formulas.
- **Report card:** this season + backtest: MAE, straight-up %, ATS %, Brier; vs. closing line, SP+, Elo.
- Calibration chart (reliability diagram).
- Model version history.

## Shared components
`TeamBadge`, `WinProbBar`, `OddsCell` (American odds formatting), `EdgeBadge`, `RatingDelta`, `StatBar` (mirrored), `TrendChart`, `DistributionChart`, `KpiTile`, `SeasonWeekPicker`, `UpdatedFooter`.

## Data fetching
- Server Components call the FastAPI service through a typed client (`web/lib/api.ts`, types generated from OpenAPI).
- ISR with tag-based revalidation (see [02-architecture.md](02-architecture.md)).
- Loading skeletons and empty states (e.g. "Lines not posted yet").
- SEO/OG: dynamic Open Graph images for game and team pages (makes shared links look great).

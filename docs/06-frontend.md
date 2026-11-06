# 06 – Frontend

## Design direction
- **Feel:** a sportsbook board crossed with a TV broadcast stats package. Dark theme by default, with a light theme available.
- **Team colors** are used as accents (card edges, chart lines, header gradients) and are always checked for contrast against the background.
- **Data-dense but readable:** tabular numbers (`font-variant-numeric: tabular-nums`), clear hierarchy, no clutter.
- **Mobile-first:** board and rankings must work on a phone (cards collapse, tables scroll horizontally inside their container only).
- **Phone pass (decision #74):** checked at 360 and 390 px. The page itself never scrolls sideways. Wide tables either get a phone layout (odds board: one block per market; team schedule: two-line rows) or pin their identity columns while the stats scroll (rankings: Rank + Team pinned below `sm`, Δ moved next to Team). Tap targets are at least 24 px (sort headers, filter labels and game-center links are 32 px tall). The header drops the week label on phones so the theme toggle shares the first row.
- Every number links to where it came from (e.g. a rating links to the team page, a line to the game center).
- Footer on every page: "Model updated {time} · TSI {version}".

### Design system (decision #69; palette, type and lighting replaced by #137)
- **Palette, the black swan and the white swan** (`web/app/globals.css`, #137): the brand has no hue. Dark ("black swan", default): `#000000` background, `#0E0E0F` panels, `#2B2B2E` lines, `#F5F5F3` text, `#9A9A9F` muted text. Light ("white swan"): `#F4F4F4` background, `#FFFFFF` panels, `#D4D4D6` lines, `#0A0A0A` text, `#5A5A60` muted text. `--primary` (TSI block, header rule, selected tab, focus ring) is the text color: white on black, black on white. Up `#3CC2A9` / Down `#F07A6A` (light `#11806B` / `#C2412F`) for movement and edges. **Team colors are the only color.** Text links are underlined (they can't rely on an accent color).
- **Type:** one family, **Instrument Sans** (#137, replaces Archivo; variable, width axis 75–100, weights 400–700): condensed widths (`font-stretch-condensed`) for page titles, team names and big numerals; normal width for reading; tabular figures everywhere (plain zeros: Mona Sans was tried and rejected for its slashed tabular zero). No monospace data labels, no all-caps eyebrows. Link-preview images use static instances in `web/assets/fonts` (Medium, Condensed Bold; SIL OFL).
- **Layout:** the "score bug" header (TSI block, wordmark, week context, nav, theme toggle, 2 px rule) is the one bold element; content left-aligned, max ~1150 px; flat panels with 1 px rules and a 4 px radius, no gradient washes. Light (below) is the only shadow. On phones the nav becomes its own scrollable row (no hamburger).
- **Shell:** `components/layout/` (`SiteHeader`, `MainNav`, `ThemeToggle`, `ThemeProvider`, `PageHeading`, `UpdatedFooter`); times in US Eastern, formatted on the server (`lib/format/time.ts`); skip link, visible focus rings, reduced motion respected. Header/footer degrade to a plain message if the API is down.

### Lighting (Phase 13.1, built 2026-11-06, #137)
The owner's brief: how light behaves, not a retro neon theme. Glows and a light that runs around a border, used only on interactive states and focal points, CSS only, off under reduced motion, designed in **both** themes (#127). Specimen used for the review: https://claude.ai/artifact/RMpPsdcoSHJwNfkUXcB4LU (round 2; hover sweeps from round 1 were dropped by the owner).

**Light comes from the teams.** `--light` is the glow's color: plain white light at night and ink by day, and a team's contrast-checked color wherever a team is in view (`.tsi-team-light` on an element carrying `teamColorVars`; a team page sets `--page-team-dark` / `--page-team-light` on `:root` through `components/team/page-team-light.tsx`). Glows fall slightly downward, as if lit from above, everywhere.

| Effect | Dark | Light (designed separately) |
|---|---|---|
| **Glow** (`.tsi-lit`, `.tsi-lit-hover`, `.tsi-glow-below`) | Bloom: 1 px rim ~70%, 6 px glow ~40%, 22 px glow ~18%, offset 2–4 px down | A 1 px rim in the full color plus light cast below (0 6 px 16 px, −6 px spread, ~60%): bloom can't show on white |
| **Border light** (`.tsi-border-light` + `components/ui/border-light.tsx`) | Two arcs, one per team color, run around the border in 7 s, with a blurred copy behind as bloom | Thicker arcs (2.5 px), no bloom |

| Where | Light | Color |
|---|---|---|
| Header rule (`.tsi-header`) | Bloom under the rule at night | White/black; the team's color on team pages (both themes) |
| Selected main-nav item (`.tsi-nav-active`) | Underline glows | Page light |
| Selected toggles (`Segmented`, `DivisionNav`) | Still glow; the pill stays black/white so text never sits on a team color | Page light |
| Keyboard focus | Outline unchanged, glow behind it | Page light |
| Rankings rows (`.tsi-row-light`) | Left edge lights **on hover only**, #1 included (owner: no permanent effect on #1) | That team's color |
| Matchup cards (This week) | Border + glow on hover | The team TSI favors; neutral without a prediction |
| Win-probability bars | Each side glows, still | Its team's color |
| Team page | Header rule, header band glow, profile and win-total bars, focus and toggles | The team's color |
| Rating trend chart | The latest point glows | The series' team color |
| **Border light** | The scoreboard of the game center and the matchup tool (shared `ScoreBoard`); planned: games of the week (13.4), projected champion (13.6, with its path lit) | The two teams' colors |

**Rules:** no glowing text (`text-shadow`); no new hues (black, white, neutrals, team colors mixed with transparency); contrast checked with the light on; glows are static (a 160 ms fade on hover), and the border light is the only animation, on a page's focal point only. Under `prefers-reduced-motion` the border light's animation is removed (not shortened by the global 0.01 ms rule, which would flicker) and it becomes a still two-color border. The rings sit outside Tailwind's layers for one rule (`margin: 0`), so a panel's `space-y-*` can't shorten them. Performance: the arc rotates a conic gradient through the registered `@property --tsi-angle`; box-shadows never animate.

**Checked (2026-11-06, local site on the live API):** rankings, This week, team page, game center and matchup tool in both themes at 1440 and 390 px (screenshots); reduced motion turns the border light still; `npm run check` clean.

## Routes

| Route | Page |
|---|---|
| `/` | **Home** (13.4, #141): FBS and FCS games of the week, FBS and FCS Top 25 rails, one Power/Résumé toggle |
| `/rankings` | **Rankings** (Power/Résumé toggle), FBS (was `/` until 13.4) |
| `/rankings/fcs`, `/rankings/all` | FCS rankings; FBS and FCS on one scale (Power only) (#115) |
| `/week` → `/week/[season]/[week]` | **Matchup board** for the week (defaults to current week), games with an FBS team |
| `/week/[season]/[week]/fcs`, `…/all` | the same board for games with an FCS team, or either (#115) |
| `/games/[id]` | **Game center** |
| `/teams/[slug]` | **Team page** |
| `/matchup` | **Hypothetical matchup tool** (#85) |
| `/playoff` | **CFP projections + bracket** (#101); `/playoff/fcs`: FCS playoff (#125) |
| `/conferences/[slug]` | Standings + title odds (later) |

## Page specs

### Rankings `/`
- Toggle: Power | Résumé. Filters: conference, Top 25 / all.
- Columns: Rank, Δ (movement arrow), Team (logo + name), Record, TSI rating, Off (rank), Def (rank), SOS, SOR, Proj. W (season sim, links to the team's projected record), Conf (conference title %), CFP % (later).
- Sortable (TanStack Table). Sticky header. Clicking a row opens the team page.
- Side widget: biggest risers/fallers since the latest Sunday poll (#134). **Built (#88):** "Biggest movers", top 5 each way for the active ranking and conference (ignores Top 25/All), "#52 → #37" with the Δ arrow; beside the table from `xl`, below it otherwise; hidden without a baseline run.
- **This season only:** both rankings use the `season` ratings (no preseason prior). A one-line note under the toggle says so.
- **Provisional:** teams with fewer than 4 games show a *provisional* tag next to their rank.
- **Updated daily:** the header shows "Updated {date}". Δ arrows and biggest movers compare with the **latest Sunday poll** (Phase 12.5, #126, #134): the last run of the most recent Sunday (Eastern) before the shown run's day. On a Sunday that is the previous Sunday (the week's official move); Monday–Saturday it is that Sunday, so midweek results show. The header names it: "Arrows show each team's move since Sun, Nov 8."
- **Résumé tab:** a short explainer: "How hard would it be for a typical #12 team to match this record against this schedule? Re-evaluated daily as opponents' seasons play out." Clicking a team's SOR opens its team page at the **Résumé** section (#89): the rank, record, what a typical #12 team would expect from the same games, and how often it would match the record; the schedule's "#12 team wins" column shows each game's difficulty against the opponent's current rating (muted until the game counts).
- **Built (decision #70):** Power/Résumé toggle, Top 25 / all, conference filter (client-side over both rankings, rendered once on the server); TanStack Table v9 sorting with a sticky header inside the table's own scroll area; Δ = movement since the latest Sunday poll (`previous_rank` from the last run of the most recent Sunday before the shown run, Eastern time, `previous_as_of`; the intro names its date, e.g. "since Sun, Nov 8"; no Δ column without one; #79, #134), offense/defense ranks (`off_rank`/`def_rank`) from the API; row click and team-name links go to the team page; logos on a light chip so dark marks stay visible.

### Matchup board `/week/[season]/[week]`
- Week selector + filters: Top 25 only, conference, sort by kickoff / closest game (TSI plays and the edge sort were removed with the Book, #139).
- **Matchup card:** logos & ranks, kickoff/TV, win-probability bar in team colors, projected score, a TSI line vs. market line row (spread, total, ML).
- After games: final score, ✔/✘ for each market, CLV.
- **Built (decision #71):** `/week` redirects to the current week; `generateStaticParams` prerenders it and other weeks render on first visit (params awaited inside `<Suspense>`). Filters: Top 25 only, conference; sort: kickoff (grouped by day), closest game (TSI plays and biggest edge removed, #139). Card: kickoff (ET), Top-25 ranks, projected score (final score once over, with TSI's projection beside it), win-probability bar, TSI vs. Vegas for spread / total / moneyline (favorite named). No TV listings (CFBD media not ingested).
- **Ranks in the All view (Phase 12.6, #135):** FBS Top 25 ranks stay plain numbers; FCS Top 25 ranks show as a small muted "FCS 8" chip (`components/board/board-ranks.ts`, `matchup-card.tsx`; muted text on the muted background, 5.3:1 light / 5.5:1 dark), and a card with one widens both rank slots so names stay aligned. "Top 25 only" there keeps games with a Top 25 team of either division.
- **Team colors** (Phase 13.2, #138) go through `lib/format/color.ts`, per theme via CSS variables (`--team-dark` / `--team-light`) or `teamColor(team, theme)`: never white, black or gray (OKLCH chroma < 0.04 is skipped); the first team color at ≥ 2:1 against that theme's card; else the team's color lightened (dark) or darkened (light) to 2.5:1, same hue; else a neutral (no team needs it in 2026). The colors themselves are CFBD's, with sourced corrections in `backend/src/tsi/team_colors.py` applied by the API. Contact sheet of every team in both themes: https://claude.ai/artifact/NLTUN6CbWTaLSKaj2Mzm81.

### Game center `/games/[id]`
- **Header:** both teams, records, TSI ranks, kickoff, venue, projected score, win probability.
- **Odds board:** spread / total / moneyline / team totals, with **Fair** vs. **TSI Book** vs. **Market** columns and edge highlighted.
- **Alt-line ladder:** cover/over probability at each number around the line.
- **Margin distribution chart:** histogram/density of predicted margin with the market spread marked (and key numbers marked in v2).
- **Tale of the tape:** mirrored bar chart of off/def ratings, EPA/play, success rate, explosiveness, pace (ranks shown).
- **Rating trends:** both teams' TSI rating by week on one chart.
- **Post-game:** final score, how each market graded, snapshot history ("line moved from X to Y").
- **Built (decision #72):** this week's games are prerendered and others render on first visit (inside `<Suspense>`; an unknown id streams the not-found page with `noindex`). Sections: score-bug header (final score once over), odds board (TSI's line with its cover/over chance at the nearest bettable line, next to Vegas; no Book prices or plays since #139; team totals have no market data yet), margin density with Tie and Vegas lines (whole-point hover; cover chance from the API's alt-spread ladder, never computed in the browser), alt spread and total ladders with the Vegas rung highlighted, tale of the tape (ranks, rating, off/def, SOS, record; the better side bold), rating trends (home solid, away dashed, direct end labels, neutral away color when the team colors look alike) and prediction history. EPA, success rate, explosiveness and pace in the tape wait for an API addition. Games without a snapshot say why (before Oct 20, 2026, or not yet within eight days).

### Team page `/teams/[slug]`
- Header gradient in team colors, logo, record, Power rank, Résumé rank, rating.
- **Rating trend** line chart (season, with the preseason prior shown as the starting point).
- **Efficiency profile:** off/def percentile bars (or radar) vs. FBS.
- **Schedule table:** each game with opponent, TSI win prob (pre-game for played games, current for upcoming), result, spread result.
- **Projected record** (#98): record now, projected wins, chance to win out, conference title % and title-game %, and a bar chart of final win totals (plain server-rendered HTML bars with a screen-reader table, no chart library). Shown for every rated team; a value the API lacks is left out. CFP % later.
- If manually adjusted (#104): an "Adjusted" note with the reason and the raw model's line, total and win chance (game cards, game center); the team page lists adjustments in effect and marks adjusted schedule lines with †.
- **Built (decision #73):** the current Top 25 is prerendered and every other team renders on first visit (`<Suspense>`; unknown slug → not found). Header: a solid team-color band (flat per #69, instead of a gradient), logo, mascot, conference, record, Power/Résumé rank, rating, predictive rating (rank), SOS. Profile: power/résumé/offense/defense rank bars among rated FBS teams (ranks from `/rankings`). Rating trend: the shared `components/charts/rating-trend-chart.tsx` (one or two teams; y ticks every 2/5/10 points with ≥ 2 points of padding). Schedule: date, opponent (with Top-25 rank and site), result or projected score (links to the game center), TSI line and win chance from the team's side: the published snapshot when there is one, else the API's `/matchup` with today's ratings, marked * "if played today". Non-FBS teams show their schedule with "no rating". Not yet: preseason prior as the trend's starting point (live history starts Oct 19, 2026), percentiles for EPA/success/explosiveness, spread result per game (needs market lines in the team endpoint), projected record.

### Playoff `/playoff`
- **Built (decision #101):** from the latest nightly simulation (`GET /playoff`; regular season only, a plain message otherwise). **Projected bracket:** one representative valid field (each power conference's likeliest champion, the likeliest group-of-six team, Notre Dame if among the twelve likeliest, then at-large by playoff odds), seeded by average seed; first round → quarterfinals → semifinals → championship in four columns (stacked on phones), pairings from the API's format; in each game the team likelier to reach the next round advances, ending in a projected champion. **Playoff odds:** every team with a 1%+ chance: record, Résumé rank, playoff, bye, semifinal, final and title chances, and title odds (fair American odds). Team pages add "Makes the playoff" and "Wins the title" to the projected record.
- **FCS (#125, built 2026-11-05):** `/playoff/fcs` (FBS / FCS links under the heading): the 24-team bracket in five rounds (three columns below 1536 px, numbers only for the 16 seeds) and odds with playoff, bye, quarterfinal, semifinal, final and title chances. The bracket is drawn from the API's generic `rounds`. FCS team pages and FCS rankings show projected wins and conference odds.

### Matchup `/matchup`
- **Built (decision #85):** pick any two FBS teams (away/home, neutral-site checkbox) in a plain GET form grouped by conference: works without JavaScript, and results are shareable URLs (`/matchup?away=auburn&home=alabama&neutral=1`); "Swap home and away" is a link. Result: the shared `ScoreBoard` (projected score, win probability), TSI's line (no Vegas column: books only post scheduled games), the margin chart (from `sigma_margin`), alternate spread/total ladders and the tale of the tape. Labeled hypothetical: not saved or graded. Empty state suggests three top-6 pairings on neutral fields; same team twice or an unknown slug get a plain message.

### Home `/` (Phase 13.4, #141, built 2026-11-06)
- **Layout:** desktop (`lg`+): FBS Top 25 rail left, FCS Top 25 rail right (15.5 rem, 18 rem from `xl`), the two games of the week stacked in the middle (FBS first, larger). Phones and tablets: games first, then the two rails (side by side from `sm`). One **Power / Résumé** toggle (`Segmented`) switches the rails and the picks (`components/home/`).
- **Game card** (`game-of-week.tsx`): kickoff (ET, formatted on the server), both teams with their current rank in the chosen ranking and record, TSI's projected score (its own row, so the scores line up when a name wraps; the final score once played, with TSI's projection in the caption), win-probability bar, TSI's line next to Vegas, a plain-language "why this game" (ranks, TSI's win chance, and the stakes: "A win would raise X's playoff chances by N points and Y's by M", swings under 5 points left out), and a link to the game center. Both cards carry the **border light** in the two teams' colors (#137). Before the first pick a card says picks come with Sunday's rankings.
- **Rails** (`rankings-rail.tsx`): rank, logo on a white tile (dark logos vanish on black), school, record, movement since the Sunday poll (hidden while a division has no previous poll, so FCS doesn't say "new" 25 times); rows light in the team's color on hover (`li.tsi-row-light`).
- **Picks** come from `/games-of-week`: by the chosen ranking alone, the game whose lower-ranked team is ranked highest (#142), picked with Sunday's rankings and held all week.

### TSI Book and Model pages: removed (Phase 13.3, #139)
The Book is owner-only and there is no public Model or "How TSI works" page (#127). `/book` and `/model` are gone (404), with their nav links, sitemap entries, components and charts; the API serves the ledger and the report card only with the owner's key. Their specs and build notes (#75, #76) are in git history.

## Shared components
`TeamBadge`, `WinProbBar`, `OddsCell` (American odds formatting), `EdgeBadge`, `RatingDelta`, `StatBar` (mirrored), `TrendChart`, `DistributionChart`, `KpiTile`, `SeasonWeekPicker`, `UpdatedFooter`.

## Data fetching
- Server Components call the FastAPI service through a typed client (`web/lib/api.ts`, types generated from OpenAPI).
- ISR with tag-based revalidation (see [02-architecture.md](02-architecture.md)).
- Loading skeletons and empty states (e.g. "Lines not posted yet").
- SEO/OG: dynamic Open Graph images for game and team pages (makes shared links look great).

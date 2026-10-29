# 03 – Data Sources

## Primary: CollegeFootballData.com (CFBD)
- Get a key at https://collegefootballdata.com/key. Store it as `CFBD_API_KEY`.
- Accessed with a thin `httpx` wrapper (`tsi/ingest/client.py`), not the official `cfbd` package, so raw JSON can be cached and every call counted. Base URL `https://api.collegefootballdata.com`, Bearer auth. Responses include an `X-CallLimit-Remaining` header, which the client logs.
- **The free tier is ~1,000 calls/month** (per CFBD's API v2 announcement; paid Patreon tiers raise it, and the limits can change, so confirm when signing up). That's why caching is mandatory: completed seasons are fetched once and live in Postgres forever.

### Call budget
Every real CFBD request (including failed ones) is recorded in `ingest_log`; cache hits are free and not logged. Ingest checks the month's count against `CFBD_MONTHLY_CALL_BUDGET` and stops before exceeding it.

| Job | Calls (estimate) |
|---|---|
| Backfill, per season: prefer **season-wide** requests (`year=` with no week) for games, advanced stats, PPA, drives, lines, talent, returning production | ~10–25 |
| Full backfill 2014–2026 (13 seasons) | ~150–325, spread over **2+ sessions** with the disk cache on |
| Daily job: games + 2× advanced stats + lines | 4 per day (~124/month) |

- Fetch a small test season (e.g. 2024) first and verify the call count before the full backfill.
- If the budget gets tight, drop `/games/teams` (advanced stats cover most of it) or move to a paid tier.

### Endpoints we use

| Data | Endpoint (client method area) | Used for |
|---|---|---|
| Teams (FBS list, colors, logos) | `/teams`, `/teams/fbs` | `teams` table, branding |
| Venues | `/venues` | neutral site / travel (later) |
| Calendar | `/calendar` | season/week boundaries |
| Games & scores | `/games` | `games` table |
| Team box stats | `/games/teams` | basic per-game stats |
| Advanced game stats | `/stats/game/advanced` (×2: `excludeGarbageTime=true` and full game) | Filtered: EPA/play, success rate, explosiveness, rush/pass EPA. Full game: plays and drives, so points per drive matches full-game points. Includes postseason. Teams are named by school, matched to our ids through the game |
| ~~PPA/EPA by game~~ | ~~`/ppa/games`~~ | Not needed: covered by advanced stats |
| ~~Drives~~ | ~~`/drives`~~ | Not needed: drive counts come from advanced stats |
| Betting lines | `/lines` | spreads, totals, moneylines by provider |
| Talent composite | `/talent` | preseason prior |
| Returning production | `/player/returning` | preseason prior |
| Recruiting | `/recruiting/teams` | prior (optional) |
| SP+, Elo, FPI | `/ratings/sp`, `/ratings/elo`, `/ratings/fpi` | comparison only, **never model inputs** |
| AP / Coaches poll | `/rankings` | comparison only |

### Ingestion rules
- **Historical backfill:** seasons 2014–2025 (2014 provides the priors for 2015, the first backtest season).
- **Idempotent upserts:** re-running ingest for a week never duplicates rows.
- **Raw response cache + freshness** (`ingest/freshness.py`): raw JSON is cached on disk (`backend/.cache/`, gitignored).
  - **Finished season** (a response fetched after Feb 1 of the following year): served from cache forever.
  - **In-progress season:** a cached response expires after 6 hours, so the daily job always gets new results.
  - **No season** (e.g. `/venues`): expires after 30 days.
  - `--refresh` forces a re-fetch.
- **Daily job:** `tsi ingest daily` runs from GitHub Actions at 10:00 UTC. It re-fetches current-season games (~1 call/day); teams and calendar are loaded only when a season first appears.
- **Garbage time:** use CFBD's garbage-time-filtered advanced stats where offered.
- **FCS opponents:** ingest the games and the FCS team rows (division = `fcs`) so FCS expansion needs no schema change.
- **Conference/division per season:** write `team_seasons` from each season's `/teams?year=` response, because teams change conferences and move FCS→FBS.

### Market lines
- CFBD `/lines` returns lines from multiple providers (2024: ESPN Bet, DraftKings, Bovada), with team ids. All providers are stored. A **consensus** line (median across providers) is computed in Phase 3.
- **Sign:** `spread` is from the home team's view, negative = home favored. Verified two ways: 0 mismatches against CFBD's `formattedSpread`, and closing-spread MAE vs. actual margin of ~12 pts (vs. ~25 if flipped).
- **Change-only snapshots:** a new `market_lines` row is stored only when a provider's numbers change, so the daily job builds real line movement without duplicate rows.
- **Closing:** a snapshot captured at or after kickoff is `is_closing`. If the numbers didn't change, the latest stored row is flagged instead of adding a duplicate.
- **Caveat:** for historical seasons, CFBD gives one line per provider (plus the opening spread/total), not a timestamped history. Treat that line as the approximate close. During the live season, our own Tue/Thu fetches create real snapshots.
- Optional later: The Odds API for fresher in-week odds and line movement.

## Data quality checks (`tsi check`, rules in `quality/checks.py`)
**Fail** (correctness; exit code 1):
- Look-ahead: completed game with a future kickoff, stats on an unplayed game, a closing line that isn't the book's last snapshot or whose game hasn't started (a pre-kickoff capture is fine: change-only snapshots)
- Integrity: a game's team without a `team_seasons` row, stats points ≠ game score
- FBS data the model needs: FBS game with stats for only one side, or completed without a score

**Warn** (known CFBD gaps the model must tolerate):
- Non-FBS completed games without a score
- FBS-vs-FBS games without advanced stats or without a closing spread
- FBS game 2+ days past kickoff but not final (cancelled/stale)
- FBS game within 3 days of kickoff with no line yet
- FBS team with fewer than 10 games in a finished season (2020 excluded)
- FBS team missing talent or returning production

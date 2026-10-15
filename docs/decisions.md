# Decision Log

Add an entry when a meaningful decision is made or reversed. Newest at the bottom.

| # | Date | Decision | Why |
|---|---|---|---|
| 1 | 2026-10-14 | Project is **The Swann Index (TSI)**, a personal CFB rating model + dashboard | Owner's long-standing idea; strong portfolio piece |
| 2 | 2026-10-14 | **Public, read-only** site; no user accounts | Portfolio visibility; only the owner runs the model |
| 3 | 2026-10-14 | **FBS only** at launch; schema division-agnostic; FCS is Phase 10 | Keep MVP scoped without blocking expansion |
| 4 | 2026-10-14 | **Pure-stats** model v1; manual adjustments later as a separate, visible layer | Establish an honest baseline first |
| 5 | 2026-10-14 | Prediction engine prices **full markets** (spread, total, ML, team totals, alts) from one joint score distribution | Owner wants a complete "bookie"-style predictor; one distribution keeps lines consistent |
| 6 | 2026-10-14 | Paper-trading only, immutable timestamped snapshots, CLV tracking | Honest public track record; no real-money handling |
| 7 | 2026-10-14 | Stack: Python/FastAPI + Postgres (Neon) + Next.js/Tailwind on Vercel; GH Actions cron | Popular stack; Python fits the modeling; no Docker required |
| 8 | 2026-10-14 | Data source: CollegeFootballData.com API | Free, comprehensive, has an official Python client |
| 9 | 2026-10-14 | Build **one roadmap item at a time**; small single-purpose modules (~200-line target); pure math separated from I/O | Owner preference; keeps code reviewable and backtests testable |
| 10 | 2026-10-14 | Secrets only via env vars (`pydantic-settings` / `process.env`), `.env.example` per app, gitleaks pre-commit hook | Never commit keys; automated guard instead of relying on memory |
| 11 | 2026-10-14 | Conference & division move to a per-season `team_seasons` table | Realignment and FCS→FBS moves would corrupt historical backtests if stored on `teams` |
| 12 | 2026-10-14 | `predictions` gets a `variant` (raw/adjusted); lock = latest snapshot before kickoff (derived, no `locked` flag) | Satisfies rule 6 from day one; no cron needed at kickoff; keeps snapshots insert-only |
| 13 | 2026-10-14 | `ingest_log` + `CFBD_MONTHLY_CALL_BUDGET` guard; season-wide requests for backfill | Free tier ≈ 1,000 calls/month |
| 14 | 2026-10-14 | Python installed and pinned via `uv`, not winget | Avoids Store-alias/PATH issues; one tool manages Python + packages |
| 15 | 2026-10-14 | Use vetted third-party skills (Anthropic / vendor first), installed per phase, reviewed and recorded in `.claude/skills/SOURCES.md` | Reuse proven patterns without supply-chain surprises |
| 16 | 2026-10-14 | `team_game_stats` stores offense only; `model_runs.kind` = live/backtest; DB trigger enforces prediction immutability | No duplicated defensive rows; backtests share tables but can be re-run; rule 2 enforced by the database, not just code |
| 17 | 2026-10-14 | CFBD accessed via a thin `httpx` client instead of the official `cfbd` package | Raw JSON is easy to cache on disk and every call is logged to `ingest_log`; fewer dependencies |
| 18 | 2026-10-14 | Daily automated refresh (GitHub Actions, 10:00 UTC) instead of only weekly; cache freshness rule by season | Owner wants rankings to update the day after games; ~30 CFBD calls/month for games |
| 19 | 2026-10-14 | Until Phase 6, the daily job writes to the Neon **dev** branch (`DATABASE_URL` secret) | Production isn't in use yet; switch the secret to `production` at go-live |
| 20 | 2026-10-14 | Efficiency stats garbage-time filtered; plays/drives from full-game stats; `/drives` and `/ppa/games` dropped | Points per drive must use full-game drives to match full-game points (1,048 of 3,212 2024 team-games differ); advanced stats already include drive counts, saving calls |
| 21 | 2026-10-14 | Market lines stored as change-only snapshots; closing = snapshot at/after kickoff (or latest row flagged); lines added to the daily job | Real line-movement history without ~800 duplicate rows per day; closing lines needed for CLV and the report card |
| 22 | 2026-10-14 | DB-backed tests run in a throwaway `test_<random>` schema inside the dev database (dropped after); skipped when no DB is configured | No local Postgres/Docker needed; real tables untouched; catches SQL/ORM bugs that pure tests miss |
| 23 | 2026-10-14 | **Two rating sets:** `season` (this season's games only) drives Power/Résumé rankings; `predictive` (adds a preseason prior that fades to zero by midseason) drives predictions and the Book. Teams with <4 games are ranked as *provisional* | Owner: rankings must reflect only the current season, not prior years; predictions still need early-season accuracy |
| 24 | 2026-10-14 | Résumé benchmark = a typical **#12** team; SOR uses each opponent's **current** rating, so past wins lose or gain value as opponents' seasons play out (dynamic SOS) | #12 ≈ playoff bubble in a 12-team CFP. Owner wants wins re-valued as opponents rise or fall. Résumé is retrospective, so this isn't look-ahead |
| 25 | 2026-10-14 | Rankings and ratings refit **daily** in the nightly job (not weekly) | Owner: midweek games (e.g. Tuesday MACtion) should show by the next morning |
| 26 | 2026-10-14 | 2020 (COVID) treated like any other season in fitting, tuning, and backtests | Owner preference; it's real data, just fewer games |
| 27 | 2026-10-14 | No go-live deadline: Phase 2 gets full tuning (2015–22) and validation (2023–25) before launch | Owner isn't constrained by bowl season |
| 28 | 2026-10-14 | v1 model = baseline exactly as doc 04 (PPD + EPA ridge, HFA, pooled FCS, fading prior, Elo comparison); refinements after it's working end to end | Get a complete, honest baseline first |

## Open questions
- API host: Render vs. Fly.io (decide in Phase 6)
- Recharts vs. visx for the distribution chart (decide in Phase 5)
- Exact CFP format/seeding rules for the playoff projector (verify before Phase 8)
- Provisional threshold (4 games?) and prior cutoff week (6–8?): set in Phase 2 backtest
- Off-season: pause the nightly job Feb–Jul to save calls? (low priority: ~124 calls/month fits easily)

## Resolved
- ~~Résumé benchmark #12 vs. #25~~ → #12 (#24)
- ~~Go-live scope~~ → no deadline; tune fully (#27)
- ~~Is the CFBD free tier enough?~~ → yes: full 2014–2026 backfill took ~90 calls; ongoing ~124/month of ~1,000

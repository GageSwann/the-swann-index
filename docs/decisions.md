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

## Open questions
- API host: Render vs. Fly.io (decide in Phase 6)
- Recharts vs. visx for the distribution chart (decide in Phase 5)
- Exact CFP format/seeding rules for the playoff projector (verify before Phase 8)
- Should the Résumé benchmark be "typical #12 team" or "typical #25 team"? (test in Phase 2)
- Go-live scope: if Phase 2 tuning runs long, launch with untuned defaults + Elo comparison before bowls and finish tuning after? (decide end of Phase 1)
- CFBD paid tier: is the free 1,000 calls/month enough after the backfill? (decide after the 2024 test-season ingest)

# Transfer meter (decision #145)

Measures how many bytes the database sends for a nightly run, an API request or a site
build: the quantity Neon bills as network transfer. Runs against a **local Postgres copy
only** (`meterlib.relay_env` refuses any non-local host), so measuring costs no Neon
transfer. Production adds a few percent for TLS.

How it works: `pgproxy.py` is a TCP relay on `127.0.0.1:5433` in front of local Postgres
(`5432`) that counts bytes in each direction; its control port `5434` answers
`down up connections`. The other scripts point `DATABASE_URL` / `DATABASE_URL_DIRECT` at
the relay and read the counter before and after each step (or each SQL statement).

Run everything from `backend/` with this folder on `PYTHONPATH` (not `python -I`, which
drops it). In Git Bash, prefix commands whose arguments start with `/` with
`MSYS_NO_PATHCONV=1`, or `/teams/x` becomes `C:/Program Files/Git/teams/x`.

```bash
M=../.claude/skills/tsi-weekly-run/scripts/transfer_meter
uv run python -I $M/pgproxy.py &                                   # 1. the relay
PYTHONPATH=$M uv run python $M/profile_cli.py out.csv run          # nightly run, bytes per query
PYTHONPATH=$M uv run python $M/run_cmd.py nightly -- uv run tsi run   # total only
MSYS_NO_PATHCONV=1 PYTHONPATH=$M uv run python $M/profile_api.py "/rankings?division=fbs" "/teams/notre-dame"
PYTHONPATH=$M uv run python $M/serve_relay.py &                    # API on :8001 through the relay
PYTHONPATH=$M uv run python $M/api_bytes.py                         # bytes per endpoint, cold and warm
# site build: TSI_API_URL=http://127.0.0.1:8001 npm run build in web/, read the counter before/after
```

`parity_snapshot.py OUT.pkl` saves the rankings and season projection at a fixed time for
a before/after comparison of a refactor (identical `repr` = identical output).

Baseline (2026-11-09, local copy through Nov 9; decision #145):

| What | Bytes |
|---|---|
| Nightly `tsi run` | 12.6 MB before #145, **7.2 MB** after (Elo still reads every season: 3.7 MB) |
| Full site build (`npm run build`, 119 pages) | 17.6 MB |
| `/rankings` | ~267 KB |
| `/playoff` | ~189 KB |
| `/weeks/{s}/{w}/games` | 145–200 KB |
| `/teams/{slug}` | ~87 KB |
| `/games/{id}` | ~3 KB |
| `/matchup` first call (removed in #145) | 4.5 MB |

Endpoint costs don't grow with the number of stored runs. A local `next start` of a
production build returned 500 on team, week and rankings pages after `/api/revalidate`
("`usePathname()` in a Client Component outside of `<Suspense>`"); the live site doesn't,
so page-by-page refresh costs were estimated from the endpoint costs instead.

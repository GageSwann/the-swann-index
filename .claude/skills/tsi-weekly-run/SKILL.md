---
name: tsi-weekly-run
description: Operator runbook for The Swann Index (TSI) in production. Use it whenever the user asks whether last night's run worked, why the site didn't update or shows old data, how the model or the TSI Book did this week, to re-run the nightly job or refresh the site, to deploy, roll back or check Render/Vercel/GitHub Actions, about Neon branches (production vs dev) or applying a migration to production, about rotating a secret or token, or when anything on https://the-swann-index.vercel.app looks broken. Use it even if they just say "how did we do this week?" or "is the site up to date?".
---

# TSI operator runbook

TSI runs itself: a nightly GitHub Action updates the database and refreshes the site.
This runbook covers checking that, fixing it when it doesn't, the weekly review, and
the rare manual jobs (deploys, rollbacks, migrations, secret rotation). Project rules in
`CLAUDE.md` still apply; the ones that matter most here are repeated below.

## The system

| Piece | Where | Updated by |
|---|---|---|
| Site | https://the-swann-index.vercel.app (Vercel, root `web/`) | every push to `main`; nightly cache refresh |
| API | https://tsi-api-44wx.onrender.com (Render free web service `tsi-api`, Docker) | push to `main` touching `backend/`, after CI passes |
| Database | Neon project `nameless-morning-73071395`, branch **`production`** (`br-purple-frog-b5ee7m4a`) | nightly job only |
| Local dev DB | Neon branch **`dev`** (`br-long-dust-b5phcp0e`), a copy of production | local work (`backend/.env`) |
| Nightly job | `.github/workflows/daily-refresh.yml`, cron 10:00 UTC | `tsi run` (ingest, rate, grade, publish), then site refresh |
| CI | `.github/workflows/ci.yml` | every push and pull request; gates Render deploys |

Pages are served from Vercel's cache. The API is only called when the cache refreshes
(nightly, hourly at most, or on first visit to an uncached page). The free Render API
sleeps after ~15 idle minutes and takes up to a minute to wake, so a slow first API
call is normal, not an outage.

## Ground rules

- **Production is the Neon `production` branch.** Local tools (`backend/.env`) point at
  `dev`. Never put the production connection string in `backend/.env`; to touch
  production on purpose, use a temporary shell variable (see "Migrations").
- **Published predictions are immutable** (CLAUDE.md rule 2). Never edit or delete
  snapshots or picks in the database to "fix" a result; a DB trigger rejects updates
  anyway. Corrections happen by publishing new snapshots before kickoff.
- **Secrets never pass through the chat.** The owner pastes them into dashboards and
  GitHub themselves. When a check needs one, print booleans or lengths only.
- **Ask the owner before** running the nightly job by hand (it writes to production and
  spends CFBD calls), applying a migration, changing a workflow, or rolling back.

## 1. Daily check: did last night's run work?

```bash
gh run list --workflow daily-refresh.yml --limit 5
gh run view <run-id> --log | grep -E "ingest |rate |grade |board |publish |revalidated\"|Z [0-9]{3} /"
curl -s https://tsi-api-44wx.onrender.com/meta/current
curl -s https://the-swann-index.vercel.app/ | grep -oE "Model updated [^<]{0,40}" | head -1
```

The cron is 10:00 UTC, but GitHub often starts scheduled jobs hours late (13:50–16:40
UTC has been normal). A run that hasn't started by ~20:00 UTC is worth a look.

What a healthy log says:

| Line | Meaning |
|---|---|
| `ingest 2026: N games, N stat rows, N new line snapshots` | CFBD refresh (~4 calls); line snapshots are stored only when numbers change |
| `rate 138 FBS teams, #1 ... -> model_runs.id=N` | new daily ratings + rankings |
| `grade N picks W-L-P, +X units` | locked picks of finished games graded; 0 on days without finished games |
| `board N games, N TSI Plays` / `publish N new snapshots (N unchanged), N picks` | predictions for the next 8 days; a snapshot is inserted only when something changed |
| `{"revalidated":"tsi",...}` then `200 /`, `200 /week`, ... | the site was told to refresh and its main pages reloaded |

Then confirm `ratings_updated_at` from `/meta/current` matches the run, and the site's
"Model updated" time (US Eastern) matches it too. If the API is newer than the site,
the refresh step failed: see Troubleshooting.

## 2. Re-running the nightly job (owner's OK first)

```bash
gh workflow run daily-refresh.yml
sleep 10; gh run watch $(gh run list --workflow daily-refresh.yml --limit 1 --json databaseId --jq '.[0].databaseId') --exit-status
```

Re-running is safe: ingest reuses its cache and only spends calls on the in-progress
season, rating adds a new run, grading skips already graded picks, and publishing
inserts only what changed. It does spend ~4 CFBD calls.

To refresh only the site (no pipeline), the owner runs this in their own PowerShell
with the token from their password manager. Never ask for the token.

```powershell
$t = Read-Host "REVALIDATE_TOKEN" -AsSecureString
$plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($t))
Invoke-RestMethod -Method Post -Uri https://the-swann-index.vercel.app/api/revalidate -Headers @{ Authorization = "Bearer $plain" }
```

The response is `{"revalidated":"tsi",...}`. The next visit to each page gets the old
page once while the new one builds, so load the main pages once afterwards.

## 3. Weekly review

Run after the Sunday-morning nightly run has graded Saturday's games:

```bash
python .claude/skills/tsi-weekly-run/scripts/weekly_review.py            # last completed week, production API
python .claude/skills/tsi-weekly-run/scripts/weekly_review.py --week 9   # a specific week
python .claude/skills/tsi-weekly-run/scripts/weekly_review.py --api http://127.0.0.1:8000  # local dev API
```

It reads only the public API (no secrets) and prints Markdown: data freshness, the TSI
Book (season and the week's graded picks with CLV), the week's prediction accuracy vs.
the closing line, Power rankings with weekly movement, and next week's ranked games,
plays and biggest disagreements with Vegas.

How to read it, so one week isn't over-interpreted:

- **CLV is the signal; the W-L record is mostly noise** over 5–10 picks a week. Positive
  average CLV (lines moving toward TSI after it bets) is what the backtest showed every
  season. A run of negative-CLV weeks is the real warning sign.
- **Margin error:** the backtest gap to the closing line is ~0.4 points. Single weeks
  swing (week 8 was 1.0); look at the season-to-date row on the Model page.
- **TSI's side vs. the closing spread** hovers near 50% by design (no spread edge), which
  is why the Book almost never bets spreads. Far below 50% for several weeks would be
  worth investigating; one bad week is not.
- Summarize for the owner in plain language with the main numbers. If the review shows
  something that changes how the model or Book should work, propose it as a scratchpad
  experiment (CLAUDE.md "Experiment before adopting"); don't change the model directly.

## 4. Deploys and rollbacks

How a change ships:

1. Push to `main` (the normal workflow; CLAUDE.md "How we work").
2. CI runs (`gh run list --workflow ci.yml --limit 1`). Vercel builds the site at the same
   time, from `web/`.
3. If the push touched `backend/` and CI passed, Render deploys the API
   (`autoDeployTrigger: checksPass`). Changes outside `backend/` (including `render.yaml`)
   don't deploy the API: after editing `render.yaml`, the owner clicks **Manual Sync** on
   the Blueprint, then **Manual Deploy** on `tsi-api`.

Verify after a deploy: `curl -s https://tsi-api-44wx.onrender.com/health` (200) and the
pages you changed. For the web, an audit at phone width catches layout breaks that only
real data shows (a long team name caused a live-only overflow once).

**Rollback**, preferred first:

- `git revert <sha>` and push: the history stays honest and both hosts redeploy.
- Site, immediately: Vercel → project → **Deployments** → the last good one → **Instant Rollback**.
- API, immediately: Render → `tsi-api` → **Events** → the last good deploy → **Rollback**.

A dashboard rollback is temporary: the next push deploys `main` again, so follow it with
a revert.

## 5. Neon branches and migrations

Which branch a connection reaches (no secrets printed):

```bash
cd backend && uv run python -c "import tsi; from sqlalchemy import text; from tsi.config import get_settings; from tsi.db.engine import make_engine; c = make_engine(get_settings()).connect(); print(c.execute(text(\"select current_setting('neon.branch_id', true)\")).scalar())"
```

`br-long-dust-…` = `dev` (expected locally); `br-purple-frog-…` = `production` (wrong for
local work: fix `backend/.env`).

**Refresh `dev` from production:** Neon console → Branches → `dev` → ⋯ → **Reset from
parent**. The endpoint and connection string stay the same. Restart a running local API
afterwards.

**Migrations:** apply and test on `dev` first (`uv run alembic upgrade head`, then
`uv run pytest`, `tsi backtest run --no-save`). For production, with the owner's OK:

1. Deploy order (CLAUDE.md): a migration that drops or renames a column goes to
   production **before** the code that depends on it is pushed; additive migrations can
   follow the code.
2. The owner opens a fresh PowerShell in `backend/`, sets the production **direct**
   (non-pooled) string for that session only, applies, and closes the window:

   ```powershell
   $env:DATABASE_URL_DIRECT = Read-Host "production direct URL"
   $env:DATABASE_URL = $env:DATABASE_URL_DIRECT
   uv run alembic upgrade head
   exit
   ```

   Environment variables win over `backend/.env`, so nothing local changes.
3. Check the live API afterwards (`/meta/current`, `/rankings`).

## 6. Rotating secrets

Generate tokens with the system's secure generator (PowerShell):

```powershell
$b = New-Object byte[] 32; [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b); ($b | % { $_.ToString('x2') }) -join ''
```

| Secret | Lives in | To rotate |
|---|---|---|
| `REVALIDATE_TOKEN` | Vercel env; GitHub secret | new token → Vercel → Settings → Environment Variables → edit → **redeploy** (env changes apply to new deployments only); GitHub secret → update. Until both match, the nightly refresh step fails with 401 |
| `DATABASE_URL` (production) | Render env; GitHub secret | Neon → Roles → reset `neondb_owner` password (this changes **every** branch's string, `dev` too) → copy new pooled strings → Render (Save, rebuild, and deploy), GitHub secret, and the owner's `backend/.env` for `dev` |
| `CFBD_API_KEY` | GitHub secret; `backend/.env` | new key at collegefootballdata.com → update both |

After any rotation, run the daily check (section 1) after the next nightly run, or re-run
it with the owner's OK.

## 7. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| API returns 500, Render log shows `relation "…" does not exist` | `DATABASE_URL` points at an empty branch | Render env must be the `production` branch's pooled string (host `ep-soft-firefly-…-pooler`) |
| Site shows yesterday's "Model updated" time, API is newer | refresh step failed or was skipped | check the run log for the refresh step; 401 = token mismatch between Vercel and GitHub (rotate both); skipped = `SITE_URL` / `TSI_API_URL` repo variables missing (`gh variable list`); then refresh only the site (section 2) |
| Nightly job: `run the live pipeline` failed | ingest failed (CFBD down, quota) or DB unreachable | the rest of `tsi run` still runs on stored data and exits 1; read the log; CFBD outages resolve themselves; check the call budget below |
| First page load or API call takes ~60 s | Render free tier woke from sleep | normal; the nightly refresh step wakes it before refreshing the site |
| Vercel build fails at "Generating static pages" | API down or too slow during prerendering | check `/health`; the build allows 180 s per page (`staticPageGenerationTimeout`); redeploy once the API is up |
| Render build fails immediately ("Exited with status 1") | Dockerfile path or a dependency problem | paths in `render.yaml` are relative to `rootDir` (`backend/`); read the build log's last lines |
| CI fails on `npm run check` with type errors after an API change | generated types out of date | `uv run tsi openapi`, then `npm run api:types` in `web/`, commit both (CLAUDE.md "API changes") |
| API 500s under load (`QueuePool limit … reached`) | many cold-cache requests at once | in-process caches must be single-flight (CLAUDE.md "Neon latency"); see `services/read/matchup.py` |
| Rankings arrows missing | no rating run ≥ 6 days older (start of a season) | expected; the Δ column hides itself until a week of runs exists |

**CFBD call budget:** the free tier is ~1,000 calls a month; the client refuses past 980
(`CFBD_MONTHLY_CALL_BUDGET`). The nightly job uses ~4 a day. Calls are logged in the
`ingest_log` table of whichever branch made them, and CFBD reports what's left in each
response (`calls remaining` in the ingest log lines). Backfills (`tsi ingest season`)
cost ~9 calls per uncached season: avoid them near the end of a month.

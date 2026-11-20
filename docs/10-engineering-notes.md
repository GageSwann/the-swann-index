# 10 – Engineering notes

Things learned the hard way. `CLAUDE.md` keeps the short version of each; the details live here. Read the section for the area you're touching. Each note names the decision it came from (`decisions.md`).

## 1. Neon network transfer (the budget that took the site down)

**The limit (#140):** Neon's free plan allows **5 GB of network transfer a month for the whole project**, every branch counted (`dev` too) and every reader (local scripts, GitHub Actions, Render). Over the limit Neon **suspends the compute until the next billing period**: connections are refused ("exceeded the quota"), the API's `/health` still answers 200 but every data endpoint answers 500.

**History:** the period that started Oct 31 hit 5.40 GB on 2026-11-09 (production 4.19, dev 1.21) and Neon suspended the project that evening; the project total froze at **5.6 GB**. On Nov 20 the owner added Neon's $5 limit increase (25 GB) for one period to come back early (#151); the new period (Nov 20 – Dec 1) started at 0 GB and serves to prove the free 5 GB fits.

**Where it went (#145, measured with the transfer meter):** the site re-checked every visited page's data **hourly** (~1,000 ISR writes and ~30 MB of gzipped API responses a day, ~0.3 GB a day from Neon). Since #145 pages re-check daily and the nightly refresh is what updates them.

**What reads what now** (local copy, transfer meter):

| Reader | Before | Now |
|---|---|---|
| Nightly `tsi run` | 12.6 MB | 3.0 MB (#146 Elo carry, #147 one read per season) |
| Nightly page refresh (~60 pages) | 7.3 MB | 3.3 MB (#148 Résumé context cache) |
| A full site build (~120 pages) | 17.6 MB | 9.95 MB (2026-11-20) |
| `/rankings` · `/playoff` · week board | ~267 · ~189 · 145–200 KB | same |
| `/teams/{slug}` | ~87 KB | ~8 KB after #148; ~42 KB with the rebuilt season's ~90 runs (the rating history reads every run) |
| Home page | 764 KB | same (largest left) |

**Heavy (never against Neon without the owner's OK):** `tsi backtest run` / `book`, scratch experiments, `tsi model fit`, `tsi model elo-carry`, the backtest and migrate-with-reload workflows, `tsi ingest season`, a full replay (13.8), `pg_dump`. Run them on a **local copy** (§2) and write only results to Neon. **Light:** the nightly job, the API, site builds (but batch pushes: each web push rebuilds the site from the live API).

**Measuring:**
- The **transfer meter** (`.claude/skills/tsi-weekly-run/scripts/transfer_meter/`) is a byte-counting relay in front of a local Postgres: exact server-to-client bytes, what Neon bills. Check every new reader with it before shipping, never against Neon. Neon itself gives no per-query bytes; `pg_stat_statements` shows rows per call but is cleared whenever the compute scales to zero.
- Measuring the site in `next dev` overcounts: dev runs `generateStaticParams` on every visit, so each team page re-read the FBS rankings (9.5 MB of a 15.8 MB pass in #148). Disable it for the measurement.
- **Neon console:** the project's **Overview** shows the period's total (the number the limit uses; the Billing page shows transfer only after an overage). Each branch's Overview shows its own share, but **while the project is suspended the branch panels read 0** ("metrics are not updated for inactive projects"; seen 2026-11-20 while the project total read 5.6 GB). Per branch by API: `data_transfer_bytes` from the branch details endpoint (needs a Neon API key). The project page says "Since Nov 1" and the branch page "Since Oct 31" for the same period (time zones).
- The database is ~63 MB, so one `pg_dump` costs about that; the danger is *repeated* full reads (2.89 GB by Nov 6 ≈ 46 of them).

**While suspended:** the site serves its cached pages as long as nothing expires them, so the nightly job is paused (`gh workflow disable daily-refresh.yml`): its refresh step runs even after a failed `tsi run` and would expire the pages. Pushes fail CI's web job (it prerenders from the live API), so Render deploys nothing, and Vercel's build fails (the old site stays). Coming back (done 2026-11-20): confirm Neon answers, Render Manual Deploy (CI was red), re-enable and run the nightly job, then redeploy the site.

## 2. Local Postgres copy

Both PCs have one; it is where heavy work runs (§1).
- **Work PC** (it can't reach Neon at all): local Postgres 17, 2014–2026 re-ingested from the CFBD disk cache, current through Nov 9; no production snapshot or pick history. #145 was measured on it.
- **Home PC:** portable PostgreSQL 17.11 (EDB binaries, no admin rights or service) in `%LOCALAPPDATA%\Programs\PostgreSQL17`, database `tsi`, trust auth on localhost only. Start it after a reboot: `pg_ctl -D "%LOCALAPPDATA%\Programs\PostgreSQL17\data" -l "%LOCALAPPDATA%\Programs\PostgreSQL17\server.log" start` (from its `bin`).
- **Point tools at it** by setting both `DATABASE_URL` and `DATABASE_URL_DIRECT` to `postgresql+psycopg://postgres@localhost:5432/tsi` for the command. Alembic and the DB tests use the direct one; setting only one sends them to `dev`.
- The server must use `timezone = UTC` (Neon's), or three API tests fail on `-05:00` timestamps.
- Building one: re-ingest from the CFBD disk cache (`tsi ingest season --season 2014 --through 2026`, no transfer, ~11 CFBD calls for the current season, no live-only tables), or one `pg_dump` of `dev` (~63 MB of transfer, every table including snapshots and picks). Then `alembic upgrade head` and one `tsi run`.

## 3. Database and SQLAlchemy

- **SQLAlchemy 2.1:** don't `dict(session.execute(...))`; unpack rows in a comprehension. Use `.ext(postgresql.distinct_on(...))`, not `.distinct(cols)`.
- **Upserts** always go through `db/upsert.py` (batched executemany, skips unchanged rows). Never send the same primary key twice in one batch; de-duplicate first.
- **Filter by id lists** with `one_of(col, ids)` (`db/queries/filters.py`, `= ANY(array)`), never `.in_()`.
- **Alembic** autogenerate misses primary-key changes; hand-write those. Pass the short constraint name (e.g. `"basis"`), never the full `ck_table_name`.
- **numpy threads:** `tsi/__init__.py` caps BLAS at 1 thread (multithreading made our small solves ~40× slower). Scratch scripts must `import tsi` before numpy.

## 4. API performance

- **Where time goes:** locally each Neon round trip is ~30 ms, so round trips dominate. In production (Render Ohio next to Neon us-east-2) a round trip is a few ms but Render's free tier has **0.1 CPU**, so Python CPU per request dominates (≈10× local; gzip runs at level 1 for that reason, #136).
- **Measure both:** round trips with a SQLAlchemy `before_cursor_execute` counter; CPU with `time.process_time()` averaged over ~20 requests (the Windows clock ticks every 15.6 ms). Profile in-process with `TestClient(create_app())` used as a context manager (the lifespan creates the sessions).
- **Endpoints are `async` and do all database work through `deps.read(sessions, lambda s: ...)`** (#102). Never a sync endpoint with a session dependency: it deadlocked the pool under build bursts. At most 10 requests run at once (`CONCURRENT_REQUESTS`, below the 15-connection pool).
- The API engine autocommits (`make_engine(read_only=True)`, #93); every engine pings connections before use (#99); the site's API client retries transient 5xx/network failures (`web/lib/api/retry.ts`).
- **In-process caches that load from the DB must be single-flight** (one loader behind a lock, like `ResumeCache`, #148): a cold-cache burst (a site build) otherwise exhausts the pool. Cache only what can't go stale (a saved run never changes) or key it by run.
- `tsi serve --reload` on Windows can stop reloading after the first change: restart it when results look stale.

## 5. The nightly job and CFBD

- `tsi run` takes ~35 s in Actions, mostly CFBD downloads. CFBD is slowest at the top of the hour (full-season advanced stats > 30 s at 11:00 UTC, ~15 s later; #144). The client has a 60 s read timeout, retries after 5 s / 30 s, honors `Retry-After` on 429, and runs same-endpoint requests one at a time.
- The ingest fetches its requests concurrently (`CfbdClient.prefetch`, #106): a new daily loader declares `requests(season)` and joins the prefetch in `services/results.py`.
- **Elo carry (#146):** live runs resume Elo from `model/artifacts/elo_carry.json` (end of last season) when the database's fingerprint of the 2014–2025 games and the Elo parameters match; otherwise the run logs "replaying all seasons" and reads every game (~3 MB more, numbers identical). Rebuild it (`tsi model elo-carry`, on a local copy) after each season ends, with `tsi model fit`, and whenever Elo's k / HFA / carryover / division means change.
- The run reads this season's games and stats once and shares them between ratings, rankings and the sim (`LiveInputs.shares`, #147).

## 6. Model and backtest workflow

- **Model changes:** rerun `tsi backtest run` (+ `tsi backtest book` for Book changes), then `tsi model fit`, and commit the new artifact. Save a backtest run after every model change: it is what `/model/report` serves (#76). A local save lands on the local/`dev` database; once the artifact is on `main`, the **Save backtest to production** workflow (`gh workflow run backtest.yml`, #110) saves it to production (heavy: it reads the history from production; see the roadmap item to change that). The artifact is written with LF, so an unchanged refit leaves git clean.
- **Backtest speed:** ~30 s each (`backtest book` reruns the margin backtest): ~825 daily refits × 6 ridge fits, a third in `np.linalg.solve` on ~530 columns. Vectorizing the rest saved nothing measurable (2026-11-05), and faster solvers would break bit-exact parity.
- **Parity:** dump every walk-forward pick (or rating, forecast, sim result) with `repr` floats before and after a change; refactors must be identical.
- **Season sim indexes:** FBS teams first, then FCS, then pooled opponents; FBS-only code (the CFP projector) relies on FBS being the first block. Adding teams or games changes every random draw: compare old vs. new within simulation noise.
- The experiment playbook is doc 09 §6.

## 7. Tests

- **DB tests** build the schema from the ORM, so the immutability trigger is loaded from the initial migration file (`tests/db_integration/conftest.py`). Shared builders live in `tests/factories.py`.
- **API tests** seed a tiny 2026 season (`tests/db_integration/api_seed.py`) and override `get_session` + `get_now` (clock pinned) on `create_app(...)`; the test client needs the `httpx2` dev dependency (Starlette 1.9).
- **gitleaks** flags realistic-looking fake keys in tests: use low-entropy values like `"fakekey"`.
- CI (`ci.yml`) runs on every push/PR and skips DB tests. Its web job builds the site against the **live API**, so CI goes red whenever the API is down.

## 8. Deploying

- **Who deploys what:** the nightly job runs whatever is on `main` and writes to Neon `production` (`DATABASE_URL` secret, same as Render). The API runs what Render last deployed. The site is what Vercel last built.
- **Render deploys only commits that touch `backend/` and pass CI** (`rootDir: backend`, `checksPass`), and it looks at the **newest commit of a push** only: a backend commit followed by a web/docs commit in the same push is never deployed. Make the backend commit the last one in its push. If CI was red (or the fix touched only `web/`/docs), use Render's **Manual Deploy** and confirm the live API serves the change.
- **Vercel builds only pushes that change `web/`** (`web/vercel.json` `ignoreCommand`, #144). Vercel skips the build on exit 0, builds on exit 1, and **fails the deployment on any other exit code**: on 2026-11-20 the last successful deployment (`ded3e03`) wasn't in Vercel's shallow clone, `git diff` exited 128 and the build failed. The command now checks the commit exists first and turns every error into 1 (build).
- **Ship API changes before the site** (#90): Vercel prerenders pages from the *live* API, and its build finishes before Render deploys. Push the backend, wait until the live API serves the change, then push the web (or redeploy the site).
- **Breaking API changes span two deploys:** add the new fields first and keep the old ones until the live site no longer reads them (`Playoff.format` → `rounds`, #125).
- **API changes:** run `tsi openapi` and commit `docs/api/openapi.json` (else `tests/api/test_openapi.py` fails), then `npm run api:types` in `web/` and commit `lib/api/schema.d.ts` (else `npm run check` fails). Response shapes are the dataclasses in `services/read/`; the web imports them via `lib/api/types.ts`.
- **Migration order:** a migration that **adds** what new code needs runs **before** pushing that code; one that **drops** a column runs **after** the code that stops mapping it is live (the ORM selects every mapped column). A rename is add → code switch → drop.
- **Migrating before the code is on `main`:** the **Migrate production** workflow checks out a ref. Push a temporary branch from `origin/main` holding only the migration file (no `web/` change, so Vercel skips it), `gh workflow run migrate.yml --ref <branch>`, confirm `Running upgrade` in its log, delete the branch, then push `main` with the backend commit last (done for #145).
- **GitHub Actions:** `astral-sh/setup-uv` has no floating major tag; pin the exact version (e.g. `v10.3.0`).

## 9. Web

**Next.js 16**
- Newer than training data: read the guide in `web/node_modules/next/dist/docs/` before writing Next.js code (`web/AGENTS.md`; `next dev` rewrites that file, commit it as is). Cache Components are on (`"use cache"` + cache tags, not `revalidate` exports).
- Visited pages stay in the document, hidden (React Activity, up to 3 routes): a page's `<style>` or other global side effect keeps applying after you leave. Set globals in a `useLayoutEffect` and undo them in its cleanup (`components/team/page-team-light.tsx`).
- **"A `use cache` function is awaiting a promise created outside it"** in `next dev` is a false alarm when the API is slow (a Render cold start): the dev server reruns the call after 10 s and blames shared state. Dev-only; builds allow 162 s. Warm the API first (`curl …/meta/current`).
- `next start` locally answered 500 on team, week and rankings pages after `/api/revalidate` ("`usePathname()` … outside of `<Suspense>`", 2026-11-09) while the live site was fine. Unexplained; don't rely on `next start` for checks.

**Data and caching**
- **Only through `web/lib/api/queries.ts`** (server-only, `"use cache"` + `cacheLife("tsi")` + tags); never `fetch` the API elsewhere. New `cacheLife` profiles need `next typegen` (part of `npm run typecheck`).
- **The `tsi` profile re-checks daily** (#145); the nightly `/api/revalidate` (`revalidateTag("tsi", { expire: 0 })`, roadmap 12.2) updates pages. Anything that must change during the day happens in the browser: a game's state (scheduled / in progress / final score pending / final) comes from the viewer's clock (`lib/game-phase.ts`, `components/game/game-phase.tsx`: `useGamePhase` in client components, `PhaseScope` + `When` / `PhaseLabel` around server-rendered parts; #149).
- **Team page sections appear for every ranked team** (owner, #90): when an input is missing, show the section with that value left out, never hide it.

**Look (#137, doc 06 "Lighting")**
- Black and white only (`--primary` = text color); team colors are the only color; Instrument Sans (width axis, weights 400–700). Never `text-shadow`, never a new hue, every effect designed for both themes.
- Light goes through the kit in `app/globals.css`: `--light` is the glow color (`.tsi-team-light` + `teamColorVars` makes it a team's), `.tsi-lit` / `.tsi-lit-hover` / `.tsi-glow-below`, and the border light (`components/ui/border-light.tsx`) on a page's focal point only.
- **Team colors (#138):** CFBD's colors stay in `teams`; sourced corrections live in `backend/src/tsi/team_colors.py`, applied in `team_refs`. The site picks the shown color per theme in `web/lib/format/color.ts` (never white/black/gray; lifts a too-dark color in its own hue). Check a change on every team with a contact sheet (run the real `color.ts` over all teams with `node`; Node 24 strips the types).
- **Team logos (#143):** always `components/team/team-logo.tsx` (white tile ringed in the team's color); never a bare `<Image>` of a logo.

**Building blocks**
- Charts: import from `components/charts/lazy.tsx` (lazy, same-height placeholders; #87), never directly; colors from `lib/chart-theme.ts` (`axisStyle`); shared parts in `components/charts/chart-parts.tsx` and `line-series-chart.tsx`.
- **Probabilities** always go through `chance()` (`lib/format/numbers.ts`): never "0%" or "100%" (owner, #153).
- Table headers: `components/ui/head-cell.tsx`. Dates: `lib/format/time.ts`. `cn` merges conflicting Tailwind classes, so `className` overrides win. No shadcn components remain (#77).
- **Long names:** a `TeamLink` inside a flex row needs a `min-w-0` wrapper to truncate (full name on hover); otherwise it overlaps its neighbours (biggest movers, the bracket; roadmap 12.7).
- **Screen-reader tables** ignore `sr-only`'s 1 px width and can widen a page on phones: wrap the table in an `sr-only` div (13.7).
- Page metadata: `pageMeta()` from `lib/metadata.ts`; pass `ownImage: true` on routes with an `opengraph-image` file. Indexing is off until `ALLOW_INDEXING=1` (#86).

**Checks and dependencies**
- Run `npm run check` on its own and confirm exit 0 before committing (don't pipe it). `lib/api/schema.d.ts` is Prettier-ignored (formatting it breaks `api:check`). After deleting a route, clear `web/.next` (stale `.next/dev/types` break `tsc`).
- `npm audit --omit=dev` must stay at 0 (dev-only lint tooling has known `braces` advisories; don't `audit fix --force`). npm 11 blocks `unrs-resolver`'s postinstall; ESLint works without it.

**Vercel Hobby limits** (usage on 2026-11-20, while the site was frozen): image transformations **4.7K / 5K** (4.5K on Nov 9), ISR writes 31K / 200K (30K on Nov 9), ISR reads 47K / 1M, CDN requests 57K / 1M, origin transfer 678 MB / 10 GB, active CPU 36 min / 4 h. Every other line is far from its limit.
- **Image transformations:** each logo × width is one. The 31-day `minimumCacheTTL` (#144) slowed them; the default `imageSizes` (7 widths) still turns each team into ~5 (32, 48, 64, 96, 128 px for our 17–56 px logos). Since 2026-11-20 `imageSizes: [64, 128]`: one or two per team (Next picks the smallest allowed width ≥ 1x and ≥ 2x the rendered size). Not `unoptimized`: the CFBD logos are 500 px PNGs of 18–60 KB, so a rankings page would load several MB. Formats are already WebP only.
- **ISR writes** are the signal that the daily cache works: expect roughly 60–100 a day after the reset, not ~1,000.

**Browser testing**
- Test the dev server at `http://localhost:3005`, not `127.0.0.1`: Next.js 16 refuses dev assets to an unexpected origin, so a `127.0.0.1` page never hydrates.
- Playwright isn't a project dependency: `uv run --no-project --with playwright python script.py` from a neutral folder (`python -m playwright install chromium` once per PC). With fake time use `page.clock.set_fixed_time` (`clock.install` also fakes timers).
- The site defaults to dark and ignores the system theme (next-themes): for light screenshots set `localStorage.theme = "light"` with `context.add_init_script` before loading.

## 10. Windows shell and tools

- PowerShell here-strings mangle inline Python: write scripts to the scratchpad and run them with `python -I` from a neutral directory (a local `types.py` once shadowed the stdlib). `python -I` drops the script's own folder from `sys.path`: use `PYTHONPATH` for helper modules next to a script.
- Shell heredocs turn `\n` inside Python strings into real newlines: write edit scripts with the Write tool, or use the Edit tool.
- Commit messages: bash heredoc + `git commit -F` (PowerShell `Set-Content` adds a BOM). `sed` replacements containing `#` need another delimiter.
- The console is cp1252: set `PYTHONIOENCODING=utf-8` (or write to a file) to print ★/–; use `%#I`, not `%-I`, in `strftime`.
- Git Bash rewrites arguments that start with `/` into Windows paths: prefix such commands with `MSYS_NO_PATHCONV=1`.
- **Stale `next dev` processes** survive sessions and can keep a port or lock `web/.next/dev`: list `node` processes with their command lines (`Get-CimInstance Win32_Process`, or `Get-NetTCPConnection -LocalPort 3005 -State Listen`) and stop the stale one before starting another or deleting `.next`. Deleting `.next` under a running dev server crashes it; a stale one can serve old CSS.
- The auto-mode permission check blocks disabling a workflow (`gh workflow disable`: ask the owner to run it) and stopping processes matched broadly by name (stop the one PID you started, after checking its command line).
- The artifact tools reject the short `GAGESW~1` temp path as `out_dir`; use the full `C:\Users\Gage Swann\...` path.

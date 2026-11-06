# 09 – Conventions: Code, Secrets, Workflow & Skills

How TSI code is written and how work is done. This applies to both `backend/` and `web/`.

## 1. Working style: one step at a time
- Work through [07-roadmap.md](07-roadmap.md) **one checklist item at a time**. Finish it, test it, tick it, commit it, then start the next one.
- Every item ends in a runnable state. Don't leave half-built modules lying around.
- Commits stay small and focused, using conventional prefixes: `feat:`, `fix:`, `docs:`, `test:`, `chore:`, `refactor:`.
- If an item turns out bigger than expected, split it into sub-items in the roadmap before continuing.

## 2. Modularity
**Small files with one job each.** These are guidelines, not hard limits:

| Unit | Target | Smell |
|---|---|---|
| Python module / TS file | ≤ ~200 lines | > 300 lines, so split it |
| Function | ≤ ~40 lines | needs a comment to explain its sections |
| React component | one component per file | file exports several unrelated components |

**Layering (backend):** dependencies point one way only.
```
cli / api  →  services (orchestration)  →  model / book / ingest  →  db
```
- **Pure math stays pure.** `model/` and `book/` functions take plain data (DataFrames, arrays, dataclasses) and return plain data. They do no DB queries, no HTTP, and no env reads. This makes them easy to unit test and safe for walk-forward backtests.
- **I/O lives at the edges.** Only `ingest/` talks to CFBD. Only `db/` (repositories) talks to Postgres. Only `api/` speaks HTTP.
- **Config is read in one place:** `tsi/config.py`. Other modules receive settings as arguments; they never call `os.environ` directly.

**Example: `book/` split by responsibility**
```
book/
├── distribution.py   # bivariate-normal score distribution
├── odds.py           # prob ↔ American odds, vig add/remove
├── markets.py        # spread/total/ML/team-total/alt pricing
├── edges.py          # TSI vs. market comparison
├── staking.py        # flat + fractional Kelly
├── snapshots.py      # publish immutable prediction snapshots
└── grading.py        # results, units, CLV
```
`model/`, `ingest/` (one loader per endpoint), `quality/` (rules split by severity), `cli/` (one module per command group), and `api/routers/` (one router per resource) follow the same pattern.

**Database writes:** use `tsi.db.upsert.upsert_rows`. It sends rows as one batched executemany and skips rows whose values didn't change. Don't build giant `VALUES` literals; they're 3–4× slower.

**Frontend:** `app/` route files stay thin and only fetch and compose. Components live in `components/<area>/`, formatting helpers live in `lib/format/`, and the API client lives in `lib/api/`.

## 3. Secrets & configuration
- **Never put passwords, API keys, tokens, or connection strings in code, docs, tests, or commit messages.** Read them from environment variables.
- Backend: `tsi/config.py` uses **pydantic-settings** to load `backend/.env`. A missing required variable fails fast with a clear error that names the variable, never its value.
- Web: server-only secrets (`REVALIDATE_TOKEN`) are read from `process.env` in server code only. Never prefix a secret with `NEXT_PUBLIC_`, because anything with that prefix is shipped to the browser.
- Each app has a committed `.env.example` that lists **variable names with empty or placeholder values**. Update it in the same commit that adds a new variable.
- Real `.env` / `.env.local` files are gitignored.
- CI and hosting get secrets from GitHub Actions secrets, Vercel env, and Render/Fly env.
- **Never log secrets.** Log the CFBD endpoint and params, not request headers. Mask `DATABASE_URL` if it is ever printed.
- **Automated guard:** a pre-commit hook runs **gitleaks** to block commits that contain secrets.

## 4. Code quality
- **Python:** 3.12, full type hints, `ruff` (lint + format), `pytest`. Tests mirror the source tree (`tests/model/test_ratings.py`).
- **TypeScript:** `strict: true`, ESLint + Prettier, no `any` in the API client (types are generated from OpenAPI).
- **Tests never hit the live CFBD API.** Use saved JSON fixtures in `backend/tests/fixtures/`.
- **No look-ahead guard:** model functions take an explicit `as_of` (kickoff time or season/week) and filter inside. Add a test for every new input.
- **Logging:** use the stdlib `logging` module (no `print`) in library code. The CLI may use `rich` for output.
- **Pre-commit hooks:** ruff, ruff-format, gitleaks, end-of-file/trailing-whitespace fixers.

## 5. Skills (Claude Code)
Use proven skills from others instead of reinventing patterns. **Rules for third-party skills:**
1. Prefer skills from Anthropic or from the tool's own vendor (Vercel, Neon, etc.).
2. **Read the `SKILL.md` and any scripts before installing.** Skills can run code.
3. Install into the project (`.claude/skills/`) and commit them so the setup is reproducible. Record the source repo and commit in `.claude/skills/SOURCES.md`.
4. Install a skill only when its phase starts, not all up front.

| Phase | Skill | Source | Use |
|---|---|---|---|
| any | `code-review`, `security-review`, `simplify` | built into Claude Code | review each item before committing; `security-review` before go-live |
| 2, 5, 7 | `dataviz` | built into Claude Code | backtest charts, calibration plots, all dashboard charts |
| 5 | `frontend-design` | [anthropics/skills](https://github.com/anthropics/skills) | distinctive, non-generic UI for the dashboard |
| 5 | `react-best-practices` | [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) | React / Next.js performance rules from Vercel (replaces the planned `nextjs` skill, which no longer exists; #66). Current Next.js API docs ship inside the `next` package |
| 5–7 | `webapp-testing` | [anthropics/skills](https://github.com/anthropics/skills) | Playwright checks, screenshots, phone-width tests |
| 3+ | `skill-creator` | [anthropics/skills](https://github.com/anthropics/skills) | write **our own** project skills, e.g. `tsi-weekly-run` (run, check, publish) and `tsi-backtest` |
| 6 | Vercel / Neon vendor skills or MCP servers | vendor repos | evaluated at Phase 6: not adopted, the dashboards + `gh` CLI were enough and the runbook skill covers operations (#84) |

Install command (for the [skills CLI](https://github.com/vercel-labs/skills)), run from the repo root:
```powershell
npx skills add anthropics/skills --skill frontend-design --agent claude-code
```

## 5b. Database reads cost transfer (#140)
Neon's free plan allows **5 GB of public network transfer a month for the whole project**, every branch counted; going over suspends the database (and the live API) until the next billing period. Anything that reads the full history (backtests, experiment scripts, refits, replays, backfills, dumps) runs against a **local Postgres copy**, never Neon, and writes only its results back. Check the Neon console's usage before heavy work and ask the owner. Batch pushes: every push rebuilds ~100 site pages from the live API.

## 6. Model experiments: the playbook (lessons from Phase 11, #118–#125)
How a model idea gets tested, distilled from what worked and what misled us.

**Before believing a gain**
- **Small MAE gains need a paired test.** Compare the two models game by game (difference in absolute error per game, mean ÷ standard error). v1.5's signals passed at 2.3–2.6 SE; the totals signals (#123) looked good on MAE but were ≤ 1.6 SE and were rejected.
- **Check every season, not just the two periods.** A gain that comes mostly from one season (2023 kept showing up) is fragile; report the per-season deltas.
- **Combinations rarely add much.** Screen signals one at a time first; pairs usually add little beyond the best single one.
- **For totals changes, run the Book backtest too.** Totals drive the Book's profit: a lower totals MAE can still make the Book worse (#123: every candidate cut validation ROI). For margin changes, check that the Book is unchanged and watch the refit `k_spread`.
- **More complex isn't more accurate.** Gradient boosting on top of the ratings (#121) and per-closeness key-number weights (#119) were worse out of sample. The linear stack plus small, well-tested corrections wins.

**Look for gaps by game type**
- Break errors down by **game type** (FBS–FBS, FBS–FCS, FCS–FCS), **season stage** (stack bucket) and **size of the prediction**. The biggest single gain of the phase (#124: FBS-vs-FCS margins overshot by ~30%, MAE 14.34 → 12.56) was invisible in the headline FBS numbers and only showed up while checking the FCS sim's inputs.
- Compare TSI's bias with the **closing line's** bias on the same games: if the line is close to unbiased and TSI isn't, it's a model problem, not noise in the games.
- Check σ (log loss by σ) and the sim's τ for any new group before reusing the FBS values; for FCS both held (#125).

**Corrections after the stack**
- Fit post-stack corrections (rest #120, FBS-vs-FCS #124) on **held-out** stack predictions with the same leave-one-season-out rule as the stacks (`backtest/situational_fit.py`, `backtest/cross_division_fit.py`); fit production on all seasons the same way in `services/model_fit.py`.
- Prefer the simplest form that holds out of sample (one or two factors, an offset) and leave groups with too few games unadjusted.
- When a correction needs games the stacks don't learn from (FCS), walk them forward but keep every other fitted piece on FBS-vs-FBS games, then confirm the rest of the artifact is **byte-identical** after the refit.

**Verifying changes**
- **Refactors:** snapshot the output before (a pickle of the sim's projections, the backtest numbers) and prove it identical after. Example: the shared Résumé helper (`services/playoff_resume.py`) reproduced the FBS playoff odds exactly.
- **Intended changes that alter random draws:** adding teams or games to the season sim changes every draw, so compare against the old run within simulation noise (max 0.05 wins at 4,000 sims), and check the totals: 24 in the field, one champion per conference and per simulation.
- **Committee stand-ins and formats:** check against real history (the FCS Résumé picked 88 of 96 real playoff teams, 2022–25), and get the **current season's format from the owner or the NCAA**, not from last year's data (the 2026 FCS bracket seeds 16, not 8).

**Record everything**
- Every experiment, adopted or rejected, gets a `decisions.md` entry with the numbers and the scratchpad script names. Rejected ideas are as useful as adopted ones: they stop us retrying them.

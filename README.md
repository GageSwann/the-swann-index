# The Swann Index (TSI)

A personal college football power rating model and prediction engine, with a public read-only dashboard.

TSI rates every FBS team from opponent-adjusted efficiency data, then turns those ratings into a full sportsbook-style board for every game: projected scores, spreads, totals, moneylines, win probabilities, and edges against the betting market. Every prediction is timestamped and graded, so the model's track record is public and honest.

> Status: **Planning.** See [docs/07-roadmap.md](docs/07-roadmap.md) for the current phase.

## What's in it

- **Rankings:** Power (who's best) and Résumé (who's earned it), updated weekly
- **Team pages:** rating trend, offense/defense profile, schedule with win odds, projected wins
- **Weekly board:** every matchup with TSI lines vs. Vegas lines, flagged edges
- **Game center:** projected score, full odds board, alt-line ladder, score distribution
- **TSI Book:** paper-traded picks ledger with ATS record, ROI, and closing line value
- **Model report card:** walk-forward backtests, calibration, comparisons vs. Vegas / SP+ / AP

## Stack

| Layer | Tech |
|---|---|
| Model & data pipeline | Python 3.12, pandas, NumPy, SciPy, scikit-learn |
| API | FastAPI |
| Database | PostgreSQL (Neon) via SQLAlchemy + Alembic |
| Frontend | Next.js (App Router), React, TypeScript, Tailwind CSS, Recharts |
| Automation | GitHub Actions (weekly model runs) |
| Hosting | Vercel (web), Render/Fly.io (API) |
| Data | [CollegeFootballData.com](https://collegefootballdata.com) API |

## Documentation

| Doc | Contents |
|---|---|
| [01 – Vision](docs/01-vision.md) | What TSI is, goals, non-goals, success criteria |
| [02 – Architecture](docs/02-architecture.md) | System design, repo layout, data flow, API, hosting |
| [03 – Data Sources](docs/03-data-sources.md) | CFBD endpoints, ingestion and caching rules |
| [04 – Model](docs/04-model.md) | Rating methodology, priors, backtesting |
| [05 – Prediction Engine & Book](docs/05-sportsbook.md) | Score distributions, odds, market edges, picks ledger |
| [06 – Frontend](docs/06-frontend.md) | Pages, components, visuals, design direction |
| [07 – Roadmap](docs/07-roadmap.md) | Phased build plan with checklists |
| [08 – Windows Setup](docs/08-setup-windows.md) | Phase 0 environment setup |
| [09 – Conventions](docs/09-conventions.md) | Workflow, modularity, secrets, skills |
| [Decisions](docs/decisions.md) | Decision log and open questions |

---

*TSI is a statistical model built for analysis and entertainment. It does not take or place wagers.*

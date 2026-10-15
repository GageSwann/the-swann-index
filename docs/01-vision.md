# 01 – Vision

## One-liner
**The Swann Index (TSI)** is my own college football power rating model, wrapped in a dashboard that works like a sportsbook: it ranks every team, predicts every game, prices the lines, and keeps an honest public record of how it does.

## Why
- I want my own model with my own methodology, not a copy of a list someone else made.
- It's a portfolio piece that covers real data engineering, statistical modeling, a Python API, and a polished React frontend, all deployed and running automatically.

## Who it's for
| User | What they do |
|---|---|
| **Me (operator)** | Runs and tunes the model, adds manual adjustments (later), reviews backtests |
| **Public viewers** | Read-only: browse rankings, teams, games, odds, and the track record |
| **Recruiters/engineers** | Live site + clean repo + methodology page that shows how it works |

There are no user accounts. Operator actions happen locally or through GitHub Actions, not through the website.

## Core features (MVP)
1. **TSI Power Rankings:** all FBS teams rated in points vs. an average team, with offense/defense split and week-over-week movement.
2. **TSI Résumé Rankings:** strength-of-record ranking (who has earned the most with their results).
3. **Team pages:** colors/logo, rating trend, efficiency profile, schedule with win probabilities, projected record.
4. **Weekly matchup board:** every game with TSI spread/total/moneyline next to market lines, with edges flagged.
5. **Game center:** projected score, win probability, full odds board, alt lines, score distribution chart, head-to-head comparison; graded after the game.
6. **Prediction engine ("the bookie"):** fair and vigged lines for spread, total, moneyline, and team totals, plus cover/over probabilities at any number.
7. **TSI Book ledger:** auto-logged paper picks with ATS and O/U record, units, ROI, closing line value.
8. **Model report card:** walk-forward backtest results and live-season accuracy against Vegas, SP+, and the AP poll.

## Later features
- Season simulation: projected wins, conference title odds, CFP playoff odds and bracket
- Hypothetical matchup tool (any two teams, any site)
- Manual adjustments layer (injuries, QB changes), shown transparently as raw vs. adjusted
- FCS expansion (full FCS ratings, not just a pooled FCS opponent)
- Advanced markets: first half, key-number pricing, props
- AI-written game previews

## Non-goals
- User accounts, logins, or user-submitted picks
- Taking, placing, or facilitating real wagers; the "book" is paper/analysis only
- Native mobile app (the site must be responsive instead)
- FCS in the MVP (but the schema must support it)

## Success criteria
| Metric | Target |
|---|---|
| Backtest margin MAE (2015–2025, walk-forward) | Within ~1 point of the closing line's MAE |
| Straight-up winner accuracy | ≥ 72% on FBS vs. FBS games |
| Calibration | Win-probability bins within ±3 pts of observed rate |
| ATS vs. closing line | > 50% (beating 52.4% would be exceptional) |
| Weekly pipeline | Runs unattended every week; site updates without manual deploys |
| Site | Public URL, Lighthouse performance ≥ 90, works on phone |

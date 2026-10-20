# 05 – Prediction Engine & TSI Book

The goal is to make TSI work like a full bookmaker: for every game it should be able to price any market and say where it disagrees with the real market. This is all **analysis and paper trading**; TSI never handles real money.

## 1. Score distribution
Every game prediction is a **joint distribution of the two teams' scores**, not just a single number. Every market comes from that one distribution, so the lines are always consistent with each other.

**v1: bivariate normal**
- Means: `proj_home`, `proj_away` (from [04-model.md](04-model.md))
- Std devs and correlation `ρ` fit from backtest residuals (`model/distribution.py`, `distribution_fit.py`; decision #51):
  - margin σ = the win-probability σ (log loss at 0): **15.2** in production
  - total σ grows with the projected total: **16.4 + 0.12 × (total − 55)**, fit by log loss of P(total > projection + d) for d = ±3…±14
  - ρ(margin, total) = **0.0075 × projected home margin** (clipped ±0.5): ~0 in close games, ~+0.2 when a team is favored by 25+ (blowouts raise totals)
  - team totals follow: home = (total + margin)/2, away = (total − margin)/2, both normal
- Residuals are close to normal (kurtosis 3.0–3.5), so v1 is a reasonable start; key numbers wait for v2

**v2: Monte Carlo simulation (later)**
- Simulate 10k+ games (drive-level or score-event-level) so that scores land on real football numbers
- Captures **key numbers** (3, 7, 10, 14), push probabilities, and fat tails

## 2. Markets priced

| Market | Derived from |
|---|---|
| Win probability | P(margin > 0) |
| **Spread** (fair) | mean margin |
| **Total** (fair) | mean total |
| **Moneyline** | win prob → American odds |
| Team totals | each team's score distribution |
| Alt spreads / alt totals ladder | P(margin > x), P(total > x) for x across a range |
| Cover probability at any line | P(margin > −line) |
| First half (later) | needs half-level model from quarter scores |

### Odds conversion
```
fair American odds (p ≥ 0.5) = −100 · p / (1 − p)
fair American odds (p < 0.5) = +100 · (1 − p) / p
```
**Fair** lines have no vig. **TSI Book** lines add a configurable hold (default: spreads/totals at −110/−110, moneylines priced to ~4.5% hold) so they look like a real board. The UI shows both.

**Implementation** (`book/odds.py`, `book/pricing.py`, settings in `book/config.py`): a side TSI gives probability p is priced at implied p / (1 − hold), so −110/−110 is a hold of 1/22 (4.55%). Main spread/total/team-total lines = the fair line rounded to the nearest half point (quarter points round up), priced flat at −110 (`main_line_odds`; set `None` to price from probability). Moneylines and alt ladders (±10 pts in 1-pt steps around the main line) are priced from probability. Spread probabilities are home view: home covers spread s when margin + s > 0. v1 has no push probability on whole numbers (continuous distribution).

## 3. Market comparison & edges
For each game, using the consensus market line:
- **Market implied probability:** remove the vig from the two-way moneyline (normalize the implied probabilities)
- **Spread edge:** `P_TSI(cover at market spread) − 0.5238` (break-even at −110)
- **Total edge:** same for over/under
- **Moneyline edge:** `P_TSI(win) − market_no_vig_prob`, and expected value per unit
- **Points disagreement:** `TSI spread − market spread` (easy to read on cards)

**TSI Plays:** a game becomes an official pick when its edge clears a threshold. Each pick gets a 1–3 ★ confidence tier based on edge size. Thresholds are tuned in backtest so that the tiers actually mean something.

## 4. Stake sizing (paper)
- Flat 1 unit by default
- Optional suggested stake: **fractional Kelly** (¼ Kelly), capped at 3 units
- Both are tracked, so the ledger can show flat vs. Kelly results

## 5. Prediction lifecycle & integrity
1. **Generated** when lines are ingested (Tue/Thu)
2. **Published** as an immutable snapshot with a `published_at` timestamp
3. Re-runs create **new** snapshots and never overwrite old ones; the site shows the latest pre-kickoff snapshot
4. **Locked** at kickoff
5. **Graded** after the final: spread/total/ML result, units won, and **CLV** (closing line value: the line TSI picked vs. the closing line)

CLV is the best long-run skill signal. If TSI consistently beats the closing line, the model has real signal even when short-term results are noisy.

## 6. TSI Book ledger (what the site shows)
- Season and all-time record: ATS, O/U, ML, by ★ tier
- Units won, ROI, cumulative units chart
- Average CLV, % of picks that beat the close
- Filterable pick history with a link to each game center

## 7. Season simulation (later phase)
Using the same game distributions plus **rating uncertainty** (sample team ratings each sim):
- Projected win distribution per team
- Conference title odds (standings + championship game; tiebreakers approximated)
- **CFP odds and projected bracket:** selection approximated with TSI Résumé as a committee proxy. *Check the current CFP format and seeding rules before building; keep them configurable since the format has been changing.*
- Futures-style fair odds (e.g. "TSI fair odds to win the national title: +450")

## 8. Calibration checks (must pass before launch)
- Spread: TSI-predicted cover probabilities vs. observed cover rate by bin
- Totals: same for overs
- Win probability: reliability diagram within ±3 pts per bin
- If calibration is off, fix σ/ρ before touching anything else

**First run (2026-10-19, validation 2023–25):** win probability passes (4 of 5 bins within ±3; 80–90% bin +4.3). **Cover/over probabilities at the closing line fail badly**: TSI's 70%+ covers hit 45%, 65–70% overs hit 50%. This is not a σ problem: the closing line is more accurate than TSI, so TSI's disagreement with it is mostly noise (fitted shrink factor for spreads = 0.00 on train and validation; totals 0.07). Against **opening** lines TSI does predict where the line moves (corr +0.16 to +0.21, positive CLV at every edge size), and totals beat the opener in validation (53.0% at 3+ pts edge, 55.0% at 5+, 59.4% at 7+), spreads do not (~50%). How edges turn into probabilities is decided with item 4 (market comparison & edges).

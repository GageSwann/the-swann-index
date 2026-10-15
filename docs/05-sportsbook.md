# 05 – Prediction Engine & TSI Book

The goal is to make TSI work like a full bookmaker: for every game it should be able to price any market and say where it disagrees with the real market. This is all **analysis and paper trading**; TSI never handles real money.

## 1. Score distribution
Every game prediction is a **joint distribution of the two teams' scores**, not just a single number. Every market comes from that one distribution, so the lines are always consistent with each other.

**v1: bivariate normal**
- Means: `proj_home`, `proj_away` (from [04-model.md](04-model.md))
- Std devs and correlation `ρ` fit from backtest residuals (expect margin σ ≈ 13–17)
- σ can vary by matchup (e.g. larger for high-pace / high-variance teams); start with a global value

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

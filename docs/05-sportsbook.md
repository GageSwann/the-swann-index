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

**Implementation** (`book/consensus.py`, `book/edges.py`, `book/shrink_fit.py`; decisions #52, #53):
- **Consensus** = each sportsbook's latest line at or before the publish time (`db/queries/market.line_snapshots`; aggregator "providers" `consensus` and `teamrankings` excluded). Spread and total: median across books. Moneyline: each book's pair de-vigged, then averaged.
- **Shrunk probabilities:** the Book moves a fraction k from the market's number toward TSI's: P(home covers s) = Φ(k·(TSI margin + s)/σ_margin), P(over t) = Φ(k·(TSI total − t)/σ_total); moneyline uses the spread-implied margin moved by k_spread.
- **k** is fit by log loss on leave-one-season-out predictions against the **median opening line** (history has no publish-time snapshots; the opener is the closest proxy). Production: **k_spread 0.07, k_total 0.32**. Backtest (train → validation): spread 0.00, total 0.24.
- **Edges:** spread/total = shrunk P − 0.5238 (−110 assumed: CFBD has no spread prices); moneyline = shrunk P − no-vig P, with EV per unit at the market price. The better side of each market is reported.
- Validation calibration at the opener (k from train): spreads 50.0% predicted / 49.9% observed; overs within ±0.5 pts in the bins holding 93% of games.

**TSI Plays:** a game becomes an official pick when its edge clears a threshold. Each pick gets a 1–3 ★ confidence tier based on edge size. Thresholds are tuned in backtest so that the tiers actually mean something.

## 4. Stake sizing (paper)
- Flat 1 unit by default
- Optional suggested stake: **fractional Kelly** (¼ Kelly), capped at 3 units
- Both are tracked, so the ledger can show flat vs. Kelly results

**Implementation** (`book/picks.py`, decision #54): the better side of each market becomes a pick when its edge reaches the 1★ threshold. Thresholds in probability points: spreads and totals **1.5 / 3 / 5** (1★/2★/3★), moneylines 3 / 5 / 8 and EV must be positive. With k_total ≈ 0.3 that means TSI about 5 / 7 / 10 points off the total; spreads need ~20+ points off the line (k_spread 0.07), so spread picks are rare by design. Kelly: f = (b·p − q)/b on a 100-unit bankroll, × ¼, capped at 3 units. Backtest at the median opener (k from train): validation totals 1★ 148 picks 56.1% (+8.4% ROI), 2★ 33 at 63.6%, 3★ 4 at 75%. Train has only ~126 picks (openers start in 2021), too few to tune thresholds on, so they stay at principled round values until live publish-time data accumulates.

## 5. Prediction lifecycle & integrity
1. **Generated** when lines are ingested (Tue/Thu)
2. **Published** as an immutable snapshot with a `published_at` timestamp
3. Re-runs create **new** snapshots and never overwrite old ones; the site shows the latest pre-kickoff snapshot
4. **Locked** at kickoff
5. **Graded** after the final: spread/total/ML result, units won, and **CLV** (closing line value: the line TSI picked vs. the closing line)

**Implementation** (decision #55): `tsi book publish` builds the board (`services/board.py`: forecast → prices → consensus as of now → edges → picks) and inserts a new snapshot + picks under a `live` model run for every game kicking off in the next 8 days whose forecast, Book prices or picks changed since its latest snapshot (unchanged games are skipped). `tsi book grade` grades picks on each game's locked snapshot only (latest `published_at` < kickoff, derived in `db/queries/predictions.py`), filling result, units and the closing consensus line; CLV is computed from those columns (`book/grading.py`). Live features match the walk-forward backtest exactly (checked on 2026 games: 0 difference).

CLV is the best long-run skill signal. If TSI consistently beats the closing line, the model has real signal even when short-term results are noisy.

## 6. TSI Book ledger (what the site shows)
- Season and all-time record: ATS, O/U, ML, by ★ tier
- Units won, ROI, cumulative units chart
- Average CLV, % of picks that beat the close
- Filterable pick history with a link to each game center

**Book backtest** (`tsi backtest book`, decision #56): the picks the Book would have made at the median opener (2021+; shrink k fit on train), graded on the final, CLV vs. the closing consensus (median of sportsbooks, #59). Moneylines are not backtested (no historical opening prices); spreads produce no picks (k_spread = 0 on train).

| Totals | Bets | W-L-P | Win | ROI (flat) | CLV | Beat close |
|---|---|---|---|---|---|---|
| Train 2021–22 (k fit here) | 123 | 63-58-2 | 52.1% | −0.6% | +1.12 | 67% |
| **Validation 2023–25** | 181 | 104-75-2 | **58.1%** | **+10.8%** | +0.93 | 60% |
| 1★ / 2★ / 3★ (validation) | 144 / 33 / 4 | | 56.3% / 63.6% / 75% | +7.5% / +21.5% / +43% | | |
| 2026 to date | 22 | 10-12-0 | 45.5% | −13.2% | +0.91 | 64% |

CLV is positive in every season (+0.2 to +1.8 points): lines move toward TSI's totals picks, the most reliable sign of signal. Win rates are noisy at these sample sizes (train 2★ went 15-19). Checked and rejected: an intercept in the shrink (base rate of overs) improved log loss but turned the Book into an under-only bettor (503 of 508 validation bets) with lower ROI (+2.6%).

## 7. Season simulation
Using the same game distributions plus **rating uncertainty**:
- Projected win distribution per team (built: `tsi sim season`, decision #94)
- Conference title odds (standings + championship game; tiebreakers approximated; built: #96, §7.3)
- **CFP odds and projected bracket:** selection approximated with TSI Résumé as a committee proxy, using the 2026–27 format below (keep it configurable: the format has changed every year so far)
- Futures-style fair odds (e.g. "TSI fair odds to win the national title: +450")

### 7.1 Rating uncertainty (#94)
Every remaining regular-season game gets the published forecast (`services/predict.py`: same model, same mean margin, σ_margin 15.4). A simulated season (`sim/season.py`, 10,000 by default, fixed seed) draws one shift per team, d ~ N(0, τ), kept for all of its remaining games:

    margin = forecast + d_home − d_away + e,   sd(e) = √(σ² − 2τ²)

so each single game keeps the site's win probability, and a team that is better than its rating shows it in several games at once. **τ(week) = 7.15 − 0.114 × week** (regular-season week, held at week 15 for the postseason; `sim/uncertainty.py`).

Fit: fixed-cutoff forecasts of every remaining regular-season game from weeks 1, 4, 7, 10 and 13 of 2015–2025 (conference title games excluded); τ² = mean product of a team's side-signed residuals over pairs of its remaining games. Train estimates by cutoff: 7.0, 6.8, 6.3, 5.8, 5.8 (validation: 7.3, 6.2, 5.6, 5.4, 3.3). Scored by the mean log probability of each FBS team's actual remaining wins (20,000 sims per cutoff):

| τ multiplier | 0 (independent games) | 0.5 | 0.75 | **1.0** | 1.25 |
|---|---|---|---|---|---|
| Train 2015–22 | −1.584 | −1.544 | −1.523 | **−1.520** | −1.539 |
| Validate 2023–25 | −1.670 | −1.620 | −1.590 | **−1.579** | −1.589 |

The forecasts use the production artifact, so the stack weights are in-sample for these seasons; τ is a covariance across games and barely depends on them. Live check (dev, week 9 of 2026): each team's expected wins equal its wins so far plus the sum of its games' published win probabilities, within 0.014 wins at 40,000 sims.

### 7.2 CFP format, 2026–27 (owner, #95)
- **12 teams.** Automatic bids: the **ACC, Big Ten, Big 12 and SEC champions**; the **highest-ranked team from the American, Conference USA, MAC, Mountain West, Pac-12 or Sun Belt** (champion or not); **Notre Dame** if it ranks in the top 12. The rest are at-large by ranking.
- **Seeds 1–4** (first-round byes) = the four highest-ranked teams, champions or not. Seeds 5–12 follow the ranking.
- **First round** (Dec 18–19) at the higher seed's home: 5 v 12, 6 v 11, 7 v 10, 8 v 9.
- **Quarterfinals** (Fiesta Dec 30; Cotton, Rose, Peach Jan 1), **no re-seeding**: 1 v 8/9, 2 v 7/10, 3 v 6/11, 4 v 5/12. **Semifinals**: Orange (Jan 14) and Sugar (Jan 15). The 1 and 4 quarterfinals meet in one semifinal (the 1 seed picks which), the 2 and 3 quarterfinals in the other; for the projections only the pairing matters, not the bowl. **Title game**: Monday, Jan 25, 2027, Las Vegas.
- Neutral sites from the quarterfinals on; the first round has home field.
- Committee rankings: Nov 3, 10, 17, 24, Dec 1, selection Sunday Dec 6.

### 7.3 Conference titles (#96)
- **Standings** in each simulated season from conference games (finished results + simulated ones). **Simplified tiebreakers** (owner-approved): conference win %, then head-to-head among the teams tied on it (0.5 if they didn't meet), then the better rating in that simulation (`sim/standings.py`).
- **Finalists:** the top two, or each division's winner when the conference has divisions (`team_seasons.conference_division`, from CFBD's `division`; in 2026 only the Sun Belt: East/West). FBS Independents have no title game.
- **Title game:** neutral site; mean margin from the published model (antisymmetric: A vs B = −(B vs A), checked over 435 pairs), plus both teams' shifts and game noise from the same simulation. The champion gets the win, so projected wins include it. Once the real title game is on the schedule (CFBD marks it only in `notes`; 2025's weren't flagged as conference games), its finalists are fixed and it is simulated like any remaining game.
- Checks on dev (week 9, 40k sims): per conference, P(in title game) sums to 2.0000 and P(champion) to 1.0000; expected wins = wins + Σ published win probabilities + P(champion) within 0.014.

## 8. Calibration checks (must pass before launch)
- Spread: TSI-predicted cover probabilities vs. observed cover rate by bin
- Totals: same for overs
- Win probability: reliability diagram within ±3 pts per bin
- If calibration is off, fix σ/ρ before touching anything else

**First run (2026-10-19, validation 2023–25):** win probability passes (4 of 5 bins within ±3; 80–90% bin +4.3). **Cover/over probabilities at the closing line fail badly**: TSI's 70%+ covers hit 45%, 65–70% overs hit 50%. This is not a σ problem: the closing line is more accurate than TSI, so TSI's disagreement with it is mostly noise (fitted shrink factor for spreads = 0.00 on train and validation; totals 0.07). Against **opening** lines TSI does predict where the line moves (corr +0.16 to +0.21, positive CLV at every edge size), and totals beat the opener in validation (53.0% at 3+ pts edge, 55.0% at 5+, 59.4% at 7+), spreads do not (~50%). How edges turn into probabilities is decided with item 4 (market comparison & edges).

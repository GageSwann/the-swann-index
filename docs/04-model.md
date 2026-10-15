# 04 – The Model

The TSI rating is **points per game better than an average FBS team on a neutral field**. Every team has:
- `off_rating`: points scored above average
- `def_rating`: points allowed below average (positive = good)
- `rating = off_rating + def_rating`
- `pace`: expected possessions per game

Version 1 is **pure stats**. Manual adjustments come later as a separate layer (see the end of this doc).

## 1. Game-level inputs
For each team in each game (offense and defense sides):
- Points, drives, points per drive (PPD)
- EPA/play, success rate, explosiveness (garbage time filtered)
- Plays, drives → pace
- Site: home / away / neutral

## 2. Opponent-adjusted ratings (core)
Fit a ridge regression for each efficiency metric *m* (start with PPD and EPA/play):

```
m(offense i vs defense j) = μ + O_i − D_j + h · HFA + ε
```

- One row per team per game (each game produces two rows)
- `O_i` = offensive strength, `D_j` = defensive strength, `h` = +1 home / −1 away / 0 neutral
- Ridge penalty λ tuned in backtest; it shrinks small samples toward average
- Recency weighting: optional exponential decay (half-life tuned, e.g. 6–10 games)

**Combining metrics:** PPD-based and EPA-based ratings are each converted to points per game (× expected drives), then blended:
```
off_rating = w · off_ppd + (1 − w) · off_epa_scaled
```
Weight `w` is fit in backtest. EPA is usually more predictive early in the season, while points matter more as samples grow, so `w` may vary by week.

## 3. Preseason prior
Early-season data is noisy, so each team starts from a prior:
```
prior = a · last_season_final_rating + b · returning_production + c · talent_composite + d
```
Coefficients are fit by regression on past seasons (prior vs. end-of-season rating). The prior regresses toward the mean.

**Blending through the season** (Bayesian-style shrinkage):
```
rating_week = (k · prior + n · observed) / (k + n)
```
`n` = games played and `k` = prior weight in games (tuned, likely 3–6). By midseason the data dominates.

## 4. Home-field advantage
- v1: one global HFA fit in the regression (recent CFB ≈ 2–3 points; let the data decide)
- Later: team-specific HFA (shrunk heavily), travel distance, rest days, altitude

## 5. FCS opponents (FBS-only phase)
FBS vs. FCS games are included. In v1 all FCS teams are pooled into a single `FCS` pseudo-team with its own rating, so those games inform FBS ratings without needing full FCS ratings. Phase 10 replaces this with individual FCS team ratings.

## 6. Game prediction
```
proj_points_home = league_avg_ppg + off_home − def_away + HFA/2   (pace-adjusted)
proj_points_away = league_avg_ppg + off_away − def_home − HFA/2
margin = proj_home − proj_away
total  = proj_home + proj_away
```
Pace adjustment: scale by `(pace_home + pace_away) / (2 · league_avg_pace)`.

Turning these into probabilities, odds, and markets is covered in [05-sportsbook.md](05-sportsbook.md).

## 7. Résumé ranking (Strength of Record)
For each team: the probability that a **benchmark team** (a typical #12 team by TSI rating) would have a record at least as good against the same schedule, using TSI win probabilities game by game (Poisson-binomial). The lower that probability, the more impressive the résumé. Teams are ranked by SOR.

Strength of schedule is also shown: the average TSI rating of opponents, plus the benchmark team's expected win %.

## 8. Baseline: Elo
Build a simple margin-aware Elo as the baseline. If the main model doesn't clearly beat Elo in backtest, something is wrong.

## 9. Backtesting (walk-forward)
- Seasons 2015–2025. For every week *w*, fit using **only** games before week *w*, predict week *w*, and store the results.
- Metrics:
  - Margin MAE / RMSE vs. actual
  - Straight-up accuracy
  - ATS % vs. closing spread, O/U % vs. closing total
  - Log loss & Brier score for win probability
  - Calibration table (10 bins)
  - Comparison: closing line, SP+, Elo baseline
- Hyperparameters (λ, k, w, decay, HFA, σ) are tuned on 2015–2022 and **validated on 2023–2025**. Don't tune on the validation seasons.
- Every backtest run is saved with its params and git SHA.

## 10. Model versioning
`model_version` follows `tsi-v{major}.{minor}`. Each `model_runs` row stores the version and full params. Changing methodology bumps the version, and the report card can compare versions.

## 11. Manual adjustments (later phase)
- `adjustments` table: team, ± points, reason, active weeks
- Applied **after** the stats model: `rating_adjusted = rating_raw + Σ adjustments`
- Predictions store both raw and adjusted. The UI shows an "adjusted" badge with the reason.
- The report card tracks whether adjustments helped or hurt (raw vs. adjusted accuracy).

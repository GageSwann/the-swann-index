# 04 – The Model

The TSI rating is **points per game better than an average FBS team on a neutral field**. Every team has:
- `off_rating`: points scored above average
- `def_rating`: points allowed below average (positive = good)
- `rating = off_rating + def_rating`
- `pace`: expected possessions per game

Version 1 is **pure stats**. Manual adjustments come later as a separate layer (see the end of this doc).

### Two rating sets (decision #23)
Each model run produces two sets of ratings, stored separately:

| Basis | Uses | Feeds | Why |
|---|---|---|---|
| **`season`** | **This season's games only.** No prior, no previous seasons | **Power rankings** and Résumé rankings on the site | Rankings answer "who is best *this year*", not an all-time view. Owner requirement |
| **`predictive`** | This season's games **plus** a preseason prior that fades to zero by midseason (§3) | Game predictions, odds, edges, TSI Book | Early-season lines need more than 1–3 games of data to be accurate |

- Once the prior has faded out (around midseason), the two sets are identical.
- Past seasons are still used to **tune the method**: HFA size, how much to trust EPA vs. points, ridge λ, σ. That teaches the model *how* to rate, never *who* is good this year.
- **Provisional ranks:** a team with fewer than **4** games this season (threshold tunable) is still ranked, but shown as *provisional*.
- **Updated daily:** the nightly job (10:00 UTC) refits both sets after loading data, so a Tuesday-night game moves the rankings by Wednesday morning. Each day's run is a new `model_runs` row; published snapshots are never edited (rule 2).

## 1. Game-level inputs
From `team_game_stats` (one row per team per game = that team's **offense**; its defense is the opponent's row):
- Points (from `games`), drives and plays **for the full game**, so points per drive (PPD) is consistent
- EPA/play, rush/pass EPA, success rate, explosiveness, **garbage time excluded**
- Plays and drives → pace
- Site: home / away / neutral (`games.neutral_site`)

**Data realities (from Phase 1, see `tsi check`):**
- 47 FBS-vs-FBS games (mostly 2014–16) have **no advanced stats**. Use them in the PPD/points fit and skip them in the EPA fit.
- 2014 has no talent data (247 composite starts 2015). 2014 is only used for end-of-season ratings that feed the 2015 prior.
- Some FBS team-seasons lack returning production (teams new to FBS; 2021 ODU/UConn). The prior needs a fallback (§3).
- **2020 (COVID) is treated like any other season** (decision #26). FBS teams played 0–13 games (avg 8.6); a few programs didn't play.

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

## 3. Preseason prior (`predictive` ratings only)
The prior is used **only** for the `predictive` set. Rankings never see it.
```
prior = a · last_season_final_rating + b · returning_production + c · talent_composite + d
```
Coefficients are fit by regression on past seasons (prior vs. end-of-season rating). The prior regresses toward the mean.

**Fallbacks for missing inputs:** with no returning production (e.g. a team new to FBS), drop that term and refit on the remaining inputs. With no previous FBS rating, use the pooled-FCS rating from last season plus talent.

**Fading to zero:** the prior's weight shrinks with games played and reaches **zero by a cutoff** (tuned, around week 6–8). After that, `predictive` = `season`.
```
prior_weight(n) = max(0, k · (1 − n / n_cutoff))      # n = games played
rating = (prior_weight · prior + n · observed) / (prior_weight + n)
```
`k` (starting weight in games) and `n_cutoff` are tuned in backtest. At `n = 0` the predictive rating is the prior; at `n ≥ n_cutoff` it's pure this-season data.

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
**Question it answers:** "How hard would it be for a good team to match this record against this schedule?"

For each team: the probability that a **benchmark team** would have a record at least as good against the same schedule, using TSI win probabilities game by game (Poisson-binomial). The lower that probability, the more impressive the résumé. Teams are ranked by SOR.

- **Benchmark = a typical #12 team** (decision #24): the rating of the team ranked 12th in the current `season` ratings, roughly a playoff-bubble team. Beating strong teams earns the most credit; going unbeaten against weak teams earns less, because a #12 team would often do the same.
- **Dynamic strength of schedule** (owner requirement): every daily run re-evaluates **all past games using each opponent's *current* `season` rating**, not their rating on the day the game was played. Beat a 6–0 #8 team that finishes 6–6, and the win is worth less by season's end, because that opponent's current rating has dropped.
- **Look-ahead note:** this is intentional. Résumé is a *retrospective* measure of results, not a prediction, so rule 1 (no look-ahead) doesn't apply to it. Predictions, the Book, and backtests still only use pre-kickoff data.
- **Later (v2 ideas):** weight wins by margin/game control, a "best wins / worst losses" list on team pages, home/road context.

Strength of schedule is also shown: the average current `season` rating of opponents, plus the benchmark team's expected win % against the schedule.

## 8. Baseline: Elo
Build a simple margin-aware Elo as the baseline. If the main model doesn't clearly beat Elo in backtest, something is wrong.

## 9. Backtesting (walk-forward)
- Seasons 2015–2025 (2020 included as normal). For every week *w*, fit using **only** games before week *w*, predict week *w*, and store the results.
- Backtest predictions use the `predictive` set; also report how the `season`-only set would have predicted, to measure what the prior is worth.
- Rows are written as `model_runs.kind = 'backtest'` (their predictions can be deleted and re-run; live ones can't).
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

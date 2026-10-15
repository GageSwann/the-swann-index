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
- 47 FBS-vs-FBS games (mostly 2014–16) have **no advanced stats**, so no drive counts either. v1 excludes them from both fits. A later version could add a points-only row with league-average drives.
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
- Ridge penalty λ tuned in backtest; it shrinks small samples toward average. Targets are standardized, so one λ works for both metrics. Rows are weighted by drives (PPD) or plays (EPA). λ=2 (preliminary): with λ=25, a 13-game team kept only about a third of its signal
- Non-FBS opponents are pooled into one pseudo-team; games between two non-FBS teams are dropped
- Ratings are centered so the average FBS team = 0 (margins are unaffected)
- Recency weighting: optional exponential decay (half-life tuned, e.g. 6–10 games)

**Combining metrics:** PPD-based and EPA-based ratings are each converted to points per game (× expected drives), then blended:
```
off_rating = w · off_ppd + (1 − w) · off_epa_scaled
```
Weight `w` is fit in backtest (preliminary `w` = 0.75; 0.75 and 1.0 tie on train). EPA is usually more predictive early in the season, while points matter more as samples grow, so `w` may vary by week.

**First walk-forward results** (`tsi model ratings`; `season` set = this season only; FBS-vs-FBS with a closing line):

| Validation 2023–25 | Games | TSI MAE | Elo MAE | Vegas MAE | TSI SU% |
|---|---|---|---|---|---|
| All | 2,398 | 13.51 | 13.15 | 12.00 | 69.0 |
| Both teams 4+ games | 1,728 | **12.72** | 12.94 | 12.06 | 69.7 |
| Provisional (<4 games) | 670 | 15.55 | 13.72 | 11.86 | 67.0 |

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

**Implementation** (`model/prior.py`, `model/blend.py`, `services/prior_setup.py`):
- Offense and defense priors are fit separately. Target: that season's final `season` rating. Coefficients are fit on 2015–2022 target seasons only (validation stays out-of-sample; train seasons are in-sample for these few coefficients).
- **Missing inputs:** a separate model for every subset of {last FBS rating, talent, returning production}; each team uses the largest subset it has. A team that was FCS last year has no "last FBS rating".
- The non-FBS pooled team keeps its season fit. HFA blends the same way using average games played; the prior HFA is the train-season average (~2.8 pts).
- **Tuned for maximum accuracy (#33, owner):** `k` = 6, `n_cutoff` = 14 (train MAE plateaus at 14–16 games; never fading is slightly worse). Rankings never use the prior, so this only affects predictions.
- **Win probability:** σ is chosen to minimize log loss on train (#34): σ ≈ 12.7, not the raw residual SD (~18, inflated by blowouts). Calibration bins (validation): +1.1 / −1.2 / −3.3 / +1.4 / −0.3 pts.

| Validation 2023–25 (FBS-vs-FBS) | Games | `season` | **`predictive`** | Elo | Vegas |
|---|---|---|---|---|---|
| All | 2,398 | 13.51 | **12.84** | 13.15 | 12.00 |
| Both teams 4+ games | 1,728 | 12.72 | **12.50** | 12.94 | 12.06 |
| Provisional (<4) | 670 | 15.55 | **13.74** | 13.72 | 11.86 |
| Straight-up % | | | **71.1** | 70.5 | 72.7 |

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
A simple margin-aware Elo (`model/elo.py`) is the baseline. If the main model doesn't clearly beat Elo in backtest, something is wrong.

- Every team carries one rating across seasons. New teams start at their division mean (FBS 1500, FCS 1300, II 1100, III/other 1000). Between seasons, ratings keep 90% of their distance from the mean.
- **Tuned on 2015–2022** (grid over K, HFA, carryover): K=45, HFA=55 Elo points. Points per Elo is fit on train seasons (~22 Elo ≈ 1 point).
- **The bar to beat** (FBS-vs-FBS games with a closing line; `tsi model elo`):

| Period | Games | Elo MAE | Vegas MAE | Elo SU% | Vegas SU% | Elo Brier |
|---|---|---|---|---|---|---|
| Train 2015–22 | 5,927 | 13.45 | 12.45 | 71.0 | 74.3 | 0.189 |
| **Validate 2023–25** | 2,398 | **13.15** | **12.00** | **70.5** | **72.7** | 0.191 |

Elo is about 1.15 points worse than the closing line. The doc 01 target for TSI is within ~1 point of the closing line, so TSI must beat Elo by a real margin.

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

## 12. Improvement backlog (brainstorm, 2026-10-14)
Goal: the most accurate predictions and the most defensible rankings. **Rules for every idea:**
- Test in the walk-forward harness, one idea at a time.
- Adopt only if **train** MAE improves and validation doesn't get worse.
- Record the result in `decisions.md`.
- **Never use market lines as model inputs.** They're the benchmark; using them would make every "edge" circular.

**Tier 1: likely gains, data already loaded**
| # | Idea | Why it might help |
|---|---|---|
| B1 | **Learned blend ("stacking")**: fit margin = Σ βₖ·(component difference) on train, with components PPD, EPA, success rate, rush/pass EPA, prior, Elo, and weights that can shift with games played | Replaces hand-picked weights (w = 0.75, one prior curve) with weights the data chooses; ensembles usually beat their parts |
| B2 | ~~Recency weighting~~ **tested, rejected (#35)**: half-life 30/60/120 days → train −0.01 to −0.02, validation +0.06 to 0.00 | Noise-level; not worth fitting twice |
| B3 | **Week-varying PPD/EPA weight** | EPA stabilizes faster than points per drive, so it should matter more early |
| B4 | **Ridge toward the prior** (shrink toward the preseason estimate instead of toward 0) | One principled fit instead of fit-then-blend; avoids shrinking twice early in the season |
| B5 | **Success rate as a third opponent-adjusted metric** | Success rate is very stable and predictive; we already store it |
| B6 | **Context-dependent σ** (wider for mismatches and high-pace games) | Better win probabilities and calibration, which matter for the book |
| B7 | **Split the pooled non-FBS team** into FCS and D-II/III | One pooled team mixes NDSU with D-III schools |

**Tier 2: needs new data (CFBD calls)**
| # | Idea | Data |
|---|---|---|
| B8 | Richer prior: QB/passing returning production (already in the cached returning response), two seasons of ratings, recruiting classes, transfer portal, coaching changes | `/recruiting/teams`, `/player/portal`, `/coaches` |
| B9 | Situational home field: travel distance, altitude, dome, rest days | venues (loaded) + schedule |
| B10 | QB injuries/changes | manual adjustments layer (Phase 9) |

**Tier 3: ranking quality**
| # | Idea |
|---|---|
| B11 | Rating **uncertainty** (ridge standard errors): show ± bands; base "provisional" on uncertainty instead of a fixed 4 games |
| B12 | Résumé with dynamic SOS (planned, Phase 2) |
| B13 | Optional "form" view (recency-weighted `season` rating) alongside the full-season Power rating |

**SP+ comparison caveat:** CFBD's historical SP+ (`/ratings/sp`) is end-of-season only. Comparing our week-by-week predictions against final SP+ would give SP+ look-ahead, so it isn't a fair *prediction* benchmark. It can still serve as a sanity check on final ratings (rank correlation).

"""Walk-forward evaluation of `season` ratings (this season's games only), vs. Elo and Vegas.

Mirrors the daily job: games kicking off in [D 10:00 UTC, D+1 10:00 UTC) are
predicted from ratings fit on this season's games that kicked off before
D 10:00 UTC. Win-probability spread (sigma) is fit on TRAIN seasons only.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy.orm import Session

from tsi.backtest.evaluate import ScoredGame, Summary, summarize
from tsi.db.queries.market import closing_spreads
from tsi.db.queries.results import GameResult, completed_games
from tsi.db.queries.stats import OffenseRow, offense_rows
from tsi.model.elo import EloParams
from tsi.model.ratings.fit import RatingParams, fit_ratings, predicted_margin
from tsi.model.ratings.probability import residual_sigma, win_prob
from tsi.services.elo_report import FIRST_SCORED_SEASON, TRAIN, VALIDATE, elo_picks, is_scored

REFIT_HOUR = 10  # UTC, same as the nightly job
ESTABLISHED_GAMES = 4  # provisional threshold (doc 04)


@dataclass(frozen=True)
class _Pick:
    game: GameResult
    margin: float
    established: bool


@dataclass(frozen=True)
class ComparisonRow:
    tsi: Summary
    elo: Summary


@dataclass(frozen=True)
class RatingsReport:
    params: RatingParams
    sigma: float
    rows: list[ComparisonRow]


def refit_day(kickoff: datetime) -> date:
    """The daily run whose ratings a game is predicted from."""
    return (kickoff - timedelta(hours=REFIT_HOUR)).date()


def run_ratings_report(
    session: Session, through_season: int, params: RatingParams | None = None
) -> RatingsReport:
    params = params or RatingParams()
    games = completed_games(session, through_season)
    closing = closing_spreads(session, through_season)
    rows = offense_rows(session, FIRST_SCORED_SEASON, through_season)
    _, elo = elo_picks(games, closing, EloParams())

    picks = _walk_forward(games, rows, closing, params)
    train = [p for p in picks if TRAIN[0] <= p.game.season <= TRAIN[1]]
    sigma = residual_sigma([p.margin for p in train], [p.game.margin for p in train])

    def scored(model: str, subset: list[_Pick]) -> list[ScoredGame]:
        out = []
        for p in subset:
            margin = p.margin if model == "tsi" else elo[p.game.id].margin
            prob = win_prob(margin, sigma) if model == "tsi" else elo[p.game.id].home_win_prob
            out.append(ScoredGame(p.game.season, margin, prob, p.game.margin, -closing[p.game.id]))
        return out

    def row(label: str, subset: list[_Pick]) -> ComparisonRow:
        return ComparisonRow(
            summarize(label, scored("tsi", subset)), summarize(label, scored("elo", subset))
        )

    def seasons(first: int, last: int) -> list[_Pick]:
        return [p for p in picks if first <= p.game.season <= last]

    validate = seasons(*VALIDATE)
    report_rows = [row(str(s), seasons(s, s)) for s in sorted({p.game.season for p in picks})]
    report_rows += [
        row(f"Train {TRAIN[0]}-{TRAIN[1]}", seasons(*TRAIN)),
        row(f"Validate {VALIDATE[0]}-{VALIDATE[1]}", validate),
        row("  both teams 4+ games", [p for p in validate if p.established]),
        row("  provisional (<4)", [p for p in validate if not p.established]),
    ]
    return RatingsReport(params, sigma, report_rows)


def _walk_forward(
    games: list[GameResult],
    rows: list[OffenseRow],
    closing: dict[int, float],
    params: RatingParams,
) -> list[_Pick]:
    rows_by_season: dict[int, list[OffenseRow]] = defaultdict(list)
    for r in rows:
        rows_by_season[r.season].append(r)
    slates: dict[tuple[int, date], list[GameResult]] = defaultdict(list)
    for g in games:
        if is_scored(g, closing) and g.start_time is not None:
            slates[(g.season, refit_day(g.start_time))].append(g)

    picks = []
    for (season, day), slate in sorted(slates.items()):
        cutoff = datetime.combine(day, time(REFIT_HOUR), tzinfo=UTC)
        known = [r for r in rows_by_season[season] if r.start_time and r.start_time < cutoff]
        ratings = fit_ratings(known, params)
        for g in slate:
            home = ratings.get(g.home_id, g.home_div)
            away = ratings.get(g.away_id, g.away_div)
            played = min(ratings.games.get(g.home_id, 0), ratings.games.get(g.away_id, 0))
            margin = predicted_margin(ratings, home, away, g.neutral)
            picks.append(_Pick(g, margin, played >= ESTABLISHED_GAMES))
    return picks

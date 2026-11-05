"""Save live ratings: one `model_runs` row (kind='live') + `team_ratings` for both bases.

Each daily run is a new model_run; earlier runs are never modified, so the site can
show movement and history (rule 2 spirit).
"""

from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from tsi.db.models import ModelRun, TeamRating
from tsi.db.queries.calendar import calendar_week
from tsi.db.upsert import upsert_rows
from tsi.model.artifact import ModelArtifact
from tsi.model.resume import BENCHMARK_RANK, FCS_BENCHMARK_RANK
from tsi.services.backtest_store import current_git_sha
from tsi.services.rate import LiveRatings


def save_live_ratings(
    session_factory: sessionmaker[Session], live: LiveRatings, artifact: ModelArtifact
) -> int:
    with session_factory.begin() as session:
        season_type, week = calendar_week(session, live.season, live.as_of)
        run = ModelRun(
            kind="live",
            season=live.season,
            week=week,
            season_type=season_type,
            run_at=live.as_of,
            model_version=artifact.version,
            params={
                "artifact_version": artifact.version,
                "fitted_seasons": list(artifact.fitted_seasons),
                "season_hfa": live.rankings.ratings.hfa,
                "predictive_hfa": live.predictive_hfa,
                "resume_benchmark": live.rankings.benchmark,
                "fcs_resume_benchmark": live.rankings.fcs_benchmark,  # #24 FCS team (#133)
                # Which ranks those are, so the site names the benchmark this run used.
                "resume_benchmark_rank": BENCHMARK_RANK,
                "fcs_resume_benchmark_rank": FCS_BENCHMARK_RANK,
                "resume_sigma": artifact.sigma_season,  # SOR win-probability spread
                # Fallback `season` ratings for opponents without a stored row, for the
                # team page's Résumé breakdown (decision #89): FCS = the pool before
                # 2022, the average FCS team since (#109); everything below FCS pooled.
                "pooled_season_ratings": {
                    "fcs": _fcs_fallback(live),
                    "lower": live.rankings.ratings.get(0, "ii", live.season).rating,
                },
            },
            git_sha=current_git_sha(),
        )
        session.add(run)
        session.flush()
        upsert_rows(session, TeamRating, _season_rows(run.id, live))
        upsert_rows(session, TeamRating, _predictive_rows(run.id, live))
        return run.id


def _season_rows(run_id: int, live: LiveRatings) -> list[dict[str, Any]]:
    return [
        {
            "run_id": run_id,
            "team_id": t.team_id,
            "basis": "season",
            "variant": "raw",
            "rating": t.rating,
            "off_rating": t.off,
            "def_rating": t.defense,
            "games_played": t.games,
            "provisional": t.provisional,
            "rank_power": t.rank_power,
            "sor": t.resume.sor,
            "sos": t.resume.sos,
            "rank_resume": t.rank_resume,
        }
        for t in [*live.rankings.teams, *live.rankings.fcs_teams]  # ranks within division
    ]


def _fcs_fallback(live: LiveRatings) -> float:
    average = live.rankings.fcs_average
    return live.rankings.ratings.get(0, "fcs", live.season).rating if average is None else average


def _predictive_rows(run_id: int, live: LiveRatings) -> list[dict[str, Any]]:
    """Predictive ratings, ranked within each division."""
    ordered = sorted(live.predictive, key=lambda t: (t.division, -t.rating.rating))
    rank: dict[int, int] = {}
    for division in {t.division for t in ordered}:
        same = [t for t in ordered if t.division == division]
        rank |= {t.team_id: i + 1 for i, t in enumerate(same)}
    return [
        {
            "run_id": run_id,
            "team_id": t.team_id,
            "basis": "predictive",
            "variant": "raw",
            "rating": t.rating.rating,
            "off_rating": t.rating.off,
            "def_rating": t.rating.defense,
            "games_played": t.games,
            "provisional": t.provisional,
            "rank_power": rank[t.team_id],
        }
        for t in ordered
    ]

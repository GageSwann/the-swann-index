"""`/playoff`: playoff odds and a projected bracket from the latest stored season sim.

Odds come from the nightly simulation (decision #100); fair futures odds are the same
chances as American odds without vig (doc 05 §7). Regular season only: None when the
latest run has no playoff odds.
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from tsi.book.odds import american_from_prob
from tsi.db.queries.runs import run_and_week_ago, run_params
from tsi.db.queries.sim import StoredSim, stored_sims
from tsi.db.queries.team_info import Record, TeamRef, records, stored_ratings, team_refs
from tsi.sim.cfp_format import FORMAT_2026, CfpFormat
from tsi.sim.projected_field import OddsRow, projected_field

LISTED = 0.01  # teams below this chance of making the field are left off the table
PRICED = (0.001, 0.999)  # fair odds only between these chances (beyond: "—")


@dataclass(frozen=True)
class FairOdds:
    """American odds without vig; None when the chance is too close to 0 or 1 to price."""

    playoff: int | None
    conference: int | None
    title: int | None


@dataclass(frozen=True)
class PlayoffTeam:
    team: TeamRef
    wins: int
    losses: int
    rank_resume: int | None  # today's Résumé rank (the committee stand-in)
    playoff_prob: float
    bye_prob: float
    seed_dist: list[float]  # P(seed = 1..field size)
    quarterfinal_prob: float
    semifinal_prob: float
    final_prob: float
    champion_prob: float
    conference_title_prob: float | None  # None: no conference title game
    fair_odds: FairOdds


@dataclass(frozen=True)
class BracketFormat:
    field_size: int
    byes: int
    first_round: list[list[int]]  # [higher seed (hosts), lower seed]
    quarterfinals: list[list[int]]  # [bye seed, first-round game index]
    semifinals: list[list[int]]  # [quarterfinal index, quarterfinal index]


@dataclass(frozen=True)
class Playoff:
    season: int
    week: int
    as_of: datetime
    sims: int | None
    format: BracketFormat
    projected: list[PlayoffTeam]  # one representative field, seed 1 first
    teams: list[PlayoffTeam]  # every FBS team with a 1%+ chance, likeliest first


def playoff(session: Session, season: int, fmt: CfpFormat = FORMAT_2026) -> Playoff | None:
    run, _ = run_and_week_ago(session, season)
    if run is None:
        return None
    sims = {t: s for t, s in stored_sims(session, run.id).items() if s.playoff_prob is not None}
    if not sims:
        return None
    refs = team_refs(session, season, sims)
    rec = records(session, season, run.run_at)
    resume_rank = {
        r.team_id: r.rank_resume
        for r in stored_ratings(session, [run.id]).get(run.id, [])
        if r.basis == "season"
    }
    rows = {t: _team(refs[t], rec.get(t, Record()), resume_rank.get(t), s) for t, s in sims.items()}
    odds_rows = [
        OddsRow(
            t,
            refs[t].slug,
            refs[t].conference,
            s.playoff_prob,
            s.conference_title_prob,
            s.seed_dist or [],
        )  # fmt: skip
        for t, s in sims.items()
    ]
    return Playoff(
        season=run.season,
        week=run.week,
        as_of=run.run_at,
        sims=run_params(session, run.id).get("sim", {}).get("sims"),
        format=BracketFormat(
            field_size=fmt.field_size,
            byes=fmt.byes,
            first_round=[list(g) for g in fmt.first_round],
            quarterfinals=[list(g) for g in fmt.quarterfinals],
            semifinals=[list(g) for g in fmt.semifinals],
        ),
        projected=[rows[r.team_id] for r in projected_field(odds_rows, fmt)],
        teams=sorted(
            (row for row in rows.values() if row.playoff_prob >= LISTED),
            key=lambda r: (-r.playoff_prob, -r.champion_prob, r.team.school),
        ),
    )


def _team(team: TeamRef, rec: Record, rank: int | None, s: StoredSim) -> PlayoffTeam:
    return PlayoffTeam(
        team=team,
        wins=rec.wins,
        losses=rec.losses,
        rank_resume=rank,
        playoff_prob=s.playoff_prob or 0.0,
        bye_prob=s.bye_prob or 0.0,
        seed_dist=s.seed_dist or [],
        quarterfinal_prob=s.quarterfinal_prob or 0.0,
        semifinal_prob=s.semifinal_prob or 0.0,
        final_prob=s.final_prob or 0.0,
        champion_prob=s.champion_prob or 0.0,
        conference_title_prob=s.conference_title_prob,
        fair_odds=FairOdds(
            playoff=_fair(s.playoff_prob),
            conference=_fair(s.conference_title_prob),
            title=_fair(s.champion_prob),
        ),
    )


def _fair(p: float | None) -> int | None:
    if p is None or not PRICED[0] <= p <= PRICED[1]:
        return None
    return american_from_prob(p)

"""A game as the site's game cards show it: the home page's games of the week (#141, #188,
#190) and a team page's next game (#199). One builder, so both cards carry the same data."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from tsi.db.queries.team_info import Record, TeamRef, records
from tsi.services.read.fair_markets import FairTwoWay
from tsi.services.read.games import GameSummary, tsi_markets


@dataclass(frozen=True)
class GameLines:
    """TSI's spread and total as the card shows them, with TSI's fair odds for both sides at
    that line (#188): the same pricing as the game center."""

    spread: FairTwoWay  # home view: first = home covers, second = away covers
    total: FairTwoWay  # first = over, second = under


@dataclass(frozen=True)
class GameCard:
    """A team page's next game (#199): the game with TSI's prediction and the market, as on
    the week board, both teams' records and conference records, and TSI's lines."""

    game: GameSummary
    home_record: Record
    away_record: Record
    home_conf_record: Record | None  # None for independents (no conference standings)
    away_conf_record: Record | None
    lines: GameLines | None  # None without a prediction


@dataclass(frozen=True)
class Records:
    """Overall and conference records of a set of teams, as of one moment."""

    overall: dict[int, Record]
    conference: dict[int, Record]

    def overall_of(self, team: TeamRef) -> Record:
        return self.overall.get(team.id, Record())

    def conference_of(self, team: TeamRef) -> Record | None:
        """A conference team's conference record (0-0 before its first conference game);
        None for an independent, which has no conference standings (#190)."""
        if not team.conference or "independent" in team.conference.lower():
            return None
        return self.conference.get(team.id, Record())


def team_records(
    session: Session, season: int, as_of: datetime, team_ids: Iterable[int]
) -> Records:
    ids = set(team_ids)
    return Records(
        overall=records(session, season, as_of, ids),
        conference=records(session, season, as_of, ids, conference_only=True),
    )


def game_lines(game: GameSummary) -> GameLines | None:
    if game.prediction is None:
        return None
    markets = tsi_markets(game.prediction)
    return GameLines(spread=markets.spread, total=markets.total)


def game_card(game: GameSummary, recs: Records) -> GameCard:
    return GameCard(
        game=game,
        home_record=recs.overall_of(game.home),
        away_record=recs.overall_of(game.away),
        home_conf_record=recs.conference_of(game.home),
        away_conf_record=recs.conference_of(game.away),
        lines=game_lines(game),
    )

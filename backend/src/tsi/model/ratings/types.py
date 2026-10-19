"""Rating data types shared by the fit, blend, prior, and stacking modules."""

from dataclasses import dataclass

from tsi.model.ratings.design import rated_id


@dataclass(frozen=True)
class TeamRating:
    off: float  # points scored above an average FBS team
    defense: float  # points allowed below average (positive = good)

    @property
    def rating(self) -> float:
        return self.off + self.defense


AVERAGE_TEAM = TeamRating(0.0, 0.0)


@dataclass(frozen=True)
class RatingSet:
    teams: dict[int, TeamRating]  # FBS team id (or pool id < 0) -> rating
    hfa: float  # home-field advantage in points of margin
    games: dict[int, int]  # FBS team id -> games counted

    def get(self, team_id: int, division: str) -> TeamRating:
        """Unseen teams are rated as average; non-FBS teams share the pooled rating."""
        return self.teams.get(rated_id(team_id, division), AVERAGE_TEAM)


def matchup_margin(home: TeamRating, away: TeamRating) -> float:
    """Home-view margin before home field: (home off - away def) - (away off - home def)."""
    return (home.off - away.defense) - (away.off - home.defense)

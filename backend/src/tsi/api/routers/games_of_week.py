from fastapi import APIRouter

from tsi.api.deps import NowDep, SessionsDep, read
from tsi.services.read.games_of_week import GamesOfWeek, games_of_week

router = APIRouter(tags=["games"])


@router.get("/games-of-week", response_model=GamesOfWeek)
async def get_games_of_week(sessions: SessionsDep, now: NowDep) -> GamesOfWeek:
    """This poll week's FBS and FCS games of the week, for Power and Résumé (picked with
    Sunday's rankings and held all week); empty before the first pick."""
    return await read(sessions, lambda s: games_of_week(s, now))

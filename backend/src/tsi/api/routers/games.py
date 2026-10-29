from typing import Literal

from fastapi import APIRouter, HTTPException

from tsi.api.deps import NowDep, SessionsDep, read
from tsi.services.read.games import GameCenter, WeekBoard, game_center, week_board

router = APIRouter(tags=["games"])


@router.get("/weeks/{season}/{week}/games", response_model=WeekBoard)
async def get_week_games(
    season: int,
    week: int,
    sessions: SessionsDep,
    now: NowDep,
    season_type: Literal["regular", "postseason"] = "regular",
) -> WeekBoard:
    """Matchup board: every game with an FBS team, TSI's prediction and the market."""
    return await read(sessions, lambda s: week_board(s, season, week, season_type, now))


@router.get("/games/{game_id}", response_model=GameCenter)
async def get_game(
    game_id: int,
    sessions: SessionsDep,
    now: NowDep,
) -> GameCenter:
    """Game center: prediction, full odds board, market comparison, snapshot history, result."""
    center = await read(sessions, lambda s: game_center(s, game_id, now))
    if center is None:
        raise HTTPException(404, f"Unknown game {game_id}.")
    return center

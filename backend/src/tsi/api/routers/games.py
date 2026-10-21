from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from tsi.api.deps import get_now, get_session
from tsi.services.read.games import GameCenter, WeekBoard, game_center, week_board

router = APIRouter(tags=["games"])


@router.get("/weeks/{season}/{week}/games", response_model=WeekBoard)
def get_week_games(
    season: int,
    week: int,
    session: Annotated[Session, Depends(get_session)],
    now: Annotated[datetime, Depends(get_now)],
    season_type: Literal["regular", "postseason"] = "regular",
) -> WeekBoard:
    """Matchup board: every game with an FBS team, TSI's prediction and the market."""
    return week_board(session, season, week, season_type, now)


@router.get("/games/{game_id}", response_model=GameCenter)
def get_game(
    game_id: int,
    session: Annotated[Session, Depends(get_session)],
    now: Annotated[datetime, Depends(get_now)],
) -> GameCenter:
    """Game center: prediction, full odds board, market comparison, snapshot history, result."""
    center = game_center(session, game_id, now)
    if center is None:
        raise HTTPException(404, f"Unknown game {game_id}.")
    return center

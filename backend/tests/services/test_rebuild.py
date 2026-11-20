from datetime import UTC, date, datetime
from types import SimpleNamespace

from tsi.services.rebuild import RebuiltDay, cutoff, is_poll_day


def test_cutoff_is_the_nightly_time_in_utc():
    assert cutoff(date(2026, 11, 15)) == datetime(2026, 11, 15, 11, 0, tzinfo=UTC)


def test_poll_day_is_sunday_eastern():
    assert is_poll_day(cutoff(date(2026, 11, 15)))  # Sunday
    assert not is_poll_day(cutoff(date(2026, 11, 16)))  # Monday
    assert not is_poll_day(cutoff(date(2026, 11, 14)))  # Saturday
    # 03:00 UTC Monday is still Sunday evening in the East.
    assert is_poll_day(datetime(2026, 11, 16, 3, 0, tzinfo=UTC))


def _forecast(start: datetime):
    return SimpleNamespace(game=SimpleNamespace(start_time=start))


def test_final_forecasts_keep_games_before_the_next_cutoff():
    as_of = cutoff(date(2026, 11, 14))
    board = [
        _forecast(datetime(2026, 11, 14, 17, 0, tzinfo=UTC)),  # today
        _forecast(datetime(2026, 11, 15, 11, 0, tzinfo=UTC)),  # at the next cutoff: kept
        _forecast(datetime(2026, 11, 15, 11, 1, tzinfo=UTC)),  # next day's run forecasts it
        _forecast(datetime(2026, 11, 21, 19, 0, tzinfo=UTC)),
    ]
    day = RebuiltDay(as_of=as_of, ratings=None, board=board, sim=None, games_of_week=[])
    assert day.final_forecasts() == board[:2]

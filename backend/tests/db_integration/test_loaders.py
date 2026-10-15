"""Loaders end to end against a real (throwaway-schema) Postgres, with CFBD faked."""

import copy
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from tsi.db.models import Game, MarketLine, Prior, Team, TeamGameStats, TeamSeason, Venue
from tsi.ingest.loaders.games import load_games
from tsi.ingest.loaders.lines import load_lines
from tsi.ingest.loaders.priors import load_prior_inputs
from tsi.ingest.loaders.teams import load_teams
from tsi.ingest.loaders.venues import load_venues
from tsi.quality.runner import run_checks
from tsi.services.season import run_season

COLORADO, COLORADO_GAME = 38, 401634206
KICKOFF = datetime(2024, 8, 30, tzinfo=UTC)


def count(sessions, model) -> int:
    with sessions() as s:
        return s.scalar(select(func.count()).select_from(model))


def test_run_season_loads_everything_and_is_idempotent(sessions, fake_cfbd) -> None:
    first = run_season(fake_cfbd, sessions, 2024)
    snapshot = {m: count(sessions, m) for m in (Venue, Team, TeamSeason, Game, TeamGameStats)}
    second = run_season(fake_cfbd, sessions, 2024)

    assert first.games == 4 and first.stat_rows == 2
    assert first.new_line_snapshots == 3  # Colorado game x 3 providers; others not loaded
    assert second.new_line_snapshots == 0
    assert {m: count(sessions, m) for m in snapshot} == snapshot  # nothing duplicated
    with sessions() as s:
        stats = s.get(TeamGameStats, (COLORADO_GAME, COLORADO))
        assert (stats.points, stats.drives) == (31, 9)
        assert all(line.is_closing for line in s.scalars(select(MarketLine)))


def test_quality_checks_pass_on_loaded_data(sessions, fake_cfbd) -> None:
    run_season(fake_cfbd, sessions, 2024)

    with sessions() as s:
        failures = [r.check.name for r in run_checks(s) if r.failed]

    assert failures == []


def test_older_season_never_overwrites_team_identity(sessions, fake_cfbd, cfbd_fixture) -> None:
    load_venues(fake_cfbd, sessions)
    load_teams(fake_cfbd, sessions, 2024)
    old = copy.deepcopy(cfbd_fixture("teams_2024_sample"))
    for team in old:
        team["color"] = "#000001"
    fake_cfbd.responses[("/teams", frozenset({("year", 2014)}))] = old

    result = load_teams(fake_cfbd, sessions, 2014)

    assert result.identity_updated is False
    with sessions() as s:
        assert s.get(Team, COLORADO).color == "#cfb87c"
        assert s.get(TeamSeason, (COLORADO, 2014)) is not None


def test_games_add_placeholder_teams_once(sessions, fake_cfbd) -> None:
    load_venues(fake_cfbd, sessions)
    load_teams(fake_cfbd, sessions, 2024)

    first = load_games(fake_cfbd, sessions, 2024)
    second = load_games(fake_cfbd, sessions, 2024)

    assert first.placeholder_teams > 0
    assert second.placeholder_teams == 0
    with sessions() as s:
        assert s.scalar(select(func.count()).select_from(Game)) == 4


def test_line_history_change_only_then_closing(sessions, fake_cfbd) -> None:
    run_season(fake_cfbd, sessions, 2024)  # baseline
    with sessions.begin() as s:
        s.execute(MarketLine.__table__.delete())

    fake_cfbd.fetched_at = KICKOFF - timedelta(days=2)
    opened = load_lines(fake_cfbd, sessions, 2024)
    fake_cfbd.fetched_at = KICKOFF - timedelta(days=1)
    same = load_lines(fake_cfbd, sessions, 2024)
    moved_raw = copy.deepcopy(fake_cfbd.responses[("/lines", frozenset({("year", 2024)}))])
    moved_raw[0]["lines"][0]["spread"] -= 1
    fake_cfbd.responses[("/lines", frozenset({("year", 2024)}))] = moved_raw
    fake_cfbd.fetched_at = KICKOFF - timedelta(hours=2)
    moved = load_lines(fake_cfbd, sessions, 2024)
    fake_cfbd.fetched_at = KICKOFF + timedelta(hours=6)
    closed = load_lines(fake_cfbd, sessions, 2024)

    assert (opened.inserted, same.inserted, same.unchanged) == (3, 0, 3)
    assert (moved.inserted, moved.unchanged) == (1, 2)
    assert (closed.inserted, closed.marked_closing) == (0, 3)
    with sessions() as s:
        assert s.scalar(select(func.count()).select_from(MarketLine)) == 4
        assert s.scalar(select(func.count()).where(MarketLine.is_closing)) == 3


def test_priors_inputs_fill_their_own_columns(sessions, fake_cfbd) -> None:
    load_venues(fake_cfbd, sessions)
    load_teams(fake_cfbd, sessions, 2024)

    result = load_prior_inputs(fake_cfbd, sessions, 2024)

    assert (result.talent, result.returning, result.unmatched) == (1, 1, 2)  # Alabama unknown
    with sessions() as s:
        prior = s.get(Prior, (2024, COLORADO))
        assert (prior.talent, prior.returning_ppa) == (749.16, 0.665)

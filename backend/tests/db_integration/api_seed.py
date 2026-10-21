"""A tiny 2026 season for API tests. The clock is pinned at NOW.

Teams: Alpha(1), Bravo(2), Charlie(3), Delta(4) are FBS; Echo(5), Foxtrot(6) are FCS.
Week 1 (final): Alpha 30-20 Bravo; Charlie 21-24 Delta.
Week 2: Alpha-Charlie kicked off last night (in progress: a pre-kickoff snapshot plus
one published after kickoff that must never count); Bravo-Delta is upcoming with two
books' lines and an open pick; Echo-Foxtrot is FCS-only (left off the board).
Ratings: a week-1 run and a week-2 run. Two saved backtests: an old version without
report tables, and the current one with them.
"""

from datetime import UTC, datetime, timedelta

from tsi.db.models import (
    CalendarWeek,
    Game,
    MarketLine,
    ModelRun,
    Pick,
    Prediction,
    Team,
    TeamRating,
    TeamSeason,
)

NOW = datetime(2026, 10, 21, 12, 0, tzinfo=UTC)
SEASON = 2026
FBS = {1: "Alpha", 2: "Bravo", 3: "Charlie", 4: "Delta"}
FCS = {5: "Echo", 6: "Foxtrot"}
WEEK1_RUN_AT = datetime(2026, 10, 14, 10, 0, tzinfo=UTC)

_ACCURACY = {
    "games": 700,
    "season_mae": 13.4,
    "predictive_mae": 12.4,
    "elo_mae": 13.1,
    "vegas_mae": 12.0,
    "predictive_su": 0.717,
    "elo_su": 0.70,
    "vegas_su": 0.73,
    "predictive_brier": 0.18,
}
# The shape `services/report_tables.py` saves (one row per table).
BACKTEST_REPORT = {
    "by_season": [{"season": 2024, **_ACCURACY}],
    "periods": [{"period": "Validate 2023–25", **_ACCURACY}],
    "calibration": [{"bin": "60–70%", "games": 120, "predicted": 0.65, "observed": 0.66}],
    "ats": [
        {"min_edge": 3, "bets": 200, "wins": 100, "losses": 98, "pushes": 2, "win_rate": 0.505}
    ],
    "totals_accuracy": [
        {
            "period": "Validate 2023–25",
            "games": 700,
            "tsi_mae": 12.87,
            "vegas_mae": 12.68,
            "bias": 0.1,
            "ou_vs_close": 0.51,
        }
    ],
    "book_record": [
        {
            "period": "Validate 2023–25",
            "market": "all",
            "tier": 0,
            "bets": 181,
            "wins": 104,
            "losses": 75,
            "pushes": 2,
            "win_rate": 0.581,
            "units": 19.6,
            "roi": 0.108,
            "kelly_units": 21.0,
            "clv": 0.93,
            "beat_close": 0.6,
        }
    ],
    "book_calibration": [
        {"market": "total", "bin": "50–60%", "games": 300, "predicted": 0.54, "observed": 0.55}
    ],
    "book_units": [{"date": "2023-09-02", "season": 2023, "units": 0.9, "kelly_units": 1.2}],
}
WEEK2_RUN_AT = datetime(2026, 10, 21, 10, 0, tzinfo=UTC)
LIVE_KICKOFF = datetime(2026, 10, 21, 0, 0, tzinfo=UTC)  # Alpha-Charlie, in progress
UPCOMING_KICKOFF = datetime(2026, 10, 24, 19, 0, tzinfo=UTC)  # Bravo-Delta
# (team, rating, off, def, rank_power, rank_resume, sor, predictive rating)
WEEK2_RATINGS = [
    (1, 12.0, 7.0, 5.0, 1, 1, 0.20, 14.0),
    (4, 6.0, 3.0, 3.0, 2, 2, 0.35, 5.0),
    (3, -4.0, -1.0, -3.0, 3, 4, 0.80, -2.0),
    (2, -8.0, -5.0, -3.0, 4, 3, 0.70, -9.0),
]


def seed(session) -> None:
    session.add_all(
        [Team(id=t, school=n, slug=n.lower(), color="#123456") for t, n in (FBS | FCS).items()]
    )
    session.flush()
    session.add_all(
        [TeamSeason(team_id=t, season=SEASON, conference="Test", division="fbs") for t in FBS]
        + [TeamSeason(team_id=t, season=SEASON, conference="FCS", division="fcs") for t in FCS]
    )
    session.add_all(
        [
            CalendarWeek(
                season=SEASON,
                season_type="regular",
                week=1,
                start_date=datetime(2026, 10, 12, 7, tzinfo=UTC),
                end_date=datetime(2026, 10, 19, 6, 59, tzinfo=UTC),
            ),
            CalendarWeek(
                season=SEASON,
                season_type="regular",
                week=2,
                start_date=datetime(2026, 10, 19, 7, tzinfo=UTC),
                end_date=datetime(2026, 10, 26, 6, 59, tzinfo=UTC),
            ),
        ]
    )
    session.add_all(
        [
            _game(101, 1, datetime(2026, 10, 17, 19, tzinfo=UTC), 1, 2, 30, 20),
            _game(102, 1, datetime(2026, 10, 17, 23, tzinfo=UTC), 3, 4, 21, 24),
            _game(201, 2, LIVE_KICKOFF, 1, 3),
            _game(202, 2, UPCOMING_KICKOFF, 2, 4),
            _game(203, 2, UPCOMING_KICKOFF, 5, 6),
        ]
    )
    session.flush()
    _lines(session)
    _runs(session)
    session.flush()


def _game(gid, week, kickoff, home, away, hp=None, ap=None) -> Game:
    done = hp is not None
    return Game(
        id=gid,
        season=SEASON,
        week=week,
        season_type="regular",
        start_time=kickoff,
        home_id=home,
        away_id=away,
        home_points=hp,
        away_points=ap,
        completed=done,
    )


def _lines(session) -> None:
    def line(gid, provider, spread, total, at, closing=False, home_ml=None, away_ml=None):
        session.add(
            MarketLine(
                game_id=gid,
                provider=provider,
                spread=spread,
                total=total,
                home_ml=home_ml,
                away_ml=away_ml,
                fetched_at=at,
                is_closing=closing,
            )
        )

    line(101, "DraftKings", -7.0, 47.0, datetime(2026, 10, 17, 19, tzinfo=UTC), closing=True)
    line(202, "DraftKings", -3.0, 50.0, NOW - timedelta(days=1), home_ml=-150, away_ml=130)
    line(202, "Bovada", -3.5, 51.0, NOW - timedelta(days=1), home_ml=-160, away_ml=140)
    line(202, "consensus", -9.0, 60.0, NOW - timedelta(days=1))  # aggregator: ignored


def _runs(session) -> None:
    week1 = ModelRun(
        kind="live",
        season=SEASON,
        week=1,
        season_type="regular",
        run_at=WEEK1_RUN_AT,
        model_version="tsi-test",
        params={},
    )
    week2 = ModelRun(
        kind="live",
        season=SEASON,
        week=2,
        season_type="regular",
        run_at=WEEK2_RUN_AT,
        model_version="tsi-test",
        params={},
    )
    publish = ModelRun(
        kind="live",
        season=SEASON,
        week=2,
        season_type="regular",
        run_at=WEEK2_RUN_AT,
        model_version="tsi-test",
        params={"job": "publish"},
    )
    backtest = ModelRun(
        kind="backtest",
        season=SEASON,
        week=0,
        season_type="regular",
        run_at=WEEK1_RUN_AT,
        model_version="tsi-test",
        params={
            "metrics": {"validate_mae": 12.4, "validate_market_mae": 12.0},
            "report": BACKTEST_REPORT,
        },
    )
    old_backtest = ModelRun(
        kind="backtest",
        season=SEASON,
        week=0,
        season_type="regular",
        run_at=WEEK1_RUN_AT - timedelta(days=5),
        model_version="tsi-old",
        params={"metrics": {"validate_mae": 12.9}},
    )
    session.add_all([week1, week2, publish, backtest, old_backtest])
    session.flush()
    for t, rating, off, de, rp, rr, sor, pred in WEEK2_RATINGS:
        session.add_all(
            [
                _rating(week2.id, t, "season", rating, off, de, 1, rp, rr, sor),
                _rating(week2.id, t, "predictive", pred, pred / 2, pred / 2, 1, None, None, None),
                _rating(week1.id, t, "season", rating - 1, off, de, 0, rp, rr, sor),
            ]
        )
    snap_101 = _snapshot(publish.id, 101, datetime(2026, 10, 17, 10, tzinfo=UTC), -6.0, 52.0)
    snap_201_pre = _snapshot(publish.id, 201, datetime(2026, 10, 20, 10, tzinfo=UTC), -4.0, 50.0)
    snap_201_post = _snapshot(publish.id, 201, LIVE_KICKOFF + timedelta(hours=10), -9.0, 60.0)
    snap_202 = _snapshot(publish.id, 202, WEEK2_RUN_AT, -5.0, 57.0)
    session.add_all([snap_101, snap_201_pre, snap_201_post, snap_202])
    session.flush()
    session.add_all(
        [
            # Graded over on game 101 (54 scored; taken at 45.5, closed 47).
            _pick(snap_101.id, "total", "over", 45.5, 2, result="win", units=100 / 110, close=47.0),
            # Must never count: published after Alpha-Charlie kicked off.
            _pick(snap_201_post.id, "total", "over", 50.0, 3),
            # Open: Bravo-Delta hasn't started.
            _pick(snap_202.id, "total", "over", 50.5, 1),
        ]
    )


def _rating(run_id, team, basis, rating, off, de, games, rp, rr, sor) -> TeamRating:
    return TeamRating(
        run_id=run_id,
        team_id=team,
        basis=basis,
        variant="raw",
        rating=rating,
        off_rating=off,
        def_rating=de,
        games_played=games,
        provisional=True,
        rank_power=rp,
        rank_resume=rr,
        sor=sor,
        sos=None if sor is None else 1.5,
    )


def _snapshot(run_id, gid, published, spread, total) -> Prediction:
    margin = -spread
    return Prediction(
        run_id=run_id,
        game_id=gid,
        variant="raw",
        published_at=published,
        proj_home=(total + margin) / 2,
        proj_away=(total - margin) / 2,
        spread=spread,
        total=total,
        home_win_prob=0.6,
        sigma_margin=15.4,
        sigma_total=16.4,
        rho=0.03,
        fair_home_ml=-150,
        fair_away_ml=150,
        book_home_ml=-165,
        book_away_ml=140,
        book_spread_home_odds=-110,
        book_spread_away_odds=-110,
        book_over_odds=-110,
        book_under_odds=-110,
    )


def _pick(pred_id, market, side, line, tier, result=None, units=None, close=None) -> Pick:
    graded = datetime(2026, 10, 18, 10, tzinfo=UTC) if result else None
    return Pick(
        prediction_id=pred_id,
        market=market,
        side=side,
        line_taken=line,
        odds_taken=-110,
        edge=0.03,
        tier=tier,
        stake_units=1.0,
        kelly_units=1.5,
        closing_line=close,
        result=result,
        units_won=units,
        graded_at=graded,
    )

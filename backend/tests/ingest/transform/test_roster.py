from datetime import UTC, datetime

import pytest

from tsi.ingest.transform.roster import (
    coach_changes,
    portal_net,
    preseason_coaches,
    recruiting_average,
)

IDS = {"Georgia": 61, "Colorado": 38, "Alabama": 333}


def test_recruiting_averages_the_last_four_classes() -> None:
    classes = {
        2021: [{"team": "Georgia", "points": 300.0}],
        2022: [{"team": "Georgia", "points": 310.0}],
        2023: [{"team": "Georgia", "points": 290.0}, {"team": "Colorado", "points": 200.0}],
        2024: [{"team": "Georgia", "points": 320.0}],
        2020: [{"team": "Georgia", "points": 999.0}],  # too old: ignored
    }

    avg = recruiting_average(classes, 2024, IDS)

    assert avg[61] == pytest.approx(305.0)
    assert avg[38] == pytest.approx(200.0)  # only the classes that exist


def move(origin, dest, stars, when="2024-01-05T00:00:00.000Z", eligibility="Immediate"):
    return {
        "origin": origin,
        "destination": dest,
        "stars": stars,
        "transferDate": when,
        "eligibility": eligibility,
    }


def test_portal_net_is_stars_in_minus_out() -> None:
    raw = [
        move("Georgia", "Colorado", 4),  # Georgia -2, Colorado +2
        move("Alabama", "Colorado", 3),  # Alabama -1, Colorado +1
        move("Colorado", None, 2),  # Colorado -0.5 (no destination yet)
        move("Georgia", "Colorado", 5, eligibility="Withdrawn"),  # ignored
        move("Alabama", "Georgia", 5, when="2024-09-02T00:00:00.000Z"),  # after Aug 1: ignored
    ]

    net = portal_net(raw, 2024, IDS)

    assert net == {61: -2.0, 38: 2.5, 333: -1.0}


def coach(cid, hired, *stints):
    return {"id": cid, "hireDate": hired, "seasons": [{"teamId": t, "year": y} for t, y in stints]}


def test_preseason_coach_ignores_midseason_hires() -> None:
    raw = [
        coach(1, "2019-12-01T00:00:00.000Z", (242, 2024)),  # fired midseason, still preseason coach
        coach(2, "2024-10-27T00:00:00.000Z", (242, 2024)),  # interim hired in October
    ]

    assert preseason_coaches(raw, 2024) == {242: 1}


def test_coach_change_flag() -> None:
    assert coach_changes({1: 10, 2: 20, 3: 30}, {1: 10, 2: 21}) == {1: False, 2: True}


def test_preseason_cutoff_is_august_first() -> None:
    from tsi.ingest.transform.roster import preseason_cutoff

    assert preseason_cutoff(2024) == datetime(2024, 8, 1, tzinfo=UTC)

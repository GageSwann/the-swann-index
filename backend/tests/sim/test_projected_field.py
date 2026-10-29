from tsi.sim.cfp_format import FORMAT_2026
from tsi.sim.projected_field import OddsRow, projected_field


def row(tid, conf, make, title=None, mean_seed=6.0, slug=None) -> OddsRow:
    dist = [0.0] * 12
    dist[round(mean_seed) - 1] = make  # all of its field appearances at one seed
    return OddsRow(tid, slug or f"t{tid}", conf, make, title, dist)


def test_projected_field_follows_the_bid_rules() -> None:
    rows = [row(t, "Big Ten", 0.9 - t / 100, title=0.1, mean_seed=1 + t % 12) for t in range(14)]
    rows += [
        row(20, "SEC", 0.30, title=0.6, mean_seed=10),  # likeliest SEC champion
        row(21, "ACC", 0.20, title=0.5, mean_seed=11),
        row(22, "Big 12", 0.15, title=0.4, mean_seed=12),
        row(23, "Sun Belt", 0.10, title=0.5, mean_seed=12),  # best group-of-six odds
        row(24, "Mountain West", 0.05, title=0.5, mean_seed=12),
        row(30, "FBS Independents", 0.85, mean_seed=4, slug="notre-dame"),
    ]
    rows[0] = row(0, "Big Ten", 0.95, title=0.7, mean_seed=1)  # Big Ten favorite

    field = projected_field(rows, FORMAT_2026)
    ids = [r.team_id for r in field]

    assert len(ids) == 12 and len(set(ids)) == 12
    assert {0, 20, 21, 22, 23, 30} <= set(ids)  # four champions, group of six, Notre Dame
    assert 24 not in ids
    assert ids[0] == 0  # seeds by average seed
    assert [r.mean_seed for r in field] == sorted(r.mean_seed for r in field)

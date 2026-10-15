import tsi.db.models  # noqa: F401  (registers tables)
from tsi.db.base import Base

TABLES = Base.metadata.tables


def test_all_schema_tables_registered() -> None:
    assert set(TABLES) == {
        "calendar_weeks",
        "venues",
        "teams",
        "team_seasons",
        "games",
        "team_game_stats",
        "market_lines",
        "ingest_log",
        "priors",
        "model_runs",
        "team_ratings",
        "predictions",
        "picks",
    }


def test_conference_and_division_are_per_season() -> None:
    assert {"conference", "division"}.isdisjoint(TABLES["teams"].columns.keys())
    pk = [col.name for col in TABLES["team_seasons"].primary_key.columns]
    assert pk == ["team_id", "season"]


def test_schema_never_hard_codes_a_division() -> None:
    # Rule 5: no "fbs"/"fcs" literals in constraints, defaults, or names.
    for table in TABLES.values():
        texts = [str(c.sqltext) for c in table.constraints if hasattr(c, "sqltext")]
        texts += [str(col.default.arg) for col in table.columns if col.default is not None]
        texts += [table.name, *table.columns.keys()]
        assert not any(word in t.lower() for t in texts for word in ("fbs", "fcs"))


def test_raw_and_adjusted_variants_are_separate_rows() -> None:
    # Rule 6: raw and adjusted output stored separately.
    assert "variant" in TABLES["predictions"].columns
    rating_pk = [col.name for col in TABLES["team_ratings"].primary_key.columns]
    assert rating_pk == ["run_id", "team_id", "variant"]


def test_predictions_have_no_mutable_lock_flag() -> None:
    # Lock is derived from published_at < kickoff; nothing to update in place.
    assert "locked" not in TABLES["predictions"].columns

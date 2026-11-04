from typer.testing import CliRunner

from tsi import __version__
from tsi.cli import app

runner = CliRunner()


def test_version_flag_prints_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.output.strip() == f"tsi {__version__}"


def test_help_lists_tsi_description() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "The Swann Index" in result.output


def test_ingest_group_lists_loaders() -> None:
    result = runner.invoke(app, ["ingest", "--help"])

    assert result.exit_code == 0
    for command in (
        "daily",
        "season",
        "venues",
        "teams",
        "calendar",
        "games",
        "stats",
        "lines",
        "priors",
        "roster",
    ):
        assert command in result.output


def test_adjust_group_lists_commands() -> None:
    result = runner.invoke(app, ["adjust", "--help"])

    assert result.exit_code == 0
    for command in ("add", "list", "expire"):
        assert command in result.output


def test_adjust_add_takes_negative_points_and_game_days(monkeypatch) -> None:
    from contextlib import nullcontext
    from datetime import UTC, datetime

    import tsi.cli.adjust as cli

    seen = {}

    def fake_add(_sessions, new, _now):
        seen["new"] = new
        raise cli.AdjustmentError("stop here")

    monkeypatch.setattr(cli, "db_runtime", lambda: nullcontext(None))
    monkeypatch.setattr(cli, "add_adjustment", fake_add)
    result = runner.invoke(
        app,
        [
            "adjust",
            "add",
            "ohio-state",
            "--off",
            "-4",
            "--def",
            "-0.5",
            "-r",
            "QB out",
            "--from",
            "2026-11-07",
            "--through",
            "2026-11-14",
        ],
    )

    assert result.exit_code == 1 and "stop here" in result.output
    new = seen["new"]
    assert (new.off_points, new.def_points, new.reason) == (-4.0, -0.5, "QB out")
    assert new.starts_at == datetime(2026, 11, 7, 10, tzinfo=UTC)
    assert new.ends_at == datetime(2026, 11, 15, 10, tzinfo=UTC)


def test_adjust_add_rejects_a_bad_date() -> None:
    result = runner.invoke(app, ["adjust", "add", "x", "--off", "1", "-r", "y", "--from", "nov 7"])

    assert result.exit_code == 1 and "needs a date" in result.output

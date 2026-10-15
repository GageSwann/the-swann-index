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
    for command in ("daily", "venues", "teams", "calendar", "games"):
        assert command in result.output

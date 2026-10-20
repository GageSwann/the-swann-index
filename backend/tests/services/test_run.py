from tsi.services import run as run_module


def test_ingest_failure_is_reported_not_raised(monkeypatch) -> None:
    def boom(*_args, **_kwargs):
        raise TimeoutError("CFBD timed out")

    monkeypatch.setattr(run_module, "run_daily", boom)

    daily, error = run_module._ingest(object(), sessions=None, now=None)

    assert daily is None and error == "TimeoutError: CFBD timed out"


def test_no_client_means_ingest_skipped() -> None:
    assert run_module._ingest(None, sessions=None, now=None) == (None, None)

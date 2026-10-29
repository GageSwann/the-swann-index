from tsi.services.run import _guarded


def test_a_failing_optional_step_is_reported_not_raised() -> None:
    def boom() -> int:
        raise ValueError("no conferences")

    assert _guarded("season sim", lambda: 42) == (42, None)
    assert _guarded("season sim", boom) == (None, "ValueError: no conferences")

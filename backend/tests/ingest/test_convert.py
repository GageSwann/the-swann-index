import pytest

from tsi.ingest.convert import to_float, to_int


@pytest.mark.parametrize(
    ("value", "expected"), [("1634.04", 1634.04), (7, 7.0), (None, None), ("", None), ("n/a", None)]
)
def test_to_float(value, expected) -> None:
    assert to_float(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"), [("2024", 2024), (-110, -110), (None, None), ("regular", None)]
)
def test_to_int(value, expected) -> None:
    assert to_int(value) == expected

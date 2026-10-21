"""Backtest report tables for the API test seed: the shape `services/report_tables.py`
saves with a run, one row per table."""

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

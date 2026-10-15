from tsi.backtest.ats import ats_record


def test_bets_the_side_the_model_likes_more_than_the_market() -> None:
    #           model  market  actual
    games = [
        (10.0, 7.0, 14),  # model likes home more; home covered 7 -> win
        (3.0, 7.0, 14),  # model likes away more; home covered -> loss
        (10.0, 7.0, 7),  # push
        (7.0, 7.0, 20),  # no edge: no bet
    ]
    rec = ats_record(*zip(*games, strict=True))

    assert (rec.wins, rec.losses, rec.pushes, rec.bets) == (1, 1, 1, 2)
    assert rec.win_rate == 0.5


def test_min_edge_filters_small_disagreements() -> None:
    rec = ats_record([8.0, 12.0], [7.0, 7.0], [10, 10], min_edge=3.0)

    assert rec.bets == 1

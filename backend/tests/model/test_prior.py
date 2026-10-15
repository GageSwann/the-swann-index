import pytest

from tsi.model.prior import PriorInputs, fit_prior_model
from tsi.model.ratings.fit import TeamRating


def samples(n: int = 60):
    """final = 0.6 * last + 0.02 * (talent - 800) + 10 * (returning - 0.5) on both sides."""
    out = []
    for i in range(n):
        last = TeamRating(off=(i % 21) - 10.0, defense=((i * 7) % 17) - 8.0)
        talent, returning = 600.0 + (i * 37) % 400, (i % 10) / 10
        bump = 0.02 * (talent - 800) + 10 * (returning - 0.5)
        final = TeamRating(0.6 * last.off + bump, 0.6 * last.defense + bump)
        out.append((PriorInputs(last, talent, returning), final))
    return out


def test_full_model_recovers_relationship() -> None:
    model = fit_prior_model(samples())
    inputs = PriorInputs(TeamRating(10.0, -5.0), 900.0, 0.8)

    prior = model.predict(inputs)

    bump = 0.02 * 100 + 10 * 0.3
    assert prior.off == pytest.approx(6.0 + bump, abs=1e-6)
    assert prior.defense == pytest.approx(-3.0 + bump, abs=1e-6)


@pytest.mark.parametrize(
    "inputs",
    [
        PriorInputs(TeamRating(10.0, -5.0), 900.0, None),  # new to FBS: no returning production
        PriorInputs(None, 900.0, 0.8),  # was FCS last year: no FBS rating
        PriorInputs(TeamRating(10.0, -5.0), None, 0.8),  # before 2015: no talent
        PriorInputs(None, None, None),  # nothing at all
    ],
)
def test_missing_inputs_fall_back_to_a_smaller_model(inputs: PriorInputs) -> None:
    prior = fit_prior_model(samples()).predict(inputs)

    assert abs(prior.off) < 30 and abs(prior.defense) < 30  # finite, sensible


def test_more_talent_means_a_better_prior() -> None:
    model = fit_prior_model(samples())

    low = model.predict(PriorInputs(None, 600.0, None)).rating
    high = model.predict(PriorInputs(None, 1000.0, None)).rating

    assert high > low


def test_no_inputs_and_no_model_means_average() -> None:
    assert fit_prior_model([]).predict(PriorInputs(None, None, None)) == TeamRating(0.0, 0.0)

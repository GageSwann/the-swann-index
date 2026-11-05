from tsi.services.read.resume_view import benchmark_ranks


def test_runs_name_the_benchmark_ranks_they_used() -> None:
    # Saved with each run from 2026-11-06 (#133): FCS résumés vs. the #24 FCS team.
    assert benchmark_ranks({"resume_benchmark_rank": 12, "fcs_resume_benchmark_rank": 24}) == (
        12,
        24,
    )
    # Older runs didn't save them: #12 FBS, and #10 FCS (decision #91).
    assert benchmark_ranks({}) == (12, 10)

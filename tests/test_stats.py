import math

from benford.stats import BENFORD_EXPECTED, chi_square_statistic, digit_counts, mean_absolute_deviation


def test_benford_probs_sum_to_one():
    assert math.isclose(sum(BENFORD_EXPECTED.values()), 1.0, rel_tol=1e-9)


def test_perfect_benford_sample_has_low_chi():
    # Large synthetic sample matching Benford
    n = 90000
    counts = {d: int(round(n * BENFORD_EXPECTED[d])) for d in range(1, 10)}
    chi, df = chi_square_statistic(counts)
    assert df == 8
    assert chi < 50  # should be modest for near-perfect fit


def test_mad_zero_when_matching():
    n = 10000
    counts = {d: int(round(n * BENFORD_EXPECTED[d])) for d in range(1, 10)}
    mad = mean_absolute_deviation(counts)
    assert mad < 0.02


def test_digit_counts_ignores_invalid():
    assert digit_counts([1, 1, 2, 0, 10, 9]) == {1: 2, 2: 1, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 1}
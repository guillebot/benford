"""Benford's law expected distribution and goodness-of-fit metrics."""

from __future__ import annotations

import math
from typing import Sequence

BENFORD_EXPECTED: dict[int, float] = {
    d: math.log10(1 + 1 / d) for d in range(1, 10)
}


def observed_proportions(counts: dict[int, int]) -> dict[int, float]:
    total = sum(counts.get(d, 0) for d in range(1, 10))
    if total == 0:
        return {d: 0.0 for d in range(1, 10)}
    return {d: counts.get(d, 0) / total for d in range(1, 10)}


def digit_counts(digits: Sequence[int]) -> dict[int, int]:
    counts = {d: 0 for d in range(1, 10)}
    for d in digits:
        if 1 <= d <= 9:
            counts[d] += 1
    return counts


def chi_square_statistic(counts: dict[int, int]) -> tuple[float, int]:
    """Pearson chi-square against Benford; returns (statistic, df=8)."""
    n = sum(counts.values())
    if n == 0:
        return float("nan"), 8
    chi = 0.0
    for d in range(1, 10):
        observed = counts.get(d, 0)
        expected = n * BENFORD_EXPECTED[d]
        if expected > 0:
            chi += (observed - expected) ** 2 / expected
    return chi, 8


def mean_absolute_deviation(counts: dict[int, int]) -> float:
    """MAD between observed proportions and Benford expected."""
    obs = observed_proportions(counts)
    return sum(abs(obs[d] - BENFORD_EXPECTED[d]) for d in range(1, 10)) / 9.0


def fit_summary(digits: Sequence[int]) -> dict:
    counts = digit_counts(digits)
    n = sum(counts.values())
    chi, df = chi_square_statistic(counts)
    mad = mean_absolute_deviation(counts)
    return {
        "n_digits": n,
        "counts": counts,
        "proportions": observed_proportions(counts),
        "chi_square": chi,
        "chi_square_df": df,
        "mad": mad,
    }
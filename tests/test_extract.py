import math

import pytest

from benford.extract import (
    ExtractOptions,
    extract_numbers_from_text,
    first_significant_digit,
    leading_digits_from_text,
    parse_numeric_value,
)


@pytest.mark.parametrize(
    "token,expected",
    [
        ("1,234,567", 1234567.0),
        ("1.234.567", 1234567.0),
        ("-42.5", -42.5),
        ("0.0042", 0.0042),
        ("$1,299.99", 1299.99),
        ("15%", 15.0),
        ("−1,000", -1000.0),
    ],
)
def test_parse_numeric_value(token, expected):
    got = parse_numeric_value(token)
    assert got is not None
    assert math.isclose(got, expected, rel_tol=0, abs_tol=1e-9)


@pytest.mark.parametrize(
    "value,digit",
    [
        (1234, 1),
        (0.0042, 4),
        (-0.00089, 8),
        (9.99, 9),
        (0.00000012, 1),
    ],
)
def test_first_significant_digit(value, digit):
    assert first_significant_digit(value) == digit


def test_ignore_years_toggle():
    text = "Population grew from 1990 to 2020 reaching 1,500,000 residents."
    with_years = ExtractOptions(ignore_years=True)
    without_years = ExtractOptions(ignore_years=False)
    assert 1990 not in extract_numbers_from_text(text, with_years)
    assert 2020 not in extract_numbers_from_text(text, with_years)
    nums = extract_numbers_from_text(text, without_years)
    assert 1990 in nums and 2020 in nums
    assert 1_500_000 in nums


def test_leading_digits_from_text():
    text = "Revenue was $12,345,678.90 and margin 0.07% with 890 units sold."
    digits = leading_digits_from_text(text, ExtractOptions(ignore_years=True))
    assert 1 in digits  # from 12...
    assert 7 in digits  # from 0.07
    assert 8 in digits  # from 890
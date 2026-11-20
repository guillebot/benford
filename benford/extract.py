"""Parse numbers from visible text and compute first significant digits."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Iterable

# Token that may be a number: optional sign, digits with separators, optional % / currency prefix
_NUMBER_PATTERN = re.compile(
    r"""
    (?<![\w/])                                  # not inside words/paths
    (?P<sign>[-−])?\s*
    (?:
        (?P<cur_before>[$€£¥₹])\s*
        (?P<num_before>[\d][\d.,\s]*)
      |
        (?P<num_after>[\d][\d.,\s]*)
        \s*(?P<cur_after>%|[$€£¥₹]|(?:USD|EUR|GBP)\b)?
    )
    (?![\w/])
    """,
    re.VERBOSE | re.UNICODE,
)

_WHITESPACE_IN_NUM = re.compile(r"\s+")


@dataclass(frozen=True)
class ExtractOptions:
    ignore_years: bool = True
    year_min: int = 1900
    year_max: int = 2099


def _strip_separators(raw: str) -> tuple[str, bool]:
    """Normalize thousand/decimal separators to a plain decimal string."""
    s = _WHITESPACE_IN_NUM.sub("", raw.strip())
    if not s:
        return "", False

    has_comma = "," in s
    has_dot = "." in s

    if has_comma and has_dot:
        # Rightmost separator is decimal (1,234.56 vs 1.234,56)
        last_comma = s.rfind(",")
        last_dot = s.rfind(".")
        if last_dot > last_comma:
            s = s.replace(",", "")
        else:
            s = s.replace(".", "").replace(",", ".")
    elif has_comma:
        parts = s.split(",")
        if len(parts) > 1 and all(len(p) == 3 for p in parts[1:]):
            s = "".join(parts)
        else:
            s = s.replace(",", ".")
    # lone dots: if groups of 3, treat as thousands
    elif has_dot:
        parts = s.split(".")
        if len(parts) > 1 and all(len(p) == 3 for p in parts[1:]) and len(parts[-1]) == 3:
            s = "".join(parts)

    return s, True


def parse_numeric_value(token: str) -> float | None:
    """Parse one extracted token into a float, or None if not a valid number."""
    sign = -1.0 if token.startswith(("-", "−")) else 1.0
    body = token.lstrip("-−").strip()
    body = re.sub(r"^[$€£¥₹]\s*", "", body)
    body = re.sub(r"\s*(%|USD|EUR|GBP)\s*$", "", body, flags=re.I).strip()
    normalized, ok = _strip_separators(body)
    if not ok or not normalized:
        return None
    if normalized.count(".") > 1:
        return None
    try:
        value = float(normalized)
    except ValueError:
        return None
    if not math.isfinite(value) or value == 0:
        return None
    return sign * value


def first_significant_digit(value: float) -> int | None:
    """Return the first significant non-zero digit (1–9) for *value*."""
    if value == 0 or not math.isfinite(value):
        return None
    v = abs(value)
    if v >= 1:
        s = f"{v:.15g}"
    else:
        # scale up until we have a digit before the decimal
        exp = 0
        while v < 1 and exp < 308:
            v *= 10
            exp += 1
        s = f"{v:.15g}"
    for ch in s:
        if ch.isdigit() and ch != "0":
            return int(ch)
    return None


def _is_ignored_year(value: float, opts: ExtractOptions) -> bool:
    if not opts.ignore_years:
        return False
    if value < 0:
        return False
    if abs(value - round(value)) > 1e-9:
        return False
    y = int(round(value))
    return opts.year_min <= y <= opts.year_max


def extract_numbers_from_text(text: str, opts: ExtractOptions | None = None) -> list[float]:
    """Find all numeric tokens in *text*."""
    opts = opts or ExtractOptions()
    values: list[float] = []
    for m in _NUMBER_PATTERN.finditer(text):
        chunk = m.group(0)
        val = parse_numeric_value(chunk)
        if val is None:
            continue
        if _is_ignored_year(val, opts):
            continue
        values.append(val)
    return values


def leading_digits_from_text(text: str, opts: ExtractOptions | None = None) -> list[int]:
    """Extract first significant digits (1–9) from all numbers in *text*."""
    opts = opts or ExtractOptions()
    digits: list[int] = []
    for val in extract_numbers_from_text(text, opts):
        d = first_significant_digit(val)
        if d is not None:
            digits.append(d)
    return digits


def leading_digits_from_values(values: Iterable[float]) -> list[int]:
    out: list[int] = []
    for val in values:
        d = first_significant_digit(val)
        if d is not None:
            out.append(d)
    return out
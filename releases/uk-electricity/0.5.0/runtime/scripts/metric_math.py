"""Small Decimal helpers. Inputs must already satisfy a business data contract.

Return None for undefined rates. Never parse currencies, fill missing values,
round display output, or infer period comparability here.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Mapping

Number = str | int | Decimal


def decimal(value: Number) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
        raise ValueError("Use a decimal string, integer or Decimal; floats/missing values are ambiguous")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid decimal: {value!r}") from exc
    if not result.is_finite():
        raise ValueError("Non-finite numbers are not valid metrics")
    return result


def ratio(numerator: Number, denominator: Number) -> Decimal | None:
    top, bottom = decimal(numerator), decimal(denominator)
    return None if bottom == 0 else top / bottom


def growth(current: Number, previous: Number) -> Decimal | None:
    now, before = decimal(current), decimal(previous)
    return None if before <= 0 else (now - before) / before


def pooled_rate(numerators: list[Number], denominators: list[Number]) -> Decimal | None:
    if not numerators or len(numerators) != len(denominators):
        raise ValueError("Need nonempty paired numerator and denominator lists")
    tops = [decimal(value) for value in numerators]
    bottoms = [decimal(value) for value in denominators]
    if any(value < 0 for value in bottoms):
        raise ValueError("Pooled-rate weights cannot be negative")
    return ratio(sum(tops, Decimal(0)), sum(bottoms, Decimal(0)))


def contributions(current: Mapping[str, Number], previous: Mapping[str, Number],
                  *, near_zero: Number = "0") -> dict[str, object]:
    """Additive metrics only; caller must align mutually exclusive categories."""
    if not current or set(current) != set(previous):
        raise ValueError("Category sets must be nonempty and identical; missing is not zero")
    tolerance = decimal(near_zero)
    if tolerance < 0:
        raise ValueError("near_zero must be nonnegative")
    deltas = {key: decimal(current[key]) - decimal(previous[key]) for key in current}
    total = sum(deltas.values(), Decimal(0))
    shares = {key: None if abs(total) <= tolerance else value / total
              for key, value in deltas.items()}
    return {"delta_total": total, "deltas": deltas, "contributions": shares}

"""Poisson / geometric probability model (assumes pi is normal)."""
import math

_LOG10 = math.log(10.0)


def expected_occurrences(pattern_length: int, digits_searched: int) -> float:
    if pattern_length <= 0 or digits_searched <= 0:
        return 0.0
    log_lam = math.log(digits_searched) - pattern_length * _LOG10
    return math.exp(log_lam) if log_lam > -700 else 0.0


def match_probability(pattern_length: int, digits_searched: int) -> float:
    lam = expected_occurrences(pattern_length, digits_searched)
    if lam <= 0:
        return 0.0
    return -math.expm1(-lam)


def expected_wait_digits(pattern_length: int) -> float:
    if pattern_length <= 0:
        return 0.0
    e = pattern_length * _LOG10
    return math.exp(e) if e < 700 else float("inf")

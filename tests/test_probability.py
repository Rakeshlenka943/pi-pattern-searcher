import math
from pi_search.probability import match_probability, expected_wait_digits

def test_zero():
    assert match_probability(5, 0) == 0.0

def test_monotonic():
    assert match_probability(3, 10_000) > match_probability(3, 100)

def test_expected_wait():
    assert math.isclose(expected_wait_digits(3), 1000.0, rel_tol=1e-12)

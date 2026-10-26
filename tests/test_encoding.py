import pytest
from pi_search.encoding import word_to_digits, digits_to_word

def test_padded_roundtrip():
    d = word_to_digits("Aman", "padded")
    assert d == "065109097110"
    assert digits_to_word(d, "padded") == "Aman"

def test_padded_bad_length():
    with pytest.raises(ValueError):
        digits_to_word("0651", "padded")

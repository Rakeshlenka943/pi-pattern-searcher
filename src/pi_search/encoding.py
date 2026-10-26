"""Word <-> digit encoding for pattern search."""


def word_to_digits(word: str, encoding: str = "padded") -> str:
    """Encode a word as an ASCII-digit string.

    padded : 3-digit fixed width, unambiguous (recommended)
    ascii  : variable width, shorter, ambiguous on decode
    """
    if not word:
        return ""
    if encoding == "padded":
        return "".join(f"{ord(c):03d}" for c in word)
    if encoding == "ascii":
        return "".join(str(ord(c)) for c in word)
    raise ValueError(f"unknown encoding: {encoding!r}")


def digits_to_word(digits: str, encoding: str = "padded") -> str:
    """Best-effort decode (exact for padded, greedy for ascii)."""
    if not digits:
        return ""
    if encoding == "padded":
        if len(digits) % 3:
            raise ValueError("padded digit string length must be a multiple of 3")
        return "".join(chr(int(digits[i:i + 3])) for i in range(0, len(digits), 3))
    if encoding == "ascii":
        out, i = [], 0
        while i < len(digits):
            if i + 3 <= len(digits) and digits[i] != "0":
                out.append(chr(int(digits[i:i + 3]))); i += 3
            elif i + 2 <= len(digits):
                out.append(chr(int(digits[i:i + 2]))); i += 2
            else:
                raise ValueError(f"cannot decode at {i}")
        return "".join(out)
    raise ValueError(f"unknown encoding: {encoding!r}")

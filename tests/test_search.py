from pi_search.search import (naive_search, kmp_search, rabin_karp_search,
                              search_stream)

def test_algorithms_agree():
    text = "31415926535897932384"
    for pat in ["1592", "65", "8323", "99"]:
        expected = text.find(pat)
        assert kmp_search(text, pat) == expected
        assert rabin_karp_search(text, pat) == expected
        assert naive_search(text, pat) == expected

def test_stream_crosses_chunk_boundary():
    assert search_stream(iter(["3141", "5926", "5358"]), "9265") == (5, 12)

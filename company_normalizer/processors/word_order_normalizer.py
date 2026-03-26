"""
Word-order normaliser — detects "jumbled" variants.

"Tata Chemical Magadhi Limited" and "Tata Magadhi Chemical Limited"
contain the same words in different order.  By converting the base-name
token set to a frozenset (order-independent), we can detect and merge them.
"""


def canonical_token_fingerprint(base_name: str) -> frozenset:
    """Return frozenset of UPPER tokens — order-insensitive identity."""
    if not base_name:
        return frozenset()
    return frozenset(base_name.upper().split())


def names_are_word_order_variants(base1: str, base2: str) -> bool:
    """True if base1 and base2 contain exactly the same words, any order."""
    fp1 = canonical_token_fingerprint(base1)
    fp2 = canonical_token_fingerprint(base2)
    return bool(fp1) and fp1 == fp2

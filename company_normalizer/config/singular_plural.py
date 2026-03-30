"""
Approved singular/plural word automated pairing using NLP.
Plural words are converted TO singular, not singular to plural.
Only valid dictionary words are converted to protect proper brand names.
"""

from functools import lru_cache
from company_normalizer.config.shared import engine as _engine, spell as _spell


@lru_cache(maxsize=4096)
def normalize_word(word: str) -> str:
    """Return the canonical SINGULAR form if it's a valid dictionary word.
    
    Results are cached — each unique word is only processed once per session,
    giving a major speed boost on large datasets with repeated words.
    """
    w_upper = word.upper().strip()
    if not w_upper:
        return ""

    # 1. Ask inflect for singular form (returns False if already singular)
    singular = _engine.singular_noun(word)

    # 2. If recognised as plural and a singular was returned
    if singular:
        # 3. Check if the singular form is a valid English word
        # pyspellchecker works in lowercase
        if _spell.known([str(singular).lower()]):
            return str(singular).upper()

    return w_upper


def is_approved_pair(word1: str, word2: str) -> bool:
    """Return True if word1 and word2 map to the same algorithmic singular form."""
    c1 = normalize_word(word1)
    c2 = normalize_word(word2)
    return c1 == c2 and c1 != ""

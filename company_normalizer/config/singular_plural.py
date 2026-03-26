"""
Approved singular/plural word pairs.  Canonical form is always the SINGULAR.
Plural words are converted TO singular, not singular to plural.
Only words in this list are normalised — everything else is left alone.
"""

# Map: any form (singular or plural) → canonical SINGULAR
SINGULAR_PLURAL_MAP = {
    # plural → singular  (these are the "source" variants)
    "SYSTEMS":       "SYSTEM",
    "SERVICES":      "SERVICE",
    "PRODUCTS":      "PRODUCT",
    "SOLUTIONS":     "SOLUTION",
    "ENTERPRISES":   "ENTERPRISE",
    "PROJECTS":      "PROJECT",
    "TECHNOLOGIES":  "TECHNOLOGY",
    "TECHNOLOGIE":   "TECHNOLOGY",   # malformed variant
    "INDUSTRIES":    "INDUSTRY",
    "CHEMICALS":     "CHEMICAL",
    "MINERALS":      "MINERAL",
    "RESOURCES":     "RESOURCE",
    "HOLDINGS":      "HOLDING",
    "VENTURES":      "VENTURE",
    "COMMODITIES":   "COMMODITY",
    "COMMODITIE":    "COMMODITY",    # malformed variant
    # singular stays as-is (identity mapping so normalize_word returns itself)
    "SYSTEM":        "SYSTEM",
    "SERVICE":       "SERVICE",
    "PRODUCT":       "PRODUCT",
    "SOLUTION":      "SOLUTION",
    "ENTERPRISE":    "ENTERPRISE",
    "PROJECT":       "PROJECT",
    "TECHNOLOGY":    "TECHNOLOGY",
    "INDUSTRY":      "INDUSTRY",
    "CHEMICAL":      "CHEMICAL",
    "MINERAL":       "MINERAL",
    "RESOURCE":      "RESOURCE",
    "HOLDING":       "HOLDING",
    "VENTURE":       "VENTURE",
    "COMMODITY":     "COMMODITY",
}

WORD_NORMALIZATION_MAP = {k.upper(): v.upper() for k, v in SINGULAR_PLURAL_MAP.items()}

# All canonical (singular) values
CANONICAL_FORMS = set(WORD_NORMALIZATION_MAP.values())


def normalize_word(word: str) -> str:
    """Return the canonical SINGULAR form, or the word unchanged if not in map."""
    return WORD_NORMALIZATION_MAP.get(word.upper().strip(), word)


def is_approved_pair(word1: str, word2: str) -> bool:
    """Return True if word1 and word2 map to the same canonical singular form."""
    c1 = WORD_NORMALIZATION_MAP.get(word1.upper().strip(), word1.upper().strip())
    c2 = WORD_NORMALIZATION_MAP.get(word2.upper().strip(), word2.upper().strip())
    return c1 == c2 and c1 in CANONICAL_FORMS

"""
Functional descriptors — primary business-type words.
If these DIFFER between two names, the names CANNOT be merged.

IMPORTANT: Store only the SINGULAR canonical form here.
Extraction normalises input words to singular before matching,
so "CHEMICALS" and "CHEMICAL" are treated identically.
"""

from company_normalizer.config.singular_plural import normalize_word

# Store SINGULAR forms only.
# The extractor normalises every input word before lookup,
# so plural variants (CHEMICALS, INDUSTRIES, TECHNOLOGIES …)
# automatically map to the canonical singular here.
FUNCTIONAL_DESCRIPTORS = frozenset([
    "LOGISTIC",      # logistics / logistic
    "TRADING",       # no plural variant
    "FINANCE",       # finance / financial handled separately
    "FINANCIAL",
    "HOLDING",       # holdings / holding
    "POWER",
    "ENERGY",
    "INFRA",
    "INFRASTRUCTURE",
    "SERVICE",       # services / service
    "PROJECT",       # projects / project
    "TECHNOLOGY",    # technologies / technology
    "SYSTEM",        # systems / system
    "SOLUTION",      # solutions / solution
    "ENTERPRISE",    # enterprises / enterprise
    "MANUFACTURING",
    "INDUSTRY",      # industries / industry
    "EXPORT",        # exports / export
    "IMPORT",        # imports / import
    "CHEMICAL",      # chemicals / chemical
    "PHARMA",
    "PHARMACEUTICAL", # pharmaceuticals / pharmaceutical
    "FOOD",          # foods / food
    "AGRO",
    "TEXTILE",       # textiles / textile
    "RETAIL",
    "CAPITAL",
])


def get_functional_descriptors() -> list:
    return list(FUNCTIONAL_DESCRIPTORS)


def is_functional_descriptor(word: str) -> bool:
    """Check if a word (or its singular form) is a functional descriptor."""
    return normalize_word(word.upper().strip()) in FUNCTIONAL_DESCRIPTORS

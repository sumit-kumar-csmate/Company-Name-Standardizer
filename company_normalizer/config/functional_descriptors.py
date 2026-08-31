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
    # ── Logistics & Trade ────────────────────────────────────────────────────
    "LOGISTIC",      # logistics / logistic
    "TRADING",       # no plural variant
    "EXPORT",        # exports / export
    "IMPORT",        # imports / import
    "SHIPPING",
    "TRANSPORT",

    # ── Finance & Investment ─────────────────────────────────────────────────
    "FINANCE",
    "FINANCIAL",
    "HOLDING",       # holdings / holding
    "CAPITAL",
    "INVESTMENT",
    "INSURANCE",
    "BANK",

    # ── Energy & Infrastructure ──────────────────────────────────────────────
    "POWER",
    "ENERGY",
    "INFRA",
    "INFRASTRUCTURE",
    "PETROLEUM",
    "OIL",
    "GAS",
    "ELECTRIC",

    # ── Technology & Services ────────────────────────────────────────────────
    "SERVICE",       # services / service
    "PROJECT",       # projects / project
    "TECHNOLOGY",    # technologies / technology
    "SYSTEM",        # systems / system
    "SOLUTION",      # solutions / solution
    "ENTERPRISE",    # enterprises / enterprise
    "MEDIA",

    # ── Manufacturing & Industry ─────────────────────────────────────────────
    "MANUFACTURING",
    "INDUSTRY",      # industries / industry
    "ENGINEERING",
    "CONSTRUCTION",
    "MINING",
    "STEEL",
    "CEMENT",
    "PAPER",
    "RUBBER",
    "PAINT",

    # ── Chemicals & Life Sciences ────────────────────────────────────────────
    "CHEMICAL",      # chemicals / chemical
    "PHARMA",
    "PHARMACEUTICAL", # pharmaceuticals / pharmaceutical

    # ── Consumer & Retail ────────────────────────────────────────────────────
    "FOOD",          # foods / food
    "AGRO",
    "TEXTILE",       # textiles / textile
    "RETAIL",

    # ── Real Estate ──────────────────────────────────────────────────────────
    "PROPERTY",
    "ESTATE",
])


def get_functional_descriptors() -> list:
    return list(FUNCTIONAL_DESCRIPTORS)


def is_functional_descriptor(word: str) -> bool:
    """Check if a word (or its singular form) is a functional descriptor."""
    return normalize_word(word.upper().strip()) in FUNCTIONAL_DESCRIPTORS

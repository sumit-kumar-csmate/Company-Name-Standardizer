"""
Geographic terms — country/region names that affect merge decisions
but are NOT stripped from company names.
"""

GEOGRAPHIC_TERMS = [
    "INDIA", "INDIAN", "ASIA", "ASIAN",
    "USA", "US", "AMERICA", "AMERICAN",
    "UK", "BRITAIN", "BRITISH",
    "EUROPE", "EUROPEAN",
    "UAE", "DUBAI",
    "CHINA", "CHINESE",
    "JAPAN", "JAPANESE",
    "KOREA", "KOREAN",
    "GERMANY", "GERMAN",
    "FRANCE", "FRENCH",
    "AUSTRALIA", "AUSTRALIAN",
    "CANADA", "CANADIAN",
    "SINGAPORE", "MALAYSIA", "THAILAND", "INDONESIA",
    "GLOBAL", "INTERNATIONAL", "INTL", "WORLDWIDE", "MULTINATIONAL",
]

GEOGRAPHIC_TERMS = [t.upper() for t in GEOGRAPHIC_TERMS]


def get_geographic_terms() -> list:
    return GEOGRAPHIC_TERMS


def is_geographic_term(word: str) -> bool:
    return word.upper().strip() in GEOGRAPHIC_TERMS

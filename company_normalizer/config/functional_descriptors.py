"""
Functional descriptors — primary business-type words.
If these DIFFER between two names, the names CANNOT be merged.
"""

FUNCTIONAL_DESCRIPTORS = [
    "LOGISTICS", "TRADING", "FINANCE", "FINANCIAL", "HOLDINGS", "HOLDING",
    "POWER", "ENERGY", "INFRA", "INFRASTRUCTURE", "SERVICES", "PROJECTS",
    "TECHNOLOGIES", "SYSTEMS", "SOLUTIONS", "ENTERPRISES", "MANUFACTURING",
    "INDUSTRIES", "EXPORTS", "IMPORTS", "CHEMICALS", "PHARMA",
    "PHARMACEUTICALS", "FOODS", "AGRO", "TEXTILES", "RETAIL", "CAPITAL",
]

FUNCTIONAL_DESCRIPTORS = [d.upper() for d in FUNCTIONAL_DESCRIPTORS]


def get_functional_descriptors() -> list:
    return FUNCTIONAL_DESCRIPTORS


def is_functional_descriptor(word: str) -> bool:
    return word.upper().strip() in FUNCTIONAL_DESCRIPTORS

"""
Configuration for prefix removal.
Longer/more-specific prefixes come first so "TO THE ORDER OF" is matched before "TO ORDER".
"""

# Trade/Shipment Prefixes
TRADE_PREFIXES = [
    "CONSIGNEE TO",
    "TO THE ORDER OF",
    "TO THE ORDER",
    "TO ORDER OF",
    "TO ORDER",
    "NOTIFIED PARTY",
    "ON BEHALF OF",
    "CARE OF",
    "C/O",
]

# Business Prefixes
BUSINESS_PREFIXES = [
    "MESSRS OF",
    "MESSRS",
    "M/S",
    "M S",
    "M.S.",
    "MR.",
    "MS.",
    "MS",
]

# Legal/Jurisdiction Prefixes
LEGAL_PREFIXES = [
    "P.T.",
    "PT",
    "CV",
]

TRADE_PREFIXES    = [p.upper() for p in TRADE_PREFIXES]
BUSINESS_PREFIXES = [p.upper() for p in BUSINESS_PREFIXES]
LEGAL_PREFIXES    = [p.upper() for p in LEGAL_PREFIXES]
ALL_PREFIXES      = TRADE_PREFIXES + BUSINESS_PREFIXES + LEGAL_PREFIXES


def get_all_prefixes():
    return ALL_PREFIXES

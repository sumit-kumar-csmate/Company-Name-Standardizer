"""
Configuration for prefix removal.
Longer/more-specific prefixes come first so "TO THE ORDER OF" is matched before "TO ORDER".
"""

# Trade/Shipment Prefixes
TRADE_PREFIXES = [
    "CONSIGNEE TO",
    "CONSIGNEE",
    "TO THE"
    "TO THE ORDER OF",
    "TO THE ORDEROF",
    "TO THE ORDER",
    "TO ORDER OF",
    "TO ORDER",
    "TO THE ORDER ORDER",
    "NOTIFIED PARTY",
    "NOTIFY",
    "NOTIFY PARTY",
    "ON BEHALF OF",
    "O/B",
    "BY ORDER OF",
    "B/O",
    "CARE OF",
    "C/O",
    "ACCOUNT OF",
    "A/C",
    "F/A",
    "FOR THE ACCOUNT OF",
    "TO THE OERDER"
]

# Business Prefixes
BUSINESS_PREFIXES = [
    "MESSRS OF",
    "MESSRS",
    "M/S",
    "M S",
    "M.S.",
    "MR.",
    "MR",
    "MS.",
    "MS",
    "ETS",
    "ETS.",
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
    # Dynamically sort by string length descending to ensure longest matches first
    return sorted(ALL_PREFIXES, key=len, reverse=True)

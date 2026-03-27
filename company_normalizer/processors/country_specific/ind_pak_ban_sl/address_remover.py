"""
Address removal module — strips trailing address components.
Applied BEFORE prefix removal.  Does NOT remove geographic country terms.
"""

import re
from company_normalizer.config.geography import is_geographic_term

ADDRESS_KEYWORDS = {
    "BUILDING", "BLDG", "BLD", "FLOOR", "FLR",
    "BLOCK","STREET", "ROAD", "AVENUE", "LANE", "TOWER", "PLAZA",
    "COMPLEX", "HOUSE", "SUITE",
    "UNIT", "ROOM", "NUMBER", "NEAR",
    "OPPOSITE", "SECTOR", "PHASE", "PLOT",
    "FLAT", "NAGAR", "COLONY", "AREA", "ZONE",
    "DISTRICT", "TEHSIL", "TALUKA", "VILLAGE",
}


def remove_address_details(name: str):
    """
    Remove address-related words from the RIGHT end of *name*.

    Returns (name_without_address, removed_address_string).
    """
    if not name or not isinstance(name, str):
        return "", ""

    original = name
    words    = name.split()

    if len(words) <= 2:
        return name, ""

    clean_words  = list(words)
    removed_parts = []
    changed = True

    while changed and len(clean_words) > 2:
        changed = False
        last    = clean_words[-1]

        if is_geographic_term(last):
            break

        # Pure trailing number
        if last.isdigit():
            removed_parts.insert(0, clean_words.pop())
            changed = True
            continue

        # Address keyword
        if last.upper() in ADDRESS_KEYWORDS:
            removed_parts.insert(0, clean_words.pop())
            changed = True
            continue

        # Short alphanumeric unit code after an address word was already removed
        if removed_parts and len(last) <= 2 and last.isalnum():
            removed_parts.insert(0, clean_words.pop())
            changed = True
            continue

        # Unit codes like A4, B12, 3B
        if removed_parts and re.fullmatch(r'[A-Z]\d+|\d+[A-Z]', last, re.IGNORECASE):
            removed_parts.insert(0, clean_words.pop())
            changed = True
            continue

    result = ' '.join(clean_words).strip()
    return (result, ' '.join(removed_parts).strip()) if result else (original, "")

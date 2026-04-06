"""Geographic term extraction and merge-rule evaluation."""

from company_normalizer.config.geography import get_geographic_terms


def extract_geography(name: str) -> set:
    if not name:
        return set()
    geo = set(get_geographic_terms())
    return {w for w in name.upper().split() if w in geo}


def geography_allows_merge(geo1: set, geo2: set) -> bool:
    """
    Rules:
    1. Neither has geography or one is empty → ALLOW
    2. Both have same geography → ALLOW
    3. Different geographies → BLOCK
    """
    if not geo1 or not geo2:
        return True
    if geo1 == geo2:
        return True
    return False

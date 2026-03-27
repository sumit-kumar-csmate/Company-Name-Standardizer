"""Functional descriptor extraction and conflict checking."""

from company_normalizer.config.functional_descriptors import get_functional_descriptors


def extract_descriptors(name: str) -> set:
    if not name:
        return set()
    fd = set(get_functional_descriptors())
    return {w for w in name.upper().split() if w in fd}


def descriptors_allow_merge(desc1: set, desc2: set) -> bool:
    if not desc1 and not desc2:
        return True
    return desc1 == desc2

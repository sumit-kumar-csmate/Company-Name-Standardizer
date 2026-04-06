"""Functional descriptor extraction and conflict checking.

Words are normalised to their canonical SINGULAR form before lookup so that
plural variants (e.g. CHEMICALS, INDUSTRIES, TECHNOLOGIES) match their
singular descriptor entry (CHEMICAL, INDUSTRY, TECHNOLOGY).

This means 'Amazon Papyrus Chemical' and 'Amazon Papyrus Chemicals'
produce the identical descriptor set {CHEMICAL} and are never falsely blocked.
"""

from company_normalizer.config.singular_plural import normalize_word
from company_normalizer.config.functional_descriptors import FUNCTIONAL_DESCRIPTORS


def extract_descriptors(name: str) -> set:
    """Extract functional descriptors from *name*, normalising to singular first."""
    if not name:
        return set()
    result = set()
    for w in name.upper().split():
        canonical = normalize_word(w)   # CHEMICALS → CHEMICAL, INDUSTRIES → INDUSTRY …
        if canonical in FUNCTIONAL_DESCRIPTORS:
            result.add(canonical)
    return result


def descriptors_allow_merge(desc1: set, desc2: set) -> bool:
    """Return True if the two descriptor sets are compatible (same or both empty)."""
    if not desc1 and not desc2:
        return True
    return desc1 == desc2

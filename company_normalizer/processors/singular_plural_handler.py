"""Singular/plural normalisation for approved word pairs."""

from ..config.singular_plural import normalize_word, is_approved_pair


def normalize_words_in_name(name: str) -> str:
    if not name:
        return ""
    return ' '.join(normalize_word(w) for w in name.split())


def names_differ_only_by_approved_pairs(name1: str, name2: str) -> bool:
    """Return True if names differ only in approved singular/plural words (same word count)."""
    if not name1 or not name2:
        return False
    w1, w2 = name1.upper().split(), name2.upper().split()
    if len(w1) != len(w2):
        return False
    diffs = 0
    for a, b in zip(w1, w2):
        if a != b:
            if not is_approved_pair(a, b):
                return False
            diffs += 1
    return diffs > 0

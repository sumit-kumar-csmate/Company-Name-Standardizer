"""Singular/plural normalisation for approved word pairs."""

from company_normalizer.config.singular_plural import normalize_word, is_approved_pair


SYNONYM_MAP = {
    "BIOTECHNOLOGY": "BIOTECH",
    "TECH": "TECHNOLOGY",
    "PHARMA": "PHARMACEUTICAL",
    "MFG": "MANUFACTURING",
    "INTL": "INTERNATIONAL",
}

def normalize_words_in_name(name: str, apply_synonyms: bool = False) -> str:
    if not name:
        return ""
    words = []
    for w in name.split():
        nw = normalize_word(w)
        if apply_synonyms:
            nw = SYNONYM_MAP.get(nw, nw)
        words.append(nw)
    return ' '.join(words)


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
            na = normalize_word(a)
            nb = normalize_word(b)
            if na != nb:
                sa = SYNONYM_MAP.get(na, na)
                sb = SYNONYM_MAP.get(nb, nb)
                if sa != sb:
                    return False
            diffs += 1
    return diffs > 0

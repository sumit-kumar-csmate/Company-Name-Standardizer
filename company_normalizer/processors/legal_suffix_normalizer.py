"""Legal suffix extraction and normalisation."""

from company_normalizer.config.legal_suffixes import normalize_suffix as _cfg_normalize, get_all_suffixes


def extract_and_normalize_suffix(name: str):
    """
    Extract the legal suffix from the END of *name* and normalise it.
    Returns (base_name, canonical_suffix, family_id).
    """
    if not name or not isinstance(name, str):
        return "", "", None

    name    = name.strip()
    name_up = name.upper()

    for suffix in sorted(get_all_suffixes(), key=len, reverse=True):
        suf_up = suffix.upper()
        if not name_up.endswith(suf_up):
            continue
        slen = len(suf_up)
        if slen == len(name_up):
            return name, "", None      # entire name = suffix
        if name_up[-(slen + 1)] == ' ':
            base             = name[:-(slen + 1)].strip()
            canon, family_id = _cfg_normalize(suffix)
            # Malaysia-only rule: replace "Malaysia/Malaysian" before a suffix with "M"
            # e.g. "Apical Malaysia Sdn Bhd" → "Apical M Sdn Bhd"
            base_words = base.split()
            if base_words and base_words[-1].upper() in ("MALAYSIA", "MALAYSIAN"):
                base_words[-1] = "M"
            base = ' '.join(base_words).strip() or base
            return base, canon, family_id

    return name, "", None


def suffixes_can_merge(family1: str, family2: str) -> bool:
    if not family1 or not family2:
        return False
    return family1 == family2

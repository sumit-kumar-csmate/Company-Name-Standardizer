"""Prefix removal — strips trade/business/legal prefixes from the START of a name."""

from company_normalizer.config.prefixes import get_all_prefixes, TRADE_PREFIXES, BUSINESS_PREFIXES, LEGAL_PREFIXES

# All known prefix strings in uppercase, used to detect "only-prefix" names
_ALL_KNOWN_PREFIXES_UPPER = [p.upper() for p in TRADE_PREFIXES + BUSINESS_PREFIXES + LEGAL_PREFIXES]


def remove_prefixes(name: str):
    """
    Iteratively remove all known prefixes from the start of *name*.

    Returns
    -------
    (clean_name, [removed_prefix, …], only_prefix)
      clean_name   — name with prefixes stripped
      removed_prefix — list of prefixes that were removed
      only_prefix  — True when the ENTIRE original name consists solely of
                     one or more known prefixes (nothing meaningful remains);
                     caller should output "Not Available" in this case.
    """
    if not name or not isinstance(name, str):
        return "", [], False

    current = name.strip()
    removed = []

    for _ in range(10):          # safety cap
        changed = False
        for prefix in get_all_prefixes():
            cur_up = current.upper()
            pre_up = prefix.upper()
            if not cur_up.startswith(pre_up):
                continue
            plen = len(pre_up)
            if plen == len(cur_up):
                # The prefix IS the entire remaining string — nothing else left.
                # Record it and signal that the name is only a prefix.
                removed.append(prefix)
                return "", removed, True

            # Strip if it's a completely matched trade prefix, OR if followed by a space
            from company_normalizer.config.prefixes import TRADE_PREFIXES
            if prefix in TRADE_PREFIXES or cur_up[plen] == ' ':
                current = current[plen:].strip()
                removed.append(prefix)
                changed = True
                break
        if not changed:
            break

    # Also handle case where the name (after earlier prefixes stripped) is now
    # an empty string — means everything was a prefix chain
    only_prefix = (current.strip() == "") and len(removed) > 0
    return current, removed, only_prefix

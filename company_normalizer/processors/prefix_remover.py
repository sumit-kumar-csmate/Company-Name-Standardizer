"""Prefix removal — strips trade/business/legal prefixes from the START of a name."""

from company_normalizer.config.prefixes import get_all_prefixes


def remove_prefixes(name: str):
    """
    Iteratively remove all known prefixes from the start of *name*.
    Returns (clean_name, [removed_prefix, …]).
    """
    if not name or not isinstance(name, str):
        return "", []

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
                continue         # prefix IS the whole name
            
            # Strip if it's a completely matched trade prefix, OR if followed by a space
            from company_normalizer.config.prefixes import TRADE_PREFIXES
            if prefix in TRADE_PREFIXES or cur_up[plen] == ' ':
                current = current[plen:].strip()
                removed.append(prefix)
                changed = True
                break
        if not changed:
            break

    return current, removed

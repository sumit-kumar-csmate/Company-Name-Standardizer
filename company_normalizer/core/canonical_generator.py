"""Canonical name generator — produces the final standardised output name."""

from ..processors.singular_plural_handler import normalize_words_in_name


def generate_canonical(name_data: dict) -> str:
    base   = name_data.get('base_name', '')
    suffix = name_data.get('legal_suffix', '')
    if not base:
        return ""
    norm = normalize_words_in_name(base)
    return f"{norm} {suffix}".strip() if suffix else norm.strip()


def _merge_andpvtltd_words(names_upper: list) -> set:
    """Collect all AND/PRIVATE/LIMITED words present across any name in group."""
    special = {"AND", "PRIVATE", "LIMITED"}
    found = set()
    for n in names_upper:
        for w in n.split():
            if w in special:
                found.add(w)
    return found


def generate_canonical_for_group(name_data_list: list, group_indices: list,
                                  merge_reason: str = "All rules align") -> str:
    """
    One canonical name for a whole merge group.

    AND/PVT/LTD rule:
      If merge_reason is AND_PVT_LTD_ONLY, the canonical name is built by
      taking the longest cleaned name in the group (most words), ensuring all
      of AND / PRIVATE / LIMITED that appear in ANY member are included,
      in a natural position (AND between core words if applicable, then PRIVATE,
      then LIMITED at the end).

    PRIVATE_LIMITED_FAMILY rule:
      If ANY member has "PRIVATE LIMITED", the whole group gets "PRIVATE LIMITED".
    """
    if not group_indices:
        return ""

    primary = name_data_list[group_indices[0]]
    family  = primary.get('legal_family')

    # ── AND/PVT/LTD merge canonical ──────────────────────────────────────────
    if merge_reason == "AND_PVT_LTD_ONLY":
        # Pick the member whose cleaned text is longest (most complete)
        best_idx = max(group_indices,
                       key=lambda i: len(name_data_list[i].get('cleaned_upper', '')))
        best     = name_data_list[best_idx]
        canon    = best.get('cleaned_upper', '')

        # Gather all AND/PRIVATE/LIMITED words from all members
        all_cleaned = [name_data_list[i].get('cleaned_upper', '') for i in group_indices]
        needed      = _merge_andpvtltd_words(all_cleaned)
        present     = set(w for w in canon.split() if w in needed)
        missing     = needed - present

        # Insert missing words into canon at natural positions
        words = canon.split()
        # PRIVATE and AND go before LIMITED; add at end if unclear
        for mw in sorted(missing):
            if mw == "AND":
                # Try to insert between the first and second word if > 1 word
                if len(words) >= 2:
                    words.insert(1, "AND")
                else:
                    words.append("AND")
            else:
                words.append(mw)

        # Re-normalise (singular) and title-case
        norm = normalize_words_in_name(' '.join(words))
        return norm.strip()

    # ── Standard PRIVATE_LIMITED_FAMILY rule ─────────────────────────────────
    forced = None
    if family == "PRIVATE_LIMITED_FAMILY":
        has_private = any(
            name_data_list[i].get('legal_suffix') == "PRIVATE LIMITED"
            for i in group_indices
        )
        forced = "PRIVATE LIMITED" if has_private else "LIMITED"

    if forced:
        tmp = {**primary, 'legal_suffix': forced}
        return generate_canonical(tmp)

    return generate_canonical(primary)


def format_canonical_name(canonical: str) -> str:
    return canonical.title() if canonical else ""

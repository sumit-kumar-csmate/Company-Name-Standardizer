"""Canonical name generator — produces the final standardised output name."""

from company_normalizer.processors.singular_plural_handler import normalize_words_in_name


def generate_canonical(name_data: dict) -> str:
    base   = name_data.get('base_name', '')
    suffix = name_data.get('legal_suffix', '')
    if not base:
        return ""
    norm = normalize_words_in_name(base)
    return f"{norm} {suffix}".strip() if suffix else norm.strip()


# ══════════════════════════════════════════════════════════════════════════════
# CANONICAL NAME QUALITY SCORER
# ══════════════════════════════════════════════════════════════════════════════

def _quality_score(name_data: dict) -> tuple:
    """
    Score a name_data entry on 8 quality dimensions.
    Higher score = better canonical candidate.

    Returns a tuple so that ties are broken deterministically.

    Scoring dimensions (each is 0 or 1, except word_count which can be > 1):

      1. has_legal_suffix      — Has a proper legal suffix (Pvt Ltd, Limited etc.)
                                 A name with a suffix is more complete.
      2. suffix_is_full        — Suffix is the full form "PRIVATE LIMITED" vs "LIMITED"
                                 (more complete suffix = better)
      3. has_no_brackets       — No parentheses in the cleaned name (bracket content
                                 is usually an abbreviation like "(I)" or "(P)")
      4. no_single_letter_word — No isolated single-letter word in the base name
                                 (e.g. "A" from "(A)" — usually less complete)
      5. word_count            — More words in the base name = more complete
                                 (e.g. "Acme Chemicals India" > "Acme Chemicals")
      6. no_trailing_artifact  — Does not end with a stray number or abbreviation
                                 that looks like an address artifact
      7. spelt_out_suffix      — Suffix is already in long form (not an abbreviation)
                                 This overlaps with suffix_is_full but catches
                                 "Corp" vs "Corporation" etc.
      8. base_char_length      — Longer character count in base name = more complete
                                 (tiebreaker so "India" beats "I")
    """
    base    = name_data.get('base_name', '').upper()
    suffix  = name_data.get('legal_suffix', '') or ''
    cleaned = name_data.get('cleaned_upper', '').upper()

    # 1. Has a legal suffix at all
    has_suffix = 1 if suffix.strip() else 0

    # 2. Suffix completeness: "PRIVATE LIMITED" > "LIMITED" > "LTD" etc.
    suffix_score = 0
    if 'PRIVATE LIMITED' in suffix.upper():
        suffix_score = 3
    elif 'LIMITED' in suffix.upper():
        suffix_score = 2
    elif suffix.strip():
        suffix_score = 1

    # 3. No parentheses in the full cleaned name
    has_no_brackets = 0 if ('(' in cleaned or ')' in cleaned) else 1

    # 4. No isolated single-letter words in base (e.g. "A", "I", "P")
    base_words = base.split()
    no_single_letter = 1 if not any(len(w) == 1 for w in base_words) else 0

    # 5. Word count in base name (more = more complete)
    word_count = len(base_words)

    # 6. No trailing artifact — last word is not a single digit or short abbrev
    no_artifact = 1
    if base_words:
        last = base_words[-1]
        if last.isdigit() or (len(last) <= 2 and not last.isalpha()):
            no_artifact = 0

    # 7. Suffix already in long-form (not abbreviated)
    #    Penalise if suffix contains a typical abbreviation
    abbrev_suffixes = {'PVT', 'LTD', 'INC', 'CORP', 'CO', 'MFG'}
    spelt_out = 1 if not any(a in suffix.upper().split() for a in abbrev_suffixes) else 0

    # 8. Character length of the base name (tiebreaker)
    base_len = len(base.replace(' ', ''))

    return (
        has_suffix,         # primary: prefer names with a legal suffix
        suffix_score,       # secondary: prefer more complete suffixes
        has_no_brackets,    # tertiary: prefer no brackets
        no_single_letter,   # then: prefer no single-letter words
        word_count,         # then: prefer more words
        no_artifact,        # then: prefer no trailing artifact
        spelt_out,          # then: prefer spelled-out suffix
        base_len,           # finally: prefer longer base text (character tiebreaker)
    )


def _elect_primary(name_data_list: list, group_indices: list) -> int:
    """
    Return the index of the best-quality member in a merge group.
    Uses _quality_score — falls back to first index if group is empty.
    """
    if not group_indices:
        return 0
    return max(group_indices, key=lambda i: _quality_score(name_data_list[i]))


# ══════════════════════════════════════════════════════════════════════════════


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

    The canonical member is now elected by QUALITY SCORE, not by row order.
    The member with the highest quality score (most complete name) becomes
    the canonical representative.

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

    # ── Elect the best-quality primary (replaces always using [0]) ────────────
    best_idx = _elect_primary(name_data_list, group_indices)
    primary  = name_data_list[best_idx]
    family   = primary.get('legal_family')

    # ── AND/PVT/LTD merge canonical ──────────────────────────────────────────
    if merge_reason == "AND_PVT_LTD_ONLY":
        # Pick the member whose cleaned text is longest (most complete)
        longest_idx = max(group_indices,
                          key=lambda i: len(name_data_list[i].get('cleaned_upper', '')))
        best        = name_data_list[longest_idx]
        canon       = best.get('cleaned_upper', '')

        # Gather all AND/PRIVATE/LIMITED words from all members
        all_cleaned = [name_data_list[i].get('cleaned_upper', '') for i in group_indices]
        needed      = _merge_andpvtltd_words(all_cleaned)
        present     = set(w for w in canon.split() if w in needed)
        missing     = needed - present

        # Insert missing words into canon at natural positions
        words = canon.split()
        for mw in sorted(missing):
            if mw == "AND":
                inserted = False
                for c_name in all_cleaned:
                    w_parts = c_name.split()
                    if "AND" in w_parts:
                        and_idx = w_parts.index("AND")
                        if and_idx > 0:
                            prev_w = w_parts[and_idx - 1]
                            if prev_w in words:
                                words.insert(words.index(prev_w) + 1, "AND")
                                inserted = True
                                break
                if not inserted:
                    if len(words) >= 2:
                        words.insert(1, "AND")
                    else:
                        words.append("AND")
            else:
                words.append(mw)

        norm = normalize_words_in_name(' '.join(words))
        return norm.strip()

    # ── Standard PRIVATE_LIMITED_FAMILY rule ─────────────────────────────────
    active_family = family
    if not active_family:
        families = [name_data_list[i].get('legal_family') for i in group_indices if name_data_list[i].get('legal_family')]
        if families:
            active_family = families[0]

    forced = None
    if active_family == "PRIVATE_LIMITED_FAMILY":
        has_private = any(
            name_data_list[i].get('legal_suffix') == "PRIVATE LIMITED"
            for i in group_indices
        )
        forced = "PRIVATE LIMITED" if has_private else "LIMITED"
    elif not family and active_family:
        for i in group_indices:
            sfx = name_data_list[i].get('legal_suffix')
            if sfx:
                forced = sfx
                break

    if forced:
        tmp = {**primary, 'legal_suffix': forced}
        return generate_canonical(tmp)

    return generate_canonical(primary)


def format_canonical_name(canonical: str) -> str:
    return canonical.title() if canonical else ""

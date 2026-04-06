"""
Merge engine — combines all business rules to decide if two names can be merged.

Merge is allowed when ALL of these pass:
  1. Legal suffix families are compatible
  2. No functional descriptor conflict
  3. Base names are identical, OR differ only by word order, OR by approved singular/plural
  4. Geographic terms allow merge

Special rule (Medium confidence):
  If two names are identical in every word EXCEPT that one has "and", "private",
  or "limited" and the other lacks it, they are merged and flagged as Medium confidence.
  The canonical name includes all such words (and + private + limited as applicable).

Space-only rule (High confidence):
  If two cleaned names are identical once all spaces are removed, they merge normally
  (one has extra spaces between characters).
"""

from company_normalizer.processors.legal_suffix_normalizer  import suffixes_can_merge
from company_normalizer.processors.descriptor_checker       import descriptors_allow_merge
from company_normalizer.processors.geographic_matcher       import geography_allows_merge
from company_normalizer.processors.singular_plural_handler  import names_differ_only_by_approved_pairs, normalize_words_in_name
from company_normalizer.processors.word_order_normalizer    import names_are_word_order_variants

# Words removed as substrings when computing the "core key" for matching
_REMOVABLE_SUBSTRINGS = ['PRIVATE', 'LIMITED', 'AND']


def _core_key(name: str) -> str:
    """
    Core comparison key:
      1. Normalize singular/plural words
      2. Uppercase
      3. Remove all spaces
      4. Strip PRIVATE / LIMITED / AND as substrings (handles both whole-word
         and embedded cases, e.g. 'Salesprivate' → core same as 'Sales Private')
    """
    s = normalize_words_in_name(name).upper().replace(' ', '')
    for w in _REMOVABLE_SUBSTRINGS:
        s = s.replace(w, '')
    return s


def _names_differ_only_by_andpvtltd(name1: str, name2: str) -> bool:
    """
    Return True if name1 and name2 share the same core after removing
    AND / PRIVATE / LIMITED (including when embedded, e.g. 'Salesprivate')
    and all spaces.  The names must not already be identical.
    """
    if not name1 or not name2:
        return False
    k1 = _core_key(name1)
    k2 = _core_key(name2)
    if not k1 or not k2:
        return False
    return k1 == k2 and name1.upper() != name2.upper()


def _anagrams_ignoring_andpvtltd(name1: str, name2: str) -> bool:
    """
    Return True if name1 and name2 contain exactly the same words 
    (in any order) after ignoring 'AND', 'PRIVATE', 'LIMITED'.
    Handles cases where word order differs AND a suffix word is missing.
    """
    if not name1 or not name2:
        return False
    w1 = {w for w in normalize_words_in_name(name1).upper().split() if w not in _REMOVABLE_SUBSTRINGS}
    w2 = {w for w in normalize_words_in_name(name2).upper().split() if w not in _REMOVABLE_SUBSTRINGS}
    return bool(w1) and w1 == w2


def _names_differ_only_by_spaces(name1: str, name2: str) -> bool:
    """
    Return True if names are identical after removing all spaces
    (one has extra/different spacing between characters — no AND/PVT/LTD involved).
    """
    if not name1 or not name2:
        return False
    return (name1.upper().replace(' ', '') == name2.upper().replace(' ', '')
            and name1.upper() != name2.upper())


def can_merge(d1: dict, d2: dict, conflict_bases: set = None):
    """
    Returns (can_merge: bool, reason: str).
    reason may include 'AND_PVT_LTD_ONLY', 'SPACE_ONLY', or 'MISSING_SUFFIX' as merge sub-reasons.
    """
    conflict_bases = conflict_bases or set()
    f1, f2 = d1.get('legal_family'), d2.get('legal_family')

    # Rule 1: Legal families
    if f1 and f2:
        if not suffixes_can_merge(f1, f2):
            return False, "Legal family mismatch"
    elif f1 or f2:
        # One has a suffix, other doesn't.
        # Check global conflicts: if this base name is associated with multiple
        # distinct suffixes across the dataset, we cannot safely merge the suffix-less version.
        b1 = d1.get('base_name', '')
        b2 = d2.get('base_name', '')
        if (b1 and b1 in conflict_bases) or (b2 and b2 in conflict_bases):
            return False, "Global suffix conflict blocks missing-suffix merge"
        
        # If no global conflict, we let it fall through to Rule 3 (base name check).
        # This safely enables universal missing-suffix matching for ALL suffix types.
        pass

    # Rule 2: Functional descriptors
    if not descriptors_allow_merge(d1.get('descriptors', set()), d2.get('descriptors', set())):
        return False, "Functional descriptor conflict"

    # Rule 3: Base name comparison
    b1, b2 = d1.get('base_name', ''), d2.get('base_name', '')

    # Space-only difference (high confidence merge)
    if _names_differ_only_by_spaces(b1, b2):
        return True, "SPACE_ONLY"

    if b1 != b2:
        # Check word-order or approved singular/plural
        if names_are_word_order_variants(b1, b2) or names_differ_only_by_approved_pairs(b1, b2):
            pass  # OK — continue to geography check
        else:
            # AND/PRIVATE/LIMITED difference on base names
            if _names_differ_only_by_andpvtltd(b1, b2) or _anagrams_ignoring_andpvtltd(b1, b2):
                # Check geography before confirming
                if not geography_allows_merge(d1.get('geography', set()), d2.get('geography', set())):
                    return False, "Geographic mismatch"
                return True, "AND_PVT_LTD_ONLY"
            # Try full cleaned names (covers cases where suffix is part of AND/PVT/LTD words)
            c1 = d1.get('cleaned_upper', b1)
            c2 = d2.get('cleaned_upper', b2)
            if _names_differ_only_by_andpvtltd(c1, c2) or _anagrams_ignoring_andpvtltd(c1, c2):
                if not geography_allows_merge(d1.get('geography', set()), d2.get('geography', set())):
                    return False, "Geographic mismatch"
                return True, "AND_PVT_LTD_ONLY"
            return False, "Base names differ"

    # Rule 4: Geography
    if not geography_allows_merge(d1.get('geography', set()), d2.get('geography', set())):
        return False, "Geographic mismatch"

    return True, "All rules align"


def build_merge_groups(name_data_list: list) -> list:
    """
    Group mergeable names using Union-Find.
    Returns list of groups (each a list of indices).
    Each group dict includes the list of original indices and the merge_reason
    that applies across the group.
    """
    n = len(name_data_list)
    
    # 1. Pre-scan for global suffix conflicts
    base_to_families = {}
    for d in name_data_list:
        base = d.get('base_name')
        if not base:
            continue
        fam = d.get('legal_family')
        if fam:
            base_to_families.setdefault(base, set()).add(fam)
            
    conflict_bases = set()
    for base, families in base_to_families.items():
        if len(families) > 1:
            conflict_bases.add(base)

    # 2. Union-Find merge
    parent = list(range(n))
    reason_map: dict = {}   # edge (i, j) → reason

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j, reason):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[rj] = ri
            # Propagate the "weaker" (more uncertain) reason upward
            existing = reason_map.get(ri, "All rules align")
            if reason == "AND_PVT_LTD_ONLY" or existing == "AND_PVT_LTD_ONLY":
                reason_map[ri] = "AND_PVT_LTD_ONLY"
            else:
                reason_map[ri] = existing

    for i in range(n):
        for j in range(i + 1, n):
            ok, reason = can_merge(name_data_list[i], name_data_list[j], conflict_bases)
            if ok:
                union(i, j, reason)

    groups: dict = {}
    for i in range(n):
        root = find(i)
        groups.setdefault(root, []).append(i)

    # Attach merge_reason to each group as a list of (indices, reason)
    result = []
    for root, indices in groups.items():
        result.append({
            'indices':      indices,
            'merge_reason': reason_map.get(root, "All rules align"),
        })
    return result

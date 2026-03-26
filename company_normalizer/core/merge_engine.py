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

from ..processors.legal_suffix_normalizer  import suffixes_can_merge
from ..processors.descriptor_checker       import descriptors_allow_merge
from ..processors.geographic_matcher       import geography_allows_merge
from ..processors.singular_plural_handler  import names_differ_only_by_approved_pairs
from ..processors.word_order_normalizer    import names_are_word_order_variants

# Words removed as substrings when computing the "core key" for matching
_REMOVABLE_SUBSTRINGS = ['PRIVATE', 'LIMITED', 'AND']


def _core_key(name: str) -> str:
    """
    Core comparison key:
      1. Uppercase
      2. Remove all spaces
      3. Strip PRIVATE / LIMITED / AND as substrings (handles both whole-word
         and embedded cases, e.g. 'Salesprivate' → core same as 'Sales Private')
    """
    s = name.upper().replace(' ', '')
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


def _names_differ_only_by_spaces(name1: str, name2: str) -> bool:
    """
    Return True if names are identical after removing all spaces
    (one has extra/different spacing between characters — no AND/PVT/LTD involved).
    """
    if not name1 or not name2:
        return False
    return (name1.upper().replace(' ', '') == name2.upper().replace(' ', '')
            and name1.upper() != name2.upper())


def can_merge(d1: dict, d2: dict):
    """
    Returns (can_merge: bool, reason: str).
    reason may include 'AND_PVT_LTD_ONLY' or 'SPACE_ONLY' as merge sub-reasons.
    """
    f1, f2 = d1.get('legal_family'), d2.get('legal_family')

    # Rule 1: Legal families
    if f1 and f2:
        if not suffixes_can_merge(f1, f2):
            return False, "Legal family mismatch"
    elif f1 or f2:
        # Special: one has suffix, other doesn't — allowed if the "missing"
        # suffix is accounted for by the AND/PVT/LTD word rule on the full name
        c1 = d1.get('cleaned_upper', '')
        c2 = d2.get('cleaned_upper', '')
        if not _names_differ_only_by_andpvtltd(c1, c2):
            return False, "Legal suffix presence mismatch"

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
            if _names_differ_only_by_andpvtltd(b1, b2):
                # Check geography before confirming
                if not geography_allows_merge(d1.get('geography', set()), d2.get('geography', set())):
                    return False, "Geographic mismatch"
                return True, "AND_PVT_LTD_ONLY"
            # Try full cleaned names (covers cases where suffix is part of AND/PVT/LTD words)
            c1 = d1.get('cleaned_upper', b1)
            c2 = d2.get('cleaned_upper', b2)
            if _names_differ_only_by_andpvtltd(c1, c2):
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
    that applies across the group (AND_PVT_LTD_ONLY takes precedence).
    """
    n      = len(name_data_list)
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
            ok, reason = can_merge(name_data_list[i], name_data_list[j])
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

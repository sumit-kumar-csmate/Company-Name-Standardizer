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
# Words removed only as whole words (to prevent 'CO' from stripping from 'COFCO')
_REMOVABLE_WHOLE_WORDS = ['CO']


def _core_key(name: str) -> str:
    """
    Core comparison key:
      1. Normalize singular/plural words
      2. Uppercase
      3. Remove whole words like 'CO' safely
      4. Remove all spaces
      5. Strip PRIVATE / LIMITED / AND as substrings (handles both whole-word
         and embedded cases, e.g. 'Salesprivate' → core same as 'Sales Private')
    """
    s = normalize_words_in_name(name, apply_synonyms=True).upper()
    words = [w for w in s.split() if w not in _REMOVABLE_WHOLE_WORDS]
    s = "".join(words)
    
    for w in _REMOVABLE_SUBSTRINGS:
        s = s.replace(w, '')
    return s


def _names_differ_only_by_andpvtltd(name1: str, name2: str) -> bool:
    """
    Return True if name1 and name2 share the same core after removing
    AND / PRIVATE / LIMITED / CO (including when embedded, e.g. 'Salesprivate')
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
    (in any order) after ignoring 'AND', 'PRIVATE', 'LIMITED', 'CO'.
    Handles cases where word order differs AND a suffix word is missing.
    """
    if not name1 or not name2:
        return False
    skip = set(_REMOVABLE_SUBSTRINGS + _REMOVABLE_WHOLE_WORDS)
    w1 = {w for w in normalize_words_in_name(name1, apply_synonyms=True).upper().split() if w not in skip}
    w2 = {w for w in normalize_words_in_name(name2, apply_synonyms=True).upper().split() if w not in skip}
    return bool(w1) and w1 == w2


def _stripped(name: str) -> str:
    """Helper to remove spaces and uppercase a string for structural comparison."""
    return name.upper().replace(' ', '') if name else ""


def _names_differ_only_by_spaces(name1: str, name2: str) -> bool:
    """
    Return True if names are identical after removing all spaces
    (one has extra/different spacing between characters — no AND/PVT/LTD involved).
    """
    if not name1 or not name2:
        return False
    return (name1.upper().replace(' ', '') == name2.upper().replace(' ', '')
            and name1.upper() != name2.upper())


def can_merge(d1: dict, d2: dict, base_to_families: dict = None):
    """
    Returns (can_merge: bool, reason: str).
    reason may include 'AND_PVT_LTD_ONLY', 'SPACE_ONLY', or 'MISSING_SUFFIX' as merge sub-reasons.
    """
    base_to_families = base_to_families or {}
    f1, f2 = d1.get('legal_family'), d2.get('legal_family')

    # Rule 1: Legal families
    if f1 and f2:
        if suffixes_can_merge(f1, f2):
            pass  # normally allowed
        else:
            # Hierarchical Suffix logic
            fam_set = {f1, f2}
            b1 = d1.get('base_name', '')
            my_fams = base_to_families.get(_stripped(b1), set())
            if fam_set == {"LIMITED_FAMILY", "PRIVATE_LIMITED_FAMILY"}:
                if "CO_LIMITED_FAMILY" not in my_fams:
                    pass  # ALLOW merge of Limited and Private Limited
                else:
                    return False, "Hierarchical mismatch (Co Limited present)"
            elif fam_set == {"LIMITED_FAMILY", "CO_LIMITED_FAMILY"}:
                if "PRIVATE_LIMITED_FAMILY" not in my_fams:
                    pass  # ALLOW merge of Limited and Co Limited
                else:
                    return False, "Hierarchical mismatch (Private Limited present)"
            else:
                return False, "Legal family mismatch"
    elif f1 or f2:
        # One has a suffix, other doesn't.
        f_present = f1 or f2
        b1, b2 = d1.get('base_name', ''), d2.get('base_name', '')
        b_target = b1 if b1 else b2
        my_fams = base_to_families.get(_stripped(b_target), set())
        
        if len(my_fams) > 1:
            if my_fams == {"LIMITED_FAMILY", "PRIVATE_LIMITED_FAMILY"} or my_fams == {"LIMITED_FAMILY", "CO_LIMITED_FAMILY"}:
                pass # not a conflict
            else:
                return False, "Global suffix conflict blocks missing-suffix merge"

    # Rule 1b: Space-only difference — checked BEFORE descriptors intentionally.
    # If two names are identical once spaces are stripped, the descriptor difference
    # is purely a spacing artefact (e.g. BIOENERGY vs BIO ENERGY), not a real conflict.
    b1, b2 = d1.get('base_name', ''), d2.get('base_name', '')
    if _names_differ_only_by_spaces(b1, b2):
        return True, "SPACE_ONLY"

    # Rule 2: Functional descriptors
    if not descriptors_allow_merge(d1.get('descriptors', set()), d2.get('descriptors', set())):
        return False, "Functional descriptor conflict"

    # Rule 3: Base name comparison
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



def _get_blocking_keys(d: dict) -> list:
    """
    Generate all blocking keys for one name_data record.

    Keys are 2-tuples (namespace, hashable_value) so different key types
    cannot accidentally collide with each other.

    Key #1  exact base_name              — covers identical base names
    Key #2  frozenset(normalized words)  — covers word-order + singular/plural variants
    Key #3  _core_key(base_name)         — covers AND/PVT/LTD + space-only diffs
    Key #4  frozenset(normalized - SKIP) — covers anagram + AND/PVT/LTD + plural
    Key #5  _core_key(cleaned_upper)     — cleaned_upper fallback for #3
    Key #6  frozenset(cleaned - SKIP)    — cleaned_upper fallback for #4
    """
    from company_normalizer.processors.singular_plural_handler import normalize_words_in_name

    SKIP = set(_REMOVABLE_SUBSTRINGS + _REMOVABLE_WHOLE_WORDS)
    keys = []

    base    = (d.get('base_name')    or '').strip()
    cleaned = (d.get('cleaned_upper') or '').strip()

    if base:
        base_up = base.upper()

        # Key 1: exact upper base name
        keys.append(('base', base_up))

        # Key 2: frozenset of singular/plural-normalized words (order-independent)
        norm_base = normalize_words_in_name(base, apply_synonyms=True).upper().split()
        if norm_base:
            keys.append(('norm_fs', frozenset(norm_base)))

        # Key 3: core key strips AND/PVT/LTD + spaces
        ck = _core_key(base)
        if ck:
            keys.append(('core', ck))

        # Key 4: frozenset of normalized words excluding AND/PVT/LTD/CO
        norm_base_set = frozenset(w for w in norm_base if w not in SKIP)
        if norm_base_set:
            keys.append(('anagram', norm_base_set))

    if cleaned:
        # Key 5: core key of the full cleaned name (handles edge-case suffix overlap)
        ck_c = _core_key(cleaned)
        if ck_c:
            keys.append(('core_c', ck_c))

        # Key 6: frozenset of normalized cleaned words excluding SKIP
        norm_cleaned = normalize_words_in_name(cleaned, apply_synonyms=True).upper().split()
        norm_cleaned_set = frozenset(w for w in norm_cleaned if w not in SKIP)
        if norm_cleaned_set:
            keys.append(('anagram_c', norm_cleaned_set))

    return keys


def build_merge_groups(name_data_list: list) -> list:
    """
    Group mergeable names using Union-Find with Exact-Match Blocking.

    Instead of O(N²) brute-force comparisons, each record generates up to 6
    blocking keys. The Union-Find engine only compares pairs that share at least
    one key — guaranteed to include every pair that *could* pass can_merge(),
    because Rule 3 requires a key match for any merge to succeed.

    Returns list of group dicts (each has 'indices' and 'merge_reason') and
    the base_to_families pre-scan dict.
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
            base_to_families.setdefault(_stripped(base), set()).add(fam)

    # 2. Build blocking index: key -> list of row indices
    blocks: dict = {}
    for i, d in enumerate(name_data_list):
        for key in _get_blocking_keys(d):
            blocks.setdefault(key, []).append(i)

    # 3. Collect unique candidate pairs from all blocks
    candidate_pairs: set = set()
    for indices in blocks.values():
        for a in range(len(indices)):
            for b in range(a + 1, len(indices)):
                i, j = indices[a], indices[b]
                if i > j:
                    i, j = j, i
                candidate_pairs.add((i, j))

    # 4. Union-Find on candidate pairs only
    parent = list(range(n))
    reason_map: dict = {}

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j, reason):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[rj] = ri
            existing = reason_map.get(ri, "All rules align")
            if reason == "AND_PVT_LTD_ONLY" or existing == "AND_PVT_LTD_ONLY":
                reason_map[ri] = "AND_PVT_LTD_ONLY"
            elif reason == "SPACE_ONLY" or existing == "SPACE_ONLY":
                reason_map[ri] = "SPACE_ONLY"
            else:
                reason_map[ri] = existing

    for i, j in candidate_pairs:
        ok, reason = can_merge(name_data_list[i], name_data_list[j], base_to_families)
        if ok:
            union(i, j, reason)

    # 5. Build output groups
    groups: dict = {}
    for i in range(n):
        root = find(i)
        groups.setdefault(root, []).append(i)

    result = []
    for root, indices in groups.items():
        result.append({
            'indices':      indices,
            'merge_reason': reason_map.get(root, "All rules align"),
        })
    return result, base_to_families


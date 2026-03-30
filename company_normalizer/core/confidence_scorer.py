from company_normalizer.config.shared import spell as _spell

# Dictionary for typo detection — helps flag names that need AI verification
# (Imported as a shared singleton — no second dictionary load on startup)

# Pre-computed prefix set for fast short-circuit before spell.correction().
# Only words whose first 3 chars match an industry term prefix go through
# the expensive edit-distance check.
_CORE_INDUSTRY_TERMS = {
    "polymer", "chemical", "industry", "service", "technology", "solution",
    "enterprise", "project", "resource", "holding", "venture", "commodity",
    "plastic", "metal", "steel", "power", "energy", "logistic", "transport",
    "construction", "building", "development", "infrastructure", "agro", "pharma",
    "health", "medical", "textile", "fabric", "system", "product", "engineering"
}
_INDUSTRY_PREFIXES = frozenset(term[:3] for term in _CORE_INDUSTRY_TERMS)


def calculate_confidence(name_data: dict, merge_reason: str = "All rules align"):
    """
    Returns (confidence_level, review_flag).
    High → NO review, Medium/Low → YES review.

    Special: AND_PVT_LTD_ONLY merge reason forces Medium confidence.
    """
    # AND/PVT/LTD-only difference → always Medium regardless of other signals
    if merge_reason == "AND_PVT_LTD_ONLY":
        return "Medium", "YES"

    score = 0
    reasons = []

    if name_data.get('legal_family') in [None, ""] and name_data.get('legal_suffix', '') != '':
        score += 2
        reasons.append("Unknown legal suffix")

    if name_data.get('legal_suffix', '') == '':
        score += 1
        reasons.append("Missing legal suffix")

    if name_data.get('removed_address'):
        score += 1
        reasons.append("Address removed")

    if len(name_data.get('removed_prefixes', [])) > 3:
        score += 1
        reasons.append("Too many prefixes")

    # Flag single-character words (like "I", "S") to aggressively trigger AI verification
    raw_cleaned = str(name_data.get('cleaned_upper', ''))
    clean_words = raw_cleaned.split()
    if any(len(w) == 1 and w.isalpha() and w not in ["A", "&", "O"] for w in clean_words):
        score += 1
        reasons.append("Single-character word detected")

    # Flag missing spaces around common legal terms (e.g. INDIAPRIVATE, PVTLTD)
    merged_suffixes = ["PRIVATE", "LIMITED", "PVT", "LTD", "INC", "CORP", "LLC"]
    for w in clean_words:
        if w == "UNLIMITED":
            continue
        for kw in merged_suffixes:
            if w.endswith(kw) and len(w) > len(kw):
                score += 1
                reasons.append(f"Merged keyword detected: {kw} inside {w}")
                break
            if kw in ["PVT", "LTD"] and w.startswith(kw) and len(w) > len(kw):
                score += 1
                reasons.append(f"Merged keyword detected: {kw} inside {w}")
                break

    # SMART TYPO DETECTION: Only flag unknown words if they look like industry terms!
    # This prevents brand names like "Adiva" or "Aglo" from wasting AI tokens.
    unknowns = _spell.unknown([w.lower() for w in clean_words if len(w) > 3])
    found_typos = []
    for unk in unknowns:
        # ── Optimization 3: Prefix short-circuit ─────────────────────────────
        # spell.correction() is expensive (edit-distance against full dictionary).
        # Skip it entirely if the word's first 3 chars don't match ANY industry
        # term prefix — a near-zero-cost O(1) frozenset lookup.
        if unk[:3] not in _INDUSTRY_PREFIXES:
            continue
        corr = _spell.correction(unk)
        if corr and corr.lower() in _CORE_INDUSTRY_TERMS:
            found_typos.append(f"{unk}->{corr}")

    if found_typos:
        score += 1
        reasons.append(f"Likely industry typos: {', '.join(found_typos)}")

    if score == 0:
        return "High", "NO"
    elif score <= 2:
        return "Medium", "YES"
    else:
        return "Low", "YES"


def get_decision_source() -> str:
    return "RULE"

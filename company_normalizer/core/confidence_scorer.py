from spellchecker import SpellChecker

# Dictionary for typo detection — helps flag names that need AI verification
_spell = SpellChecker()

# Common industry terms to watch for typos. 
# We ONLY flag a word as a typo if it looks like one of these. 
# This saves AI tokens by ignoring unique brand names like "Adiva".
_CORE_INDUSTRY_TERMS = {
    "polymer", "chemical", "industry", "service", "technology", "solution",
    "enterprise", "project", "resource", "holding", "venture", "commodity",
    "plastic", "metal", "steel", "power", "energy", "logistic", "transport",
    "construction", "building", "development", "infrastructure", "agro", "pharma",
    "health", "medical", "textile", "fabric", "system", "product", "engineering"
}

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

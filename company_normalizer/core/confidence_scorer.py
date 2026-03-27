"""Confidence scorer — assigns High / Medium / Low and a Review Flag."""


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
    clean_words = name_data.get('cleaned_upper', '').split()
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

    if score == 0:
        return "High", "NO"
    elif score <= 2:
        return "Medium", "YES"
    else:
        return "Low", "YES"


def get_decision_source() -> str:
    return "RULE"

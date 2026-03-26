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

    if name_data.get('legal_family') is None and name_data.get('legal_suffix', '') != '':
        score += 2          # unknown / unrecognised suffix
    if name_data.get('legal_suffix', '') == '':
        score += 1          # no suffix → slightly uncertain
    if name_data.get('removed_address', ''):
        score += 1          # address was stripped
    if len(name_data.get('removed_prefixes', [])) > 2:
        score += 1          # many prefixes = unusual structure

    if score == 0:
        return "High", "NO"
    elif score <= 2:
        return "Medium", "YES"
    else:
        return "Low", "YES"


def get_decision_source() -> str:
    return "RULE"

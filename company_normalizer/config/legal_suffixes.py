"""
Legal suffix normalisation configuration.
Each suffix maps to (canonical_form, family_id).
Suffixes in the same family can be merged into one canonical name.
"""

PRIVATE_LIMITED_FAMILY = "PRIVATE_LIMITED_FAMILY"
CORPORATE_FAMILY       = "CORPORATE_FAMILY"
EUROPEAN_FAMILY        = "EUROPEAN_FAMILY"
CO_LIMITED_FAMILY      = "CO_LIMITED_FAMILY"
MEXICAN_LEGAL_FAMILY   = "MEXICAN_LEGAL_FAMILY"
CV_FAMILY              = "CV_FAMILY"

NEVER_MERGE_SUFFIXES = [
    "LLC", "INC", "INCORPORATED", "GMBH", "BV", "SA", "NV",
    "KK", "AG", "AB", "OY", "SPA",
]

LEGAL_SUFFIX_MAP = {
    # Private + Limited variants → PRIVATE LIMITED
    "PRIVATE LIMITED": ("PRIVATE LIMITED", PRIVATE_LIMITED_FAMILY),
    "PVT LTD":         ("PRIVATE LIMITED", PRIVATE_LIMITED_FAMILY),
    "PVT. LTD.":       ("PRIVATE LIMITED", PRIVATE_LIMITED_FAMILY),
    "PVT LTD.":        ("PRIVATE LIMITED", PRIVATE_LIMITED_FAMILY),
    "PVT. LTD":        ("PRIVATE LIMITED", PRIVATE_LIMITED_FAMILY),
    "PVT LIMITED":     ("PRIVATE LIMITED", PRIVATE_LIMITED_FAMILY),
    "PRIVATE LTD":     ("PRIVATE LIMITED", PRIVATE_LIMITED_FAMILY),
    "PRIVATE LTD.":    ("PRIVATE LIMITED", PRIVATE_LIMITED_FAMILY),
    "PTY LTD":         ("PRIVATE LIMITED", PRIVATE_LIMITED_FAMILY),
    "PTY. LTD.":       ("PRIVATE LIMITED", PRIVATE_LIMITED_FAMILY),
    "PTY LTD.":        ("PRIVATE LIMITED", PRIVATE_LIMITED_FAMILY),
    "PTY. LTD":        ("PRIVATE LIMITED", PRIVATE_LIMITED_FAMILY),
    "PTE LTD":         ("PRIVATE LIMITED", PRIVATE_LIMITED_FAMILY),
    "PTE. LTD.":       ("PRIVATE LIMITED", PRIVATE_LIMITED_FAMILY),
    "PTE LTD.":        ("PRIVATE LIMITED", PRIVATE_LIMITED_FAMILY),
    "PTE. LTD":        ("PRIVATE LIMITED", PRIVATE_LIMITED_FAMILY),
    "PVT":             ("PRIVATE",         PRIVATE_LIMITED_FAMILY),
    "PTY":             ("PRIVATE",         PRIVATE_LIMITED_FAMILY),
    "PTE":             ("PRIVATE",         PRIVATE_LIMITED_FAMILY),
    # Limited only (no "Private") — same family, canonical = LIMITED
    "LIMITED": ("LIMITED", PRIVATE_LIMITED_FAMILY),
    "LTD":     ("LIMITED", PRIVATE_LIMITED_FAMILY),
    "LTD.":    ("LIMITED", PRIVATE_LIMITED_FAMILY),
    # CO. LTD. family
    "CO LTD":   ("CO LIMITED", CO_LIMITED_FAMILY),
    "CO. LTD":  ("CO LIMITED", CO_LIMITED_FAMILY),
    "CO. LTD.": ("CO LIMITED", CO_LIMITED_FAMILY),
    "CO LTD.":  ("CO LIMITED", CO_LIMITED_FAMILY),
    # Corporate family
    "CORP":        ("CORPORATION", CORPORATE_FAMILY),
    "CORP.":       ("CORPORATION", CORPORATE_FAMILY),
    "CORPORATION": ("CORPORATION", CORPORATE_FAMILY),
    # CV family
    "C V":  ("CV", CV_FAMILY),
    "C.V.": ("CV", CV_FAMILY),
    # European family
    "SARL": ("SARL", EUROPEAN_FAMILY),
    "SRL":  ("SARL", EUROPEAN_FAMILY),
    # Mexican legal forms
    "S DE RL DE CV":      ("S DE RL DE CV", MEXICAN_LEGAL_FAMILY),
    "S DE RL DE C V":     ("S DE RL DE CV", MEXICAN_LEGAL_FAMILY),
    "S.DE R.L DE C.V.":   ("S DE RL DE CV", MEXICAN_LEGAL_FAMILY),
    "S.DE R.L. DE C.V.":  ("S DE RL DE CV", MEXICAN_LEGAL_FAMILY),
    "S. DE R.L. DE C.V.": ("S DE RL DE CV", MEXICAN_LEGAL_FAMILY),
    "S DE R L DE C V":    ("S DE RL DE CV", MEXICAN_LEGAL_FAMILY),
}

# Add never-merge suffixes (each is its own family)
for _s in NEVER_MERGE_SUFFIXES:
    LEGAL_SUFFIX_MAP[_s]       = (_s, f"NEVER_MERGE_{_s}")
    LEGAL_SUFFIX_MAP[_s + "."] = (_s, f"NEVER_MERGE_{_s}")

# Normalise all keys to UPPERCASE
LEGAL_SUFFIX_MAP = {k.upper(): v for k, v in LEGAL_SUFFIX_MAP.items()}


def normalize_suffix(suffix: str):
    key = suffix.upper().strip()
    return LEGAL_SUFFIX_MAP.get(key, (suffix, None))


def get_all_suffixes():
    return list(LEGAL_SUFFIX_MAP.keys())

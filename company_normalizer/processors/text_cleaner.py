"""
Text cleaning module.

Pipeline (strict order):
  STEP 1 — Replace special characters with 4 spaces; replace & with "and"
  STEP 2 — Clean / Trim / Proper  (collapse whitespace, title-case)
  STEP 3 — Expand abbreviations:
              pvt  → Private     corp / corpn → Corporation
              ltd / ltda / limite → Limited       pte (with leading space) → Private
  STEP 4 — Clean / Trim / Proper again (normalise any spacing introduced)
"""

import re

# ── Step 3: Abbreviation expansions ──────────────────────────────────────────
# Applied AFTER the first clean/trim and BEFORE the second clean/trim.
# ORDER MATTERS — longer/more specific patterns first.
ABBREVIATION_MAP = [
    # Run-on typos missing a space (e.g., Chemicalprivate -> Chemical Private)
    (r'([A-Za-z]{2,})private\b', r'\g<1> Private'),
    (r'([A-Za-z]{2,})pvt\b',     r'\g<1> Private'),
    # Pvt / Pte / Priv variants → Private  (with optional dot, word-boundary)
    (r'\bPvt\.?\b',            'Private'),
    (r'\bPVT\.?\b',            'Private'),
    (r'\bPriv\b',              'Private'),
    (r'\bPRIV\b',              'Private'),
    # " pte" with leading space → " Private"  (space-sensitive per spec)
    (r'(?<= )Pte\.?\b',        'Private'),
    (r'(?<= )PTE\.?\b',        'Private'),
    # P LTD / P. LTD / P.LTD → Private Limited
    (r'\bP(?:\.\s*|\s+)(?:Ltd|Limited)\.?\b', 'Private Limited'),
    (r'\bP(?:\.\s*|\s+)(?:LTD|LIMITED)\.?\b', 'Private Limited'),
    # Ltd / Ltda / Limitada / Limiteda / Limite / Limi / Lim (end only) → Limited
    (r'\bLtda?\b\.?',          'Limited'),
    (r'\bLTDA?\b\.?',          'Limited'),
    (r'\bLimitada\b\.?',       'Limited'),
    (r'\bLIMITADA\b\.?',       'Limited'),
    (r'\bLimiteda\b\.?',       'Limited'),
    (r'\bLIMITEDA\b\.?',       'Limited'),
    (r'\bLimitad\s+a\b\.?',    'Limited'),
    (r'\bLIMITAD\s+A\b\.?',    'Limited'),
    (r'\bLimited\s+a\b\.?',    'Limited'),
    (r'\bLIMITED\s+A\b\.?',    'Limited'),
    (r'\bLimite\b',            'Limited'),
    (r'\bLIMITE\b',            'Limited'),
    (r'\bLimi\b',              'Limited'),
    (r'\bLIMI\b',              'Limited'),
    (r'\bLim\b$',              'Limited'),   # only when last word
    (r'\bLIM\b$',              'Limited'),   # only when last word
    # Ltd. (with dot) already covered above
    (r'\bLtd\.?\b',            'Limited'),
    (r'\bLTD\.?\b',            'Limited'),
    # Corp / Corpn → Corporation
    (r'\bCorpn?\.?\b',         'Corporation'),
    (r'\bCORPN?\.?\b',         'Corporation'),
    # Company → Co
    (r'\bCompany\b',           'Co'),
    (r'\bCOMPANY\b',           'Co'),
    # Other common abbreviations
    (r'\bMfg\.?\b',            'Manufacturing'),
    (r'\bMFG\.?\b',            'Manufacturing'),
    (r'\bMfrs\.?\b',           'Manufacturers'),
    (r'\bMFRS\.?\b',           'Manufacturers'),
    (r'\bIntl\.?\b',           'International'),
    (r'\bINTL\.?\b',           'International'),
    (r'\bBros\.?\b',           'Brothers'),
    (r'\bBROS\.?\b',           'Brothers'),
]

# Characters replaced with 4 spaces in Step 1
# Includes dot (.) — all these are expanded to 4 spaces so abbreviation
# expansion in Step 3 can still match whole-word patterns cleanly.
_SPECIAL_CHARS_RE = re.compile(r'[&/,;:\'"()\[\]!?_\\@#*~`|<>{}=+\-.]')


def _clean_trim_proper(text: str) -> str:
    """Collapse whitespace, strip, title-case."""
    text = ' '.join(text.split())
    return text.strip().title()


def clean_text(raw_name: str):
    """
    Clean and normalise a raw company name using the 4-step pipeline.

    Returns
    -------
    (cleaned_display, cleaned_upper) : tuple[str, str]
      cleaned_display — Title Case, for output column
      cleaned_upper   — UPPER CASE, for all rule-matching
    """
    if not raw_name or not isinstance(raw_name, str):
        return "", ""

    text = raw_name.strip()

    # Remove non-printable chars
    text = ''.join(c for c in text if c.isprintable())

    # ── STEP 0a: Alias Stripping ────────────────────────────────────────────
    # Strip "Trading As" (T/A, T A) or "Doing Business As" (DBA) if they appear
    # AFTER the start of the company name (requires preceding whitespace)
    text = re.sub(r'(?i)\s+\b(?:T/A|T\.?A\.?|D/B/A|DBA|TRADING AS|DOING BUSINESS AS)\b.*', '', text)

    # ── STEP 0b: Normalise hyphenated compound words ──────────────────────
    # Collapse "BIO-CHEM" -> "BIOCHEM", "BIO-ENERGY" -> "BIOENERGY" etc.
    # so that hyphenated and non-hyphenated variants normalise to the same token
    # BEFORE the global hyphen-to-spaces replacement fires in STEP 1.
    _COMPOUND_PREFIXES = (
        r'(?i)\b(bio|agro|chemo|petro|aero|hydro|electro|micro|macro|nano|poly|agri|pharma)'
        r'\s*-\s*'
    )
    text = re.sub(_COMPOUND_PREFIXES, lambda m: m.group(1), text)

    # ── STEP 1: Replace special chars with 4 spaces; & → "and" ──────────────
    text = text.replace('&', ' and ')
    text = _SPECIAL_CHARS_RE.sub('    ', text)

    # ── STEP 2: Clean / Trim / Proper ────────────────────────────────────────
    text = _clean_trim_proper(text)

    # ── STEP 3: Abbreviation expansions ──────────────────────────────────────
    for pattern, replacement in ABBREVIATION_MAP:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # ── STEP 4: Clean / Trim / Proper again ──────────────────────────────────
    text = _clean_trim_proper(text)

    cleaned_display = text
    cleaned_upper   = text.upper()

    return cleaned_display, cleaned_upper

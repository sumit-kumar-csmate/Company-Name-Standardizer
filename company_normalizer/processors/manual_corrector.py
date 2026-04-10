"""
Manual Corrector
================
Applies the WORD_CORRECTIONS dictionary from manual_corrections.py
to a company name string.

Matching is:
  - Case-insensitive
  - Whole-word only (so "JINAXIN" won't accidentally match inside "JINAXIN STEEL")

Applied as the FIRST step in process_single_name() so the corrected name
flows cleanly through all downstream rules.
"""

import re
from company_normalizer.config.manual_corrections import WORD_CORRECTIONS

# Build a pre-compiled pattern for each known wrong word (whole-word, case-insensitive)
_COMPILED: list[tuple[re.Pattern, str]] = [
    (re.compile(rf'\b{re.escape(wrong)}\b', re.IGNORECASE), correct)
    for wrong, correct in WORD_CORRECTIONS.items()
]


def apply_manual_corrections(name: str) -> str:
    """
    Replace all known misspelled words in *name* with their correct spellings.
    Returns the corrected string (unchanged if no matches).
    """
    if not name or not isinstance(name, str) or not _COMPILED:
        return name

    for pattern, correct in _COMPILED:
        name = pattern.sub(correct, name)

    return name

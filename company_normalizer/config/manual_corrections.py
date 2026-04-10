"""
Manual Word Corrections
=======================
A lookup table for known word-level misspellings found in trade data.

HOW TO USE:
  - Keys   : the WRONG spelling (case-insensitive, will be matched on whole words only).
  - Values : the CORRECT spelling to substitute in its place.

EXAMPLES:
  "JINAXIN"  -> "JIANXIN"   (letter transposition)
  "COFOC"    -> "COFCO"     (letter transposition)
  "SAMSUG"   -> "SAMSUNG"   (missing letter)

Add new entries below as you discover new misspellings in your data.
The processor applies these corrections BEFORE any other pipeline step,
so the corrected name flows cleanly through all downstream rules.
"""

WORD_CORRECTIONS: dict[str, str] = {
    # ── Add your corrections below ──────────────────────────────────────────
    # "WRONG_WORD": "CORRECT_WORD",

    "JINAXIN":  "JIANXIN",   # letter transposition seen in trade data
    "COFOC":    "COFCO",     # letter transposition seen in trade data
}

"""
Shared NLP singletons — initialized ONCE at startup.
All modules should import from here instead of creating their own instances.
This eliminates duplicate dictionary loads and reduces startup time + RAM usage.
"""

import inflect
from spellchecker import SpellChecker

# ── Single shared inflect engine ──────────────────────────────────────────────
engine = inflect.engine()

# ── Single shared SpellChecker instance ──────────────────────────────────────
spell = SpellChecker()

# Teach the dictionary about industry-specific jargon so they are allowed
# to be singularised. Without this, the safety net assumes weird words are
# brand names (like "Infosys").
_CUSTOM_INDUSTRY_WORDS = [
    "polyplastic",
    "agrochemical",
    "petrochemical",
    "technologie",   # For malformed variants if needed
]
spell.word_frequency.load_words(_CUSTOM_INDUSTRY_WORDS)

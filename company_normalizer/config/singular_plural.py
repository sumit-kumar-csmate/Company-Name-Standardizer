"""
Approved singular/plural word automated pairing using NLP.
Plural words are converted TO singular, not singular to plural.
Only valid dictionary words are converted to protect proper brand names.
"""

import inflect
from spellchecker import SpellChecker

_engine = inflect.engine()
_spell = SpellChecker()

# Teach the dictionary about industry-specific jargon so they are allowed to be singularised!
# Without this, the safety net assumes weird words are brand names (like "Infosys").
_CUSTOM_INDUSTRY_WORDS = [
    "polyplastic",
    "agrochemical", 
    "petrochemical",
    "technologie" # For malformed variants if needed
]
_spell.word_frequency.load_words(_CUSTOM_INDUSTRY_WORDS)

def normalize_word(word: str) -> str:
    """Return the canonical SINGULAR form if it's a valid dictionary word."""
    w_upper = word.upper().strip()
    if not w_upper:
        return ""
    
    # 1. Ask inflect for singular form (will return False if already singular)
    singular = _engine.singular_noun(word)
    
    # 2. If it's recognized as a plural and returned a singular
    if singular:
        # 3. Check if the singular form is a valid English word
        # pyspellchecker works in lowercase
        if _spell.known([str(singular).lower()]):
            return str(singular).upper()
            
    return w_upper

def is_approved_pair(word1: str, word2: str) -> bool:
    """Return True if word1 and word2 map to the same algorithmic singular form."""
    c1 = normalize_word(word1)
    c2 = normalize_word(word2)
    return c1 == c2 and c1 != ""

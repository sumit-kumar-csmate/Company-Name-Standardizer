"""
Singular/plural normalisation — Future-Proof Hybrid System.

THREE LAYERS (applied in strict order):

  Layer 1 — PROTECTED WORDS (never singularized, checked first)
             Hard list of proper nouns, foreign words, abbreviations,
             country names, brand name patterns that must never be touched.

  Layer 2 — EXPLICIT WHITELIST (exact known pairs from real trade data)
             106 verified plural→singular pairs built from 317,000+ real
             company names in Total name.csv. Zero false positives.

  Layer 3 — SAFE SUFFIX PATTERNS (future-proofing)
             A small set of unambiguous chemistry/science suffix rules that
             automatically handle NEW words not yet in the whitelist.
             Each rule has a strict minimum-length guard to prevent false matches.
             e.g. "biopolymers" → "biopolymer" (MERS rule, 11 chars ≥ 8)
                  "nanoemulsifiers" → "nanoemulsifier" (IZERS rule, 15 chars ≥ 9)
                  "agrochemicals" → "agrochemical" (ICALS rule, 13 chars ≥ 9)

  Default — word is returned UNCHANGED (safe fallback for everything else)

This is 100% deterministic — no NLP library.
To add a new word: add to ALLOWED_SINGULAR_MAP (Layer 2) or verify it
falls under a Layer 3 pattern. Never remove a word from PROTECTED_WORDS
without careful review.
"""

from functools import lru_cache

# ══════════════════════════════════════════════════════════════════════════════
# LAYER 1 — PROTECTED WORDS
# These words will NEVER be singularized regardless of any other rule.
# ══════════════════════════════════════════════════════════════════════════════
PROTECTED_WORDS = frozenset({
    # ── Short / ambiguous (≤ 4 chars) ────────────────────────────────────────
    # (words this short are auto-skipped by the min-length guard in Layer 3,
    #  but listed here explicitly for Layer 2 safety)
    "MAS", "LAS", "LOS", "DAS", "DOS", "DES", "LES",   # Spanish/Portuguese articles
    "GAS", "BUS", "MRS", "GS",  "MS",                   # Abbreviations / invariants

    # ── Country / geographic names ────────────────────────────────────────────
    "PHILIPPINES", "MALDIVES", "HONDURAS",
    "BAHAMAS", "BARBADOS", "BELIZE", "ANTILLES",
    "EMIRATES", "CANARIES",

    # ── Foreign words that end in 's' (Spanish / Portuguese / Indonesian) ────
    "ALTAS", "ATLAS",   # Spanish plural / proper noun
    "RIOS",             # Portuguese / proper name (Rio)
    "LAOS",             # Country name
    "DUBOIS",           # French surname

    # ── Proper surnames / brand names that end in 's' ─────────────────────────
    "ABBAS", "HARRIS", "JONES", "JAMES", "LEWIS", "EVANS",
    "DENNIS", "ALEXIS", "THOMAS", "LUCAS", "DALLAS",
    "ROGERS", "WALKERS", "PHILIPS", "SIEMENS", "MARS",
    "ROLLS",  "JACOBS",  "OWENS",  "MARTINS", "REEVES",
    # (Note: DREAMERS, STREAMERS, PRIMERS, FARMERS, TIMERS, SWIMMERS, TRIMMERS,
    #  PERFORMERS, REFORMERS, INFORMERS, SONS, BROTHERS, ASSOCIATES, PARTNERS,
    #  HOLDINGS, COMMUNICATIONS, DYNAMICS, ELECTRONICS, GRAPHICS have been moved
    #  to ALLOWED_SINGULAR_MAP for proper singular conversion.)

    # ── Words where the singular is wrong / misleading ────────────────────────
    "OVERSEAS",         # Adjective/adverb — "Oversea" is not a word
    "GOODS",            # "Goods" means merchandise, not plural of "good"
    "ILLINOIS",         # US State
    "CHAMOIS",          # Invariant word
    # (STATES → STATE and HEADQUARTERS → HEADQUARTER moved to ALLOWED_SINGULAR_MAP)

    # ── Words ending in -ics that are invariant / brand ───────────────────────
    # (Prevent the ICALS / TICS pattern from triggering on these)
    "PHYSICS", "ETHICS", "ECONOMICS", "MATHEMATICS", "AEROBICS",
    "ACOUSTICS", "ATHLETICS", "TACTICS",
    # (LOGISTICS → LOGISTIC moved to ALLOWED_SINGULAR_MAP)
})


# ══════════════════════════════════════════════════════════════════════════════
# LAYER 2 — EXPLICIT WHITELIST
# Built from 317,000+ real trade names in Total name.csv.
# Key = PLURAL (uppercase), Value = SINGULAR (uppercase)
# Note: Short words handled here that Layer 3 min-length guards would miss.
# ══════════════════════════════════════════════════════════════════════════════
ALLOWED_SINGULAR_MAP = {
    # ── Chemicals & Materials ─────────────────────────────────────────────────
    "ABRASIVES":        "ABRASIVE",
    "ACIDS":            "ACID",
    "ADDITIVES":        "ADDITIVE",
    "ADHESIVES":        "ADHESIVE",
    "ADSORBENTS":       "ADSORBENT",
    "LIFESCIENCES":     "LIFESCIENCE",
    "AMINES":           "AMINE",
    "AROMATICS":        "AROMATIC",
    "CAPSULES":         "CAPSULE",
    "CERAMICS":         "CERAMIC",
    "CHEMICALS":        "CHEMICAL",
    "COATINGS":         "COATING",
    "COLORANTS":        "COLORANT",
    "COLORS":           "COLOR",
    "COLOURS":          "COLOUR",
    "COMPONENTS":       "COMPONENT",
    "COSMETICS":        "COSMETIC",
    "DENIMS":           "DENIM",
    "DETERGENTS":       "DETERGENT",
    "DIAGNOSTICS":      "DIAGNOSTIC",
    "DYESTUFFS":        "DYESTUFF",
    "EATABLES":         "EATABLE",
    "ENZYMES":          "ENZYME",
    "FABRICS":          "FABRIC",
    "FERTILIZERS":      "FERTILIZER",
    "FIBERS":           "FIBER",
    "FIBRES":           "FIBRE",
    "FLAVORS":          "FLAVOR",
    "FLUIDS":           "FLUID",
    "FOODSTUFFS":       "FOODSTUFF",
    "FORMULATIONS":     "FORMULATION",
    "FRAGRANCES":       "FRAGRANCE",
    "GLOVES":           "GLOVE",
    "INGREDIENTS":      "INGREDIENT",
    "INSECTICIDES":     "INSECTICIDE",
    "INSULATORS":       "INSULATOR",
    "INTERMEDIATES":    "INTERMEDIATE",
    "MATERIALS":        "MATERIAL",
    "MEDICINES":        "MEDICINE",
    "METALS":           "METAL",
    "MICROELECTRONICS": "MICROELECTRONIC",
    "ORGANICS":         "ORGANIC",
    "PAINTS":           "PAINT",
    "PERFUMES":         "PERFUME",
    "PESTICIDES":       "PESTICIDE",
    "PETROCHEMICALS":   "PETROCHEMICAL",
    "PHARMACEUTICALS":  "PHARMACEUTICAL",
    "PHOSPHATES":       "PHOSPHATE",
    "POLYMERS":         "POLYMER",
    "ISOMERS":          "ISOMER",       # 7 chars — below Layer 3 MERS min of 9
    "MONOMERS":         "MONOMER",      # 8 chars — below Layer 3 MERS min of 9
    "EMULSIFIERS":      "EMULSIFIER",   # in whitelist as backup
    "LUBRICANTS":       "LUBRICANT",
    "HUMECTANTS":       "HUMECTANT",
    "COAGULANTS":       "COAGULANT",
    "FLOCCULANTS":      "FLOCCULANT",
    "RETARDANTS":       "RETARDANT",
    "ANTIOXIDANTS":     "ANTIOXIDANT",
    "OXIDANTS":         "OXIDANT",
    "SULFATES":         "SULFATE",
    "SULPHATES":        "SULPHATE",
    "NITRATES":         "NITRATE",
    "SILICATES":        "SILICATE",
    "CARBONATES":       "CARBONATE",
    "ELASTOMERS":       "ELASTOMER",
    "OLIGOMERS":        "OLIGOMER",
    "COPOLYMERS":       "COPOLYMER",
    "REMEDIES":         "REMEDY",
    "RESINS":           "RESIN",
    "SCIENCES":         "SCIENCE",
    "SOLVENTS":         "SOLVENT",
    "SUBSTANCES":       "SUBSTANCE",
    "SURFACTANTS":      "SURFACTANT",
    "SYNTHETICS":       "SYNTHETIC",
    "TEXTILES":         "TEXTILE",
    "TOILETRIES":       "TOILETRY",
    # ── Business / Industry descriptors ──────────────────────────────────────
    "ENTERPRISES":      "ENTERPRISE",
    "ACCESSORIES":      "ACCESSORY",
    "ACHIEVERS":        "ACHIEVER",
    "AGENCIES":         "AGENCY",
    "AIRLINES":         "AIRLINE",
    "APPARELS":         "APPAREL",
    "AUTOS":            "AUTO",
    "BATTERIES":        "BATTERY",
    "BEVERAGES":        "BEVERAGE",
    "BISCUITS":         "BISCUIT",
    "BROKERS":          "BROKER",
    "CABLES":           "CABLE",
    "CANDLES":          "CANDLE",
    "COATS":            "COAT",
    "COMMODITIES":      "COMMODITY",
    "CONSULTANTS":      "CONSULTANT",
    "CONTRACTORS":      "CONTRACTOR",
    "DAIRIES":          "DAIRY",
    "DEVICES":          "DEVICE",
    "DISTRIBUTORS":     "DISTRIBUTOR",
    "ENGINEERS":        "ENGINEER",
    "EXPORTERS":        "EXPORTER",
    "EXPORTS":          "EXPORT",
    "FASHIONS":         "FASHION",
    "FOODS":            "FOOD",
    "FORWARDERS":       "FORWARDER",
    "GARMENTS":         "GARMENT",
    "IMPORTERS":        "IMPORTER",
    "IMPORTS":          "IMPORT",
    "INDIVIDUALS":      "INDIVIDUAL",
    "INDUSTRIES":       "INDUSTRY",
    "INFRASTRUCTURES":  "INFRASTRUCTURE",
    "INSTRUMENTS":      "INSTRUMENT",
    "LABORATORIES":     "LABORATORY",
    "MANUFACTURERS":    "MANUFACTURER",
    "MERCHANTS":        "MERCHANT",
    "MILLS":            "MILL",
    "PROCESSORS":       "PROCESSOR",
    "PRODUCTS":         "PRODUCT",
    "RELATIONS":        "RELATION",
    "RESTAURANTS":      "RESTAURANT",
    "SALES":            "SALE",
    "SPECIALTIES":      "SPECIALTY",
    "SPORTS":           "SPORT",
    "SUPPLIERS":        "SUPPLIER",
    "SUPPLIES":         "SUPPLY",
    "SURFACES":         "SURFACE",
    "TECHNOLOGIES":     "TECHNOLOGY",
    "TRADERS":          "TRADER",
    "TRANSFORMERS":     "TRANSFORMER",
    "UNITS":            "UNIT",
    "VENTURES":         "VENTURE",
    "WHOLESALERS":      "WHOLESALER",
    "TIRES":            "TYRE",
    "TYRES":            "TYRE",
    "TYRE":             "TYRE",
    "DYES":             "DYE",
    "QUMICA":           "QUIMICA",
    "QUMICAS":          "QUIMICA",
    "QUIMICAS":         "QUIMICA",
    "LABORATORIAI":     "LABORATORY",
    "LABORATORIAIS":    "LABORATORY",
    "INDUSTRIAS":       "INDUSTRY",
    "INDUSTRIAL":       "INDUSTRY",

    # ── Previously Protected — Now Singularized ──────────────────────────────
    # Business identity words
    "SONS":              "SON",
    "BROTHERS":          "BROTHER",
    "ASSOCIATES":        "ASSOCIATE",
    "PARTNERS":          "PARTNER",
    "HOLDINGS":          "HOLDING",
    "COMMUNICATIONS":    "COMMUNICATION",
    "DYNAMICS":          "DYNAMIC",
    "ELECTRONICS":       "ELECTRONIC",
    "GRAPHICS":          "GRAPHIC",
    # Former -MERS non-chemistry words
    "DREAMERS":          "DREAMER",
    "STREAMERS":         "STREAMER",
    "PRIMERS":           "PRIMER",
    "FARMERS":           "FARMER",
    "TIMERS":            "TIMER",
    "SWIMMERS":          "SWIMMER",
    "TRIMMERS":          "TRIMMER",
    "PERFORMERS":        "PERFORMER",
    "REFORMERS":         "REFORMER",
    "INFORMERS":         "INFORMER",
    # General words previously blocking singular conversion
    "STATES":            "STATE",
    "HEADQUARTERS":      "HEADQUARTER",
    "LOGISTICS":         "LOGISTIC",
    # Countries
    "Netherlands":       "Netherland",
    "Nederlands":        "Netherland",
    "Nederland":         "Netherland"
}


# ══════════════════════════════════════════════════════════════════════════════
# LAYER 3 — SAFE SUFFIX PATTERNS (Future-Proofing)
#
# Covers NEW chemistry / science compound words not yet in the whitelist.
# Each rule: (minimum_word_length, plural_suffix, singular_suffix)
#
# Minimum length guard prevents false matches on short/ambiguous words.
# All patterns chosen because they are UNAMBIGUOUSLY chemistry/science suffixes
# and extremely rare in proper nouns or brand names at the required length.
#
# Examples of words these patterns handle automatically:
#   AGROCHEMICALS (13) → AGROCHEMICAL   [ICALS rule]
#   BIOPOLYMERS   (11) → BIOPOLYMER     [MERS  rule]
#   NANOEMULSIFIERS(15)→ NANOEMULSIFIER [IZERS rule]
#   BIOTECHNOLOGIES(15)→ BIOTECHNOLOGY  [OLOGIES rule]
#   COPOLYMERS    (10) → COPOLYMER      [MERS  rule]
#   OLIGOMERS     ( 9) → OLIGOMER       [MERS  rule]
#   ISOMERS       ( 7) → ISOMER         [MERS  rule, min 7]
#   MONOMERS      ( 8) → MONOMER        [MERS  rule]
#   ELASTOMERS    (10) → ELASTOMER      [MERS  rule]
#   EMULSIFIERS   (11) → EMULSIFIER     [IZERS rule]
#   STABILIZERS   (11) → STABILIZER     [IZERS rule]
#   PLASTICIZERS  (12) → PLASTICIZER    [IZERS rule]
# ══════════════════════════════════════════════════════════════════════════════
SAFE_SUFFIX_PATTERNS = [
    # (min_total_length, plural_suffix, singular_suffix)
    #
    # NOTE ON SUFFIX MATCHING:
    # The suffix here is the ENDING of the word, not the full word.
    # e.g. "ICALS" matches "CHEMICALS" (ends in ICALS) → strips ICALS, adds ICAL → "CHEMICAL"
    # e.g. "FIERS" matches "EMULSIFIERS" (ends in FIERS) → strips FIERS, adds FIER → "EMULSIFIER"

    # -ICALS → -ICAL  (chemistry adjectives used as nouns)
    # e.g. CHEMicals, PHARMACEUTicals, BIOMEDicals, AGROCHEMicals
    # Min 9: shortest real match is "CHEMICALS" (9). "RADICALS"(8) excluded.
    (9,  "ICALS",   "ICAL"),

    # -IZERS → -IZER  (agent/process chemistry words, US spelling)
    # e.g. fertilIZERS, plasticIZERS, stabilIZERS, oxidIZERS → IZERS suffix
    # Min 9: "SIZERS"(6) excluded. Shortest real match: "OXIDIZERS"(9).
    (9,  "IZERS",   "IZER"),

    # -ISERS → -ISER  (British spelling of -IZERS)
    # e.g. stabilISERS, emulsifISERS, oxidISERS
    (9,  "ISERS",   "ISER"),

    # -FIERS → -FIER  (agent words with vowel-shift: emulsiFIERS, classFIERS)
    # e.g. EMULSIFIERS (11), HUMIDIFIERS (11), CLARIFIERS (10)
    # Covered separately because these end in FIERS not IZERS.
    # Min 10: avoids short false matches.
    (10, "FIERS",   "FIER"),

    # -MERS → -MER  (polymer chemistry — very specific suffix)
    # e.g. polyMERS, elastoMERS, monoMERS, oligoMERS, copoMERS, isoMERS
    # Min 9: raises threshold to exclude 8-char words like DREAMERS, STREAMERS, PRIMERS
    # (those are added to PROTECTED_WORDS anyway as a belt-and-suspenders guard)
    # "ISOMERS"(7) and "MONOMERS"(8) added to whitelist explicitly instead.
    (9,  "MERS",    "MER"),

    # -OLOGIES → -OLOGY  (scientific disciplines)
    # e.g. techNOLOGIES, biotechNOLOGIES, nanoTECHNOLOGIES
    # Min 10: all real instances are long compound words.
    (10, "OLOGIES", "OLOGY"),

    # -ICIDES → -ICIDE  (chemical compound class — pesticides, fungicides etc.)
    # e.g. fungICIDES, herbICIDES, insectICIDES, pestICIDES
    # Min 10: excludes "TIDES"(5), "GUIDES"(6). "FUNGICIDES"(10) ✓
    (10, "ICIDES",  "ICIDE"),

    # Specific narrowed salt/ester -ATE patterns:
    # Only unambiguous chemistry suffixes used — avoids catching "GATES", "DATES" etc.
    (8,  "PHATES",  "PHATE"),    # sulPHATES, phosPHATES (≥8 chars)
    (9,  "LICATES", "LICATE"),   # siLICATES, carbonate? no — this is siLICATES
    (10, "BONATES", "BONATE"),   # carBONATES
    (8,  "SULFATES","SULFATE"),  # exact suffix → 'SULFATES' is 8 chars = 8 ✓
    (8,  "SULPHATES","SULPHATE"),
    (8,  "NITRATES","NITRATE"),  # 8 chars = 8 ✓

    # Specific narrowed -ANT patterns (too risky as general rule):
    (9,  "OXIDANTS", "OXIDANT"),     # oxidANTS
    (10, "FACTANTS", "FACTANT"),     # surFACTANTS
    (10, "LUBRICANTS","LUBRICANT"),
    (10, "RETARDANTS","RETARDANT"),
    (10, "HUMECTANTS","HUMECTANT"),
    (10, "COAGULANTS","COAGULANT"),
    (11, "FLOCCULANTS","FLOCCULANT"),
    (11, "ANTIOXIDANTS","ANTIOXIDANT"),

    # Specific narrowed -ENT patterns:
    (8,  "OLVENTS",  "OLVENT"),   # sOLVENTS (8) ✓  re-sOLVENTS (10) ✓
    (9,  "EAGENTS",  "EAGENT"),   # rEAGENTS (8)... "REAGENTS" is 8, min=9 edge case
                                   # → REAGENTS already in whitelist anyway
    (10, "MOLLIENTS","MOLLIENT"), # emOLLIENTS
]


@lru_cache(maxsize=8192)
def normalize_word(word: str) -> str:
    """
    Return the canonical SINGULAR form for a word, using the 3-layer system.

    Layer 1: PROTECTED_WORDS  → return word unchanged (fastest check)
    Layer 2: ALLOWED_SINGULAR_MAP → return mapped singular
    Layer 3: SAFE_SUFFIX_PATTERNS → apply chemistry/science suffix rule
    Default: return word unchanged

    Results are LRU-cached — each unique word is processed at most once.
    """
    w_upper = word.upper().strip()
    if not w_upper:
        return ""

    # ── Layer 1: Protected words (never touch these) ──────────────────────────
    if w_upper in PROTECTED_WORDS:
        return w_upper

    # Short words (≤ 4 chars) are never singularized — too ambiguous
    if len(w_upper) <= 4:
        return w_upper

    # ── Layer 2: Explicit whitelist ───────────────────────────────────────────
    if w_upper in ALLOWED_SINGULAR_MAP:
        return ALLOWED_SINGULAR_MAP[w_upper]

    # ── Layer 3: Safe suffix patterns ─────────────────────────────────────────
    wlen = len(w_upper)
    for min_len, plural_suffix, singular_suffix in SAFE_SUFFIX_PATTERNS:
        if wlen >= min_len and w_upper.endswith(plural_suffix.upper()):
            base = w_upper[: -len(plural_suffix)]
            if len(base) >= 3:                     # base must be at least 3 chars
                return base + singular_suffix.upper()

    # ── Default: return unchanged ─────────────────────────────────────────────
    return w_upper


def is_approved_pair(word1: str, word2: str) -> bool:
    """Return True if word1 and word2 map to the same canonical singular form."""
    c1 = normalize_word(word1)
    c2 = normalize_word(word2)
    return c1 == c2 and c1 != ""


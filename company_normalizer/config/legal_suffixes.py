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

SLU_FAMILY             = "SLU_FAMILY"
LTD_STI_FAMILY         = "LTD_STI_FAMILY"
SAC_FAMILY             = "SAC_FAMILY"

SAICA_FAMILY           = "SAICA_FAMILY"
WLL_FAMILY             = "WLL_FAMILY"
BSC_FAMILY             = "BSC_FAMILY"

INC_FAMILY             = "INC_FAMILY"
LLC_FAMILY             = "LLC_FAMILY"
GMBH_FAMILY            = "GMBH_FAMILY"
SA_FAMILY              = "SA_FAMILY"
NV_FAMILY              = "NV_FAMILY"
KK_FAMILY              = "KK_FAMILY"
SPA_FAMILY             = "SPA_FAMILY"
TBK_FAMILY             = "TBK_FAMILY"
MALAYSIAN_FAMILY       = "MALAYSIAN_FAMILY"
UAE_FREEZONE_FAMILY    = "UAE_FREEZONE_FAMILY"
CIA_FAMILY             = "CIA_FAMILY"
LLP_FAMILY             = "LLP_FAMILY"
DMCC_FAMILY            = "DMCC_FAMILY"
KG_FAMILY              = "KG_FAMILY"
SAS_FAMILY             = "SAS_FAMILY"
SMC_FAMILY             = "SMC_FAMILY"
AG_FAMILY              = "AG_FAMILY"
AB_FAMILY              = "AB_FAMILY"
OY_FAMILY              = "OY_FAMILY"
JSC_FAMILY             = "JSC_FAMILY"

LEGAL_SUFFIX_MAP = {
    # ── PRIVATE / LIMITED ───────────────────
    "PRIVATE LIMITED": ("PRIVATE LIMITED", PRIVATE_LIMITED_FAMILY),
    "CO PRIVATE LIMITED":      ("PRIVATE LIMITED", PRIVATE_LIMITED_FAMILY),
    "COMPANY PRIVATE LIMITED": ("PRIVATE LIMITED", PRIVATE_LIMITED_FAMILY),
    "CO. PRIVATE LIMITED":     ("PRIVATE LIMITED", PRIVATE_LIMITED_FAMILY),
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
    "PTY LIMITED":     ("PRIVATE LIMITED", PRIVATE_LIMITED_FAMILY),
    "PTY. LIMITED.":   ("PRIVATE LIMITED", PRIVATE_LIMITED_FAMILY),
    "PTE LTD":         ("PRIVATE LIMITED", PRIVATE_LIMITED_FAMILY),
    "PTE. LTD.":       ("PRIVATE LIMITED", PRIVATE_LIMITED_FAMILY),
    "PTE LTD.":        ("PRIVATE LIMITED", PRIVATE_LIMITED_FAMILY),
    "PTE. LTD":        ("PRIVATE LIMITED", PRIVATE_LIMITED_FAMILY),
    "PVT":             ("PRIVATE",         PRIVATE_LIMITED_FAMILY),
    "PTY":             ("PRIVATE",         PRIVATE_LIMITED_FAMILY),
    "PTE":             ("PRIVATE",         PRIVATE_LIMITED_FAMILY),
    "PT":              ("PT",              PRIVATE_LIMITED_FAMILY),
    "PT.":             ("PT",              PRIVATE_LIMITED_FAMILY),
    "LIMITED":         ("LIMITED",         PRIVATE_LIMITED_FAMILY),
    "LTD":             ("LIMITED",         PRIVATE_LIMITED_FAMILY),
    "LTD.":            ("LIMITED",         PRIVATE_LIMITED_FAMILY),

    # ── CO. LIMITED ─────────────────────────
    "CO LTD":   ("CO LIMITED", CO_LIMITED_FAMILY),
    "CO. LTD":  ("CO LIMITED", CO_LIMITED_FAMILY),
    "CO. LTD.": ("CO LIMITED", CO_LIMITED_FAMILY),
    "CO LTD.":  ("CO LIMITED", CO_LIMITED_FAMILY),
    "COMPANY LIMITED": ("CO LIMITED", CO_LIMITED_FAMILY),

    # ── CORPORATION ─────────────────────────
    "CORP":        ("CORPORATION", CORPORATE_FAMILY),
    "CORP.":       ("CORPORATION", CORPORATE_FAMILY),
    "CORPORATION": ("CORPORATION", CORPORATE_FAMILY),
    "CO":          ("CO",          None),
    "CO.":         ("CO",          None),
    "COMPANY":     ("CO",          None),

    # ── CV ──────────────────────────────────
    "C V":  ("CV", CV_FAMILY),
    "C.V.": ("CV", CV_FAMILY),
    "CV":   ("CV", CV_FAMILY),

    # ── EUROPEAN ────────────────────────────
    "SARL": ("SARL", EUROPEAN_FAMILY),
    "SRL":  ("SARL", EUROPEAN_FAMILY),
    "S R L":("SARL", EUROPEAN_FAMILY),
    "S.R.L.":("SARL", EUROPEAN_FAMILY),

    # ── MEXICAN ─────────────────────────────
    "S DE RL DE CV":      ("S DE RL DE CV", MEXICAN_LEGAL_FAMILY),
    "S DE RL DE C V":     ("S DE RL DE CV", MEXICAN_LEGAL_FAMILY),
    "S.DE R.L DE C.V.":   ("S DE RL DE CV", MEXICAN_LEGAL_FAMILY),
    "S.DE R.L. DE C.V.":  ("S DE RL DE CV", MEXICAN_LEGAL_FAMILY),
    "S. DE R.L. DE C.V.": ("S DE RL DE CV", MEXICAN_LEGAL_FAMILY),
    "S DE R L DE C V":    ("S DE RL DE CV", MEXICAN_LEGAL_FAMILY),
    "SA DE CV":           ("SA DE CV", MEXICAN_LEGAL_FAMILY),
    "S.A. DE C.V.":       ("SA DE CV", MEXICAN_LEGAL_FAMILY),
    "S A DE C V":         ("SA DE CV", MEXICAN_LEGAL_FAMILY),

    # ── SPANISH (SLU) ───────────────────────
    "SLU":                ("SLU", SLU_FAMILY),
    "S L U":              ("SLU", SLU_FAMILY),
    "S.L.U.":             ("SLU", SLU_FAMILY),

    # ── TURKISH (LTD STI) ───────────────────
    "LTD STI":            ("LTD STI", LTD_STI_FAMILY),
    "LIMITED STI":        ("LTD STI", LTD_STI_FAMILY),

    # ── PERUVIAN (SAC) ──────────────────────
    "SAC":                ("SAC", SAC_FAMILY),
    "S A C":              ("SAC", SAC_FAMILY),
    "S.A.C.":             ("SAC", SAC_FAMILY),

    # ── US CORPORATE (INC) ──────────────────
    "INC":          ("INCORPORATED", INC_FAMILY),
    "INC.":         ("INCORPORATED", INC_FAMILY),
    "INCORPORATED": ("INCORPORATED", INC_FAMILY),

    # ── US LLC ──────────────────────────────
    "LLC":                       ("LLC", LLC_FAMILY),
    "L.L.C.":                    ("LLC", LLC_FAMILY),
    "L L C":                     ("LLC", LLC_FAMILY),
    "LIMITED LIABILITY COMPANY": ("LLC", LLC_FAMILY),
    "LIMITED LIABILITY CO":      ("LLC", LLC_FAMILY),

    # ── GERMAN ──────────────────────────────
    "GMBH":                                    ("GMBH", GMBH_FAMILY),
    "GESELLSCHAFT MIT BESCHRÄNKTER HAFTUNG":   ("GMBH", GMBH_FAMILY),
    "GESELLSCHAFT MIT BESCHRANKTER HAFTUNG":   ("GMBH", GMBH_FAMILY),
    "GMBH CO KG":                              ("GMBH CO KG", GMBH_FAMILY),
    "GMBH AND CO KG":                          ("GMBH CO KG", GMBH_FAMILY),
    "KG":                                      ("KG", KG_FAMILY),
    "KOMMANDITGESELLSCHAFT":                   ("KG", KG_FAMILY),
    
    # ── AG ──────────────────────────────────
    "AG":                          ("AG", AG_FAMILY),
    "AKTIENGESELLSCHAFT":          ("AG", AG_FAMILY),

    # ── FRENCH / LATAM / ITALIAN ────────────
    "SA":                             ("SA", SA_FAMILY),
    "S A":                            ("SA", SA_FAMILY),
    "S.A.":                           ("SA", SA_FAMILY),
    "SOCIEDAD ANONIMA":               ("SA", SA_FAMILY),
    "SOCIETE ANONYME":                ("SA", SA_FAMILY),
    "SOCIÉTÉ ANONYME":                ("SA", SA_FAMILY),
    "SPA":                            ("SPA", SPA_FAMILY),
    "S.P.A.":                         ("SPA", SPA_FAMILY),
    "SOCIETA PER AZIONI":             ("SPA", SPA_FAMILY),
    "SOCIETÀ PER AZIONI":             ("SPA", SPA_FAMILY),
    "SAS":                            ("SAS", SAS_FAMILY),
    "S.A.S.":                         ("SAS", SAS_FAMILY),
    "SOCIETE PAR ACTIONS SIMPLIFIEE": ("SAS", SAS_FAMILY),
    "SOCIÉTÉ PAR ACTIONS SIMPLIFIÉE": ("SAS", SAS_FAMILY),

    # ── DUTCH / BELGIUM ─────────────────────
    "NV":                    ("NV", NV_FAMILY),
    "N.V.":                  ("NV", NV_FAMILY),
    "NAAMLOZE VENNOOTSCHAP": ("NV", NV_FAMILY),
    "BV":                    ("BV", "BV_FAMILY"),
    "BESLOTEN VENNOOTSCHAP": ("BV", "BV_FAMILY"),

    # ── JAPANESE ────────────────────────────
    "KK":               ("KK", KK_FAMILY),
    "K.K.":             ("KK", KK_FAMILY),
    "KABUSHIKI KAISHA": ("KK", KK_FAMILY),

    # ── NORDIC ──────────────────────────────
    "AB":         ("AB", AB_FAMILY),
    "AKTIEBOLAG": ("AB", AB_FAMILY),
    "OY":         ("OY", OY_FAMILY),
    "OSAKEYHTIÖ": ("OY", OY_FAMILY),
    "OSAKEYHTIO": ("OY", OY_FAMILY),

    # ── INDONESIAN ──────────────────────────
    "TBK":     ("TBK", TBK_FAMILY),
    "TERBUKA": ("TBK", TBK_FAMILY),

    # ── MALAYSIAN ───────────────────────────
    "BHD":              ("BHD", MALAYSIAN_FAMILY),
    "BERHAD":           ("BHD", MALAYSIAN_FAMILY),
    "SDN BHD":          ("SDN BHD", MALAYSIAN_FAMILY),
    "SDN. BHD.":        ("SDN BHD", MALAYSIAN_FAMILY),
    "SENDIRIAN BERHAD": ("SDN BHD", MALAYSIAN_FAMILY),
    "SDN":              ("SDN BHD", MALAYSIAN_FAMILY),
    "SDN.":             ("SDN BHD", MALAYSIAN_FAMILY),
    "SENDIRIAN":        ("SDN BHD", MALAYSIAN_FAMILY),

    # ── UAE / FREE ZONE ─────────────────────
    "FZE":                     ("FZE", UAE_FREEZONE_FAMILY),
    "FREE ZONE ESTABLISHMENT": ("FZE", UAE_FREEZONE_FAMILY),
    "FZCO":                    ("FZCO", UAE_FREEZONE_FAMILY),
    "FZC":                     ("FZCO", UAE_FREEZONE_FAMILY),
    "FREE ZONE COMPANY":       ("FZCO", UAE_FREEZONE_FAMILY),
    "FREE ZONE CO":            ("FZCO", UAE_FREEZONE_FAMILY),
    "FZ":                      ("FZ", UAE_FREEZONE_FAMILY),
    "FREE ZONE":               ("FZ", UAE_FREEZONE_FAMILY),
    "DMCC":                            ("DMCC", DMCC_FAMILY),
    "DUBAI MULTI COMMODITIES CENTRE":  ("DMCC", DMCC_FAMILY),

    # ── SPANISH (CIA) ───────────────────────
    "CIA":       ("CIA", CIA_FAMILY),
    "CIA.":      ("CIA", CIA_FAMILY),
    "COMPANIA":  ("CIA", CIA_FAMILY),
    "COMPAÑIA":  ("CIA", CIA_FAMILY),
    "COMPAÑÍA":  ("CIA", CIA_FAMILY),

    # ── JSC (VIETNAM / RUSSIA) ──────────────
    "JSC":                      ("JSC", JSC_FAMILY),
    "J.S.C.":                   ("JSC", JSC_FAMILY),
    "JOINT STOCK COMPANY":      ("JSC", JSC_FAMILY),
    "JOINT STOCK CO":           ("JSC", JSC_FAMILY),

    # ── ARGENTINA (SAICA) ───────────────────
    "SAICA":                    ("SAICA", SAICA_FAMILY),

    # ── MIDDLE EAST (WLL, BSC) ──────────────
    "WLL":                      ("WLL", WLL_FAMILY),
    "W.L.L.":                   ("WLL", WLL_FAMILY),
    "W L L":                    ("WLL", WLL_FAMILY),
    "BSC":                      ("BSC", BSC_FAMILY),
    "B.S.C.":                   ("BSC", BSC_FAMILY),
    "B S C":                    ("BSC", BSC_FAMILY),

    # ── OTHERS ──────────────────────────────
    "LLP":                           ("LLP", LLP_FAMILY),
    "LIMITED LIABILITY PARTNERSHIP": ("LLP", LLP_FAMILY),
    "SMC":                           ("SMC", SMC_FAMILY),
    "SINGLE MEMBER COMPANY":         ("SMC", SMC_FAMILY),
    "SINGLE MEMBER CO":              ("SMC", SMC_FAMILY),
}

# Normalise all keys to UPPERCASE
LEGAL_SUFFIX_MAP = {k.upper(): v for k, v in LEGAL_SUFFIX_MAP.items()}


def normalize_suffix(suffix: str):
    key = suffix.upper().strip()
    return LEGAL_SUFFIX_MAP.get(key, (suffix, None))


def get_all_suffixes():
    return list(LEGAL_SUFFIX_MAP.keys())

# Complete Rules Reference Guide — *Updated 06 Apr 2026*
## Company Name Normalization Tool — All Rules Explained for Everyone

> **How to read this guide:** This document explains every single rule and decision the system makes when it cleans up company names. Think of it like a recipe book — it lists every ingredient (rule) and exactly when and why it is used. Examples show real before → after cases.

---

## PART 1: TEXT CLEANER — Making Everything Look the Same
**File:** `processors/text_cleaner.py`

The very first thing the system does is give every name a thorough wash. Like washing vegetables before cooking — nothing else works well until this is done.

---

### Rule 1.0 — Alias Stripping
**What it does:** If a company name contains a "doing business as" or "trading as" declaration, everything from that point onwards is deleted. Only the real company name before the alias tag is kept.

**Trigger words:** `Trading As`, `T/A`, `T A`, `T.A.`, `D/B/A`, `DBA`, `Doing Business As`

| Before | After |
|---|---|
| `Acme Supplies T/A Big Boxes Ltd` | `Acme Supplies` |
| `Green Foods Trading As Fresh Market` | `Green Foods` |
| `XYZ Corp DBA The Shop` | `XYZ Corp` |

---

### Rule 1.1 — Ampersand Conversion
**What it does:** The symbol `&` is always written out as the word `and`. This prevents two identical companies from looking different just because one person hit Shift+7.

| Before | After |
|---|---|
| `Johnson & Sons` | `Johnson and Sons` |
| `Oil & Gas Traders` | `Oil and Gas Traders` |

---

### Rule 1.2 — Punctuation Masking (The "Four Spaces" Rule)
**What it does:** Every punctuation character is replaced with exactly four spaces, not just one. The reason for four is important: if someone typed `Tech.Ltd` (no space around the dot), one space replacement would give `Tech Ltd` correctly. But with just one space, `P.T.Smith` would give `P T Smith` and the "P" and "T" might glue to other things. Four spaces guarantee that when the whitespace is later collapsed, every token cleanly separates.

**Characters replaced with 4 spaces:** `. , / ; : ' " ( ) [ ] ! ? _ \ @ # * ~ \` | < > { } = + -`

| Before | After (before collapse) | Final after collapse |
|---|---|---|
| `Tech.Ltd` | `Tech    Ltd` | `Tech Ltd` |
| `Smith-Corp` | `Smith    Corp` | `Smith Corp` |
| `P.T.Barnum Co.` | `P    T    Barnum Co    ` | `P T Barnum Co` |

---

### Rule 1.3 — Clean / Trim / Proper (First Pass)
**What it does:** Three sub-rules in one:
1. All multi-spaces (including the four spaces from Rule 1.2) are collapsed into a single space.
2. Leading and trailing spaces are removed.
3. The text is converted to Title Case (first letter of every word capitalized).

| Before | After |
|---|---|
| `   TATA   CHEMICALS  ` | `Tata Chemicals` |
| `samsung ELECTRONICS pvt ltd` | `Samsung Electronics Pvt Ltd` |

---

### Rule 1.4 — Abbreviation Expansion Map
**What it does:** After the first clean pass, a lookup table expands common short forms into their full words. The system applies these in strict order — longer patterns first.

**Complete Expansion Table:**

| Raw Input | Converts To | Notes |
|---|---|---|
| `Pvt` / `PVT` / `Priv` | `Private` | Any case |
| `Pte` (with a leading space) | `Private` | Only Singapore "Pte" after a space |
| `P Ltd` / `P. Ltd` / `P.LTD` | `Private Limited` | P standing before Ltd |
| `Ltd` / `LTD` / `Ltd.` | `Limited` | Any variant with optional dot |
| `Ltda` / `LTDA` | `Limited` | Latin American variant |
| `Limitada` / `LIMITADA` | `Limited` | Spanish full form |
| `Limiteda` / `Limitad a` | `Limited` | Corrupted spellings |
| `Limite` / `Limi` | `Limited` | Truncated forms |
| `Lim` (only at end of name) | `Limited` | Only when it's the last word |
| `Corpn` / `Corp` | `Corporation` | With optional dot |
| `Company` / `COMPANY` | `Co` | Shortened |
| `Mfg` / `MFG` | `Manufacturing` | |
| `Mfrs` / `MFRS` | `Manufacturers` | |
| `Intl` / `INTL` | `International` | |
| `Bros` / `BROS` | `Brothers` | |
| `[word]private` (glued) | `[word] Private` | e.g. `Salesprivate` → `Sales Private` |
| `[word]pvt` (glued) | `[word] Private` | e.g. `Techpvt` → `Tech Private` |

---

### Rule 1.5 — Clean / Trim / Proper (Second Pass)
**What it does:** Runs the exact same collapse + strip + Title Case again after abbreviation expansion, because expansions may have left extra spaces.

| Before (after expansion) | After |
|---|---|
| `Tata  Private  Limited ` | `Tata Private Limited` |

---

## PART 2: ADDRESS REMOVER — Stripping Out Location Details
**File:** `processors/address_remover.py`

After text cleaning, company names sometimes still have building addresses, suite numbers, or plot details at the end. These are useless for matching and are removed.

---

### Rule 2.1 — Tail-End Address Keyword Scan
**What it does:** The system looks at the *last word* of the name and checks it against a list of known address words. If matched, that word is deleted and the scan repeats on the new last word.

**Complete list of address keywords removed from the end:**
`BUILDING`, `BLDG`, `BLD`, `FLOOR`, `FLR`, `BLOCK`, `STREET`, `ROAD`, `AVENUE`, `LANE`, `TOWER`, `PLAZA`, `COMPLEX`, `HOUSE`, `SUITE`, `UNIT`, `ROOM`, `NUMBER`, `NEAR`, `OPPOSITE`, `SECTOR`, `PHASE`, `PLOT`, `FLAT`, `NAGAR`, `COLONY`, `AREA`, `ZONE`, `DISTRICT`, `TEHSIL`, `TALUKA`, `VILLAGE`

| Before | After |
|---|---|
| `Tata Steel Block 5` | `Tata Steel` |
| `Samsung Electronics Floor 3 Building A` | `Samsung Electronics` |
| `Acme Corp Near Plaza` | `Acme Corp` |

---

### Rule 2.2 — Trailing Pure Number Removal
**What it does:** If the last token is a standalone number (like a building or floor number), it is removed.

| Before | After |
|---|---|
| `Samsung Electronics 7` | `Samsung Electronics` |

---

### Rule 2.3 — Short Alphanumeric Unit Code Removal
**What it does:** After an address keyword is found, the system will also strip short codes like `A4`, `B12`, or `3B` that refer to sub-units.

| Before | After |
|---|---|
| `Tata Steel Block A4` | `Tata Steel` |

---

### Rule 2.4 — Geography Protection
**What it does:** The system will NEVER strip a term that is a recognized country or region, even if it appears at the end of the name.

| Name | Result |
|---|---|
| `Tata Chemicals India` | `Tata Chemicals India` ✅ (India is not removed) |
| `Samsung Asia Floor 3` | `Samsung Asia` ✅ (Floor 3 removed, Asia preserved) |

---

### Rule 2.5 — Minimum Name Safety Guard
**What it does:** The address scanner will stop removing words if the name shrinks to 2 or fewer words, to avoid over-stripping short names.

---

## PART 3: PREFIX REMOVER — Stripping "Hello" Words
**File:** `processors/prefix_remover.py`  
**Config:** `config/prefixes.py`

Trade documents often start with politically added phrases like "Consignee To", "On Behalf Of", or just "M/S". These are meaningless for identifying the actual company.

---

### Rule 3.1 — Trade Prefixes (Shipment/Document Terms)
**What it does:** Removes these words when found at the *very beginning* of the name:

| Prefix Removed | Example Before | Example After |
|---|---|---|
| `CONSIGNEE TO` | `Consignee To Tata Steel` | `Tata Steel` |
| `CONSIGNEE` | `Consignee Tata Steel` | `Tata Steel` |
| `TO THE ORDER OF` | `To The Order Of Acme Corp` | `Acme Corp` |
| `TO THE ORDER` | `To The Order Acme Corp` | `Acme Corp` |
| `TO ORDER OF` | `To Order Of Acme Corp` | `Acme Corp` |
| `TO ORDER` | `To Order Acme` | `Acme` |
| `NOTIFIED PARTY` | `Notified Party Samsung` | `Samsung` |
| `NOTIFY` | `Notify Samsung` | `Samsung` |
| `NOTIFY PARTY` | `Notify Party Samsung` | `Samsung` |
| `ON BEHALF OF` | `On Behalf Of Global Traders` | `Global Traders` |
| `O/B` | `O/B Global Traders` | `Global Traders` |
| `BY ORDER OF` | `By Order Of Tata` | `Tata` |
| `B/O` | `B/O Tata` | `Tata` |
| `CARE OF` | `Care Of Acme` | `Acme` |
| `C/O` | `C/O Acme` | `Acme` |
| `ACCOUNT OF` | `Account Of XYZ` | `XYZ` |
| `A/C` | `A/C XYZ` | `XYZ` |
| `F/A` | `F/A XYZ` | `XYZ` |
| `FOR THE ACCOUNT OF` | `For The Account Of ABC` | `ABC` |

---

### Rule 3.2 — Business Prefixes (Honorifics / Office Terms)
| Prefix Removed | Example Before | Example After |
|---|---|---|
| `MESSRS OF` | `Messrs Of Tata Steel` | `Tata Steel` |
| `MESSRS` | `Messrs Tata Steel` | `Tata Steel` |
| `M/S` | `M/S Tata Steel` | `Tata Steel` |
| `M S` | `M S Tata Steel` | `Tata Steel` |
| `M.S.` | `M.S. Tata Steel` | `Tata Steel` |
| `MR.` / `MR` | `Mr. John Corp` | `John Corp` |
| `MS.` / `MS` | `Ms. Lisa Corp` | `Lisa Corp` |
| `ETS` / `ETS.` | `Ets Global Traders` | `Global Traders` |

---

### Rule 3.3 — Legal / Jurisdiction Prefixes
| Prefix Removed | Example Before | Example After |
|---|---|---|
| `P.T.` | `P.T. Samsung Indonesia` | `Samsung Indonesia` |
| `PT` | `PT Samsung Indonesia` | `Samsung Indonesia` |
| `CV` | `CV Global suppliers` | `Global Suppliers` |

---

### Rule 3.4 — Longest Match First
**What it does:** Longer prefixes are always tried first. This ensures `TO THE ORDER OF` is matched and removed correctly before trying to match the shorter `TO ORDER`.

---

### Rule 3.5 — Up to 10 Layers
**What it does:** The system will keep repeating prefix removal up to 10 times in case names have multiple stacked prefixes (e.g., `M/S On Behalf Of Consignee To Tata Steel`).

---

## PART 4: LEGAL SUFFIX EXTRACTION — Identifying Business Type
**File:** `processors/legal_suffix_normalizer.py`  
**Config:** `config/legal_suffixes.py`

Every business has a "type" at the end of its name — like `Private Limited` or `LLC`. The system extracts this, creates a clean "Base Name" (just the brand part), and groups all known legal variations into unified "Families".

---

### Rule 4.1 — Suffix Extraction (Longest Match, Right-to-Left)
**What it does:** The system sorts all known suffix strings by length (longest first) and checks if the cleaned name ends with any of them. This avoids false matches (e.g., "Co" inside "Co Limited" would not be picked before "Co Limited").

---

### Rule 4.2 — Legal Suffix Family Groupings
Every suffix is normalized into a standard "Family". Two names that belong to the same Family can potentially merge.

**Complete Suffix → Standard Output Table:**

| Country/Type | Raw Input Examples | Standard Output | Family |
|---|---|---|---|
| **India / Commonwealth** | `Pvt Ltd`, `Pvt. Ltd.`, `Private Limited`, `PTE Ltd`, `PTY Ltd` | `PRIVATE LIMITED` | `PRIVATE_LIMITED_FAMILY` |
| **India** | `Pvt`, `Pte`, `Pty` (standalone) | `PRIVATE` | `PRIVATE_LIMITED_FAMILY` |
| **Indonesia** | `P.T.`, `PT` | `PT` | `PRIVATE_LIMITED_FAMILY` |
| **Commonwealth** | `Limited`, `Ltd`, `Ltd.` | `LIMITED` | `LIMITED_FAMILY` |
| **Hong Kong / China** | `Co Limited`, `Co Ltd`, `Company Limited` | `CO LIMITED` | `CO_LIMITED_FAMILY` |
| **USA** | `Corp`, `Corporation` | `CORPORATION` | `CORPORATE_FAMILY` |
| **General** | `Co`, `Co.`, `Company` | `CO` | *(no family)* |
| **Dutch/Indonesian** | `C.V.`, `CV`, `C V` | `CV` | `CV_FAMILY` |
| **France/Europe** | `SARL`, `SRL`, `S.R.L.` | `SARL` | `EUROPEAN_FAMILY` |
| **Mexico** | `S DE RL DE CV`, `SA DE CV`, `S.A. DE C.V.` | `S DE RL DE CV` / `SA DE CV` | `MEXICAN_LEGAL_FAMILY` |
| **Spain** | `SLU`, `S.L.U.` | `SLU` | `SLU_FAMILY` |
| **Turkey** | `LTD STI`, `LIMITED STI` | `LTD STI` | `LTD_STI_FAMILY` |
| **Peru** | `SAC`, `S.A.C.` | `SAC` | `SAC_FAMILY` |
| **USA** | `LLC`, `L.L.C.`, `Limited Liability Company` | `LLC` | `LLC_FAMILY` |
| **USA** | `Inc`, `INC.`, `Incorporated` | `INCORPORATED` | `INC_FAMILY` |
| **Germany** | `GmbH`, `GmbH Co KG`, `Gesellschaft...` | `GMBH` | `GMBH_FAMILY` |
| **Germany** | `KG`, `Kommanditgesellschaft` | `KG` | `KG_FAMILY` |
| **Germany/Switzerland** | `AG`, `Aktiengesellschaft` | `AG` | `AG_FAMILY` |
| **France/Latin America** | `SA`, `S.A.`, `Sociedad Anonima`, `Societe Anonyme` | `SA` | `SA_FAMILY` |
| **France** | `SAS`, `S.A.S.` | `SAS` | `SAS_FAMILY` |
| **Italy** | `SpA`, `Societa Per Azioni` | `SPA` | `SPA_FAMILY` |
| **Netherlands** | `NV`, `N.V.`, `Naamloze Vennootschap` | `NV` | `NV_FAMILY` |
| **Netherlands** | `BV`, `B.V.`, `Besloten Vennootschap` | `BV` | `BV_FAMILY` |
| **Japan** | `KK`, `K.K.`, `Kabushiki Kaisha` | `KK` | `KK_FAMILY` |
| **Sweden** | `AB`, `Aktiebolag` | `AB` | `AB_FAMILY` |
| **Finland** | `OY`, `Osakeyhtiö` | `OY` | `OY_FAMILY` |
| **Indonesia** | `TBK`, `Terbuka` | `TBK` | `TBK_FAMILY` |
| **Malaysia** | `BHD`, `Berhad`, `SDN BHD`, `Sendirian Berhad` | `SDN BHD` / `BHD` | `MALAYSIAN_FAMILY` |
| **UAE / Free Zone** | `FZE`, `FZCO`, `FZC`, `Free Zone Establishment` | `FZE` / `FZCO` | `UAE_FREEZONE_FAMILY` |
| **UAE / Dubai** | `DMCC`, `Dubai Multi Commodities Centre` | `DMCC` | `DMCC_FAMILY` |
| **Spain** | `CIA`, `CIA.`, `Compania`, `Compañía` | `CIA` | `CIA_FAMILY` |
| **Vietnam / Russia** | `JSC`, `Joint Stock Company` | `JSC` | `JSC_FAMILY` |
| **Argentina** | `SAICA` | `SAICA` | `SAICA_FAMILY` |
| **Middle East** | `WLL`, `W.L.L.` | `WLL` | `WLL_FAMILY` |
| **Middle East** | `BSC`, `B.S.C.` | `BSC` | `BSC_FAMILY` |
| **General** | `LLP`, `Limited Liability Partnership` | `LLP` | `LLP_FAMILY` |
| **General** | `SMC`, `Single Member Company` | `SMC` | `SMC_FAMILY` |

---

## PART 5: FUNCTIONAL DESCRIPTOR CHECKER — What Industry Is It?
**File:** `processors/descriptor_checker.py`  
**Config:** `config/functional_descriptors.py`

This module identifies what *industry* a company belongs to based on key words in its name. This is a critical safety gate that stops two different-industry companies from accidentally being merged together.

---

### Rule 5.1 — Industry Keyword (Descriptor) Detection
**What it does:** Every word in the Base Name is checked against the functional descriptor list. If a match is found, it is tagged onto the company's profile.

**Important Sub-Rule:** Plural forms are automatically handled. The system converts every word to its singular form before checking. So `CHEMICALS` becomes `CHEMICAL`, and `INDUSTRIES` becomes `INDUSTRY`, meaning plural variants automatically match.

**Complete list of recognized industry descriptors (singular form):**

| Descriptor | Plural Variants Recognized |
|---|---|
| `LOGISTIC` | logistics |
| `TRADING` | *(no plural)* |
| `FINANCE` | *(adjective form covered)* |
| `FINANCIAL` | *(adjective)* |
| `HOLDING` | holdings |
| `POWER` | *(no plural)* |
| `ENERGY` | energies |
| `INFRA` | *(abbreviation)* |
| `INFRASTRUCTURE` | infrastructures |
| `SERVICE` | services |
| `PROJECT` | projects |
| `TECHNOLOGY` | technologies |
| `SYSTEM` | systems |
| `SOLUTION` | solutions |
| `ENTERPRISE` | enterprises |
| `MANUFACTURING` | *(no plural)* |
| `INDUSTRY` | industries |
| `EXPORT` | exports |
| `IMPORT` | imports |
| `CHEMICAL` | chemicals |
| `PHARMA` | *(abbreviation)* |
| `PHARMACEUTICAL` | pharmaceuticals |
| `FOOD` | foods |
| `AGRO` | *(abbreviation)* |
| `TEXTILE` | textiles |
| `RETAIL` | *(no plural)* |
| `CAPITAL` | *(no plural)* |

---

### Rule 5.2 — Descriptor Conflict = No Merge
**What it does:** When comparing two company names to see if they can merge, the system compares their descriptor sets.
- If **both have no descriptors** → Merge is allowed
- If **both have the exact same descriptors** → Merge is allowed
- If **descriptors differ at all** → Merge is BLOCKED

| Name 1 | Name 2 | Descriptor 1 | Descriptor 2 | Result |
|---|---|---|---|---|
| `Samsung Electronics` | `Samsung Food` | `{ELECTRONIC}` | `{FOOD}` | ❌ BLOCKED |
| `Tata Chemical` | `Tata Chemicals` | `{CHEMICAL}` | `{CHEMICAL}` | ✅ ALLOWED |
| `Acme Corp` | `Acme Limited` | `{}` | `{}` | ✅ ALLOWED |

---

## PART 6: GEOGRAPHIC MATCHER — Where Is the Company?
**File:** `processors/geographic_matcher.py`  
**Config:** `config/geography.py`

This module finds country or region names embedded inside company names and uses them to prevent merging branches from different countries.

---

### Rule 6.1 — Geographic Term Detection
**What it does:** Every word in the base name is checked against the geography list and tagged.

**Complete list of recognized geographic terms:**

| Region / Country | Terms Recognized |
|---|---|
| **India** | `INDIA`, `INDIAN` |
| **Asia (General)** | `ASIA`, `ASIAN` |
| **USA** | `USA`, `US`, `AMERICA`, `AMERICAN` |
| **UK** | `UK`, `BRITAIN`, `BRITISH` |
| **Europe** | `EUROPE`, `EUROPEAN` |
| **UAE** | `UAE`, `DUBAI` |
| **China** | `CHINA`, `CHINESE` |
| **Japan** | `JAPAN`, `JAPANESE` |
| **Korea** | `KOREA`, `KOREAN` |
| **Germany** | `GERMANY`, `GERMAN` |
| **France** | `FRANCE`, `FRENCH` |
| **Australia** | `AUSTRALIA`, `AUSTRALIAN` |
| **Canada** | `CANADA`, `CANADIAN` |
| **Southeast Asia** | `SINGAPORE`, `MALAYSIA`, `THAILAND`, `INDONESIA`, `VIETNAM`, `VN`, `BANGLADESH` |
| **Neutral / Global** | `GLOBAL`, `INTERNATIONAL`, `INTL`, `WORLDWIDE`, `MULTINATIONAL` |

---

### Rule 6.2 — Geography Merge Logic (3 Rules)
| Situation | Rule | Example | Result |
|---|---|---|---|
| Neither company has a geography term | **ALLOW** | `Tata Steel` vs `Tata Steel Ltd` | ✅ Merge |
| One has a geography term, the other has none | **ALLOW** (the un-tagged one can merge safely) | `Tata India` vs `Tata` | ✅ Merge |
| Both have geography terms and they are the same | **ALLOW** | `Tata India` vs `Tata Indian` | ✅ Merge |
| Both have geography terms but they are different | **BLOCK** | `Tata India` vs `Tata UK` | ❌ Block |

---

## PART 7: SINGULAR/PLURAL HANDLER — One Word, Many Spellings
**File:** `processors/singular_plural_handler.py`  
**Config:** `config/singular_plural.py`

This is the brain of the matching engine when it comes to treating "Chemical" and "Chemicals" as the same word. It is a 3-layer system that is extremely careful to avoid accidentally mangling brand names.

---

### Rule 7.1 — Layer 1: Protected Words (Absolute Banlist)
**What it does:** These words will NEVER be changed, no matter what. They are either proper brand names, foreign language words, country names, or legal concepts where the plural form IS the correct form.

**Complete Protected Words List:**

| Category | Words |
|---|---|
| **Short/Ambiguous Articles** | `MAS`, `LAS`, `LOS`, `DAS`, `DOS`, `DES`, `LES` (Spanish/Portuguese articles) |
| **Abbreviations/Invariants** | `GAS`, `BUS`, `MRS`, `GS`, `MS` |
| **Country Names** | `PHILIPPINES`, `MALDIVES`, `NETHERLANDS`, `HONDURAS`, `BAHAMAS`, `BARBADOS`, `BELIZE`, `AMERICAS`, `ANTILLES`, `EMIRATES`, `CANARIES` |
| **Foreign Proper Nouns** | `ALTAS`, `ATLAS`, `RIOS`, `LAOS`, `DUBOIS` |
| **Proper Surnames/Brands** | `ABBAS`, `HARRIS`, `JONES`, `JAMES`, `LEWIS`, `EVANS`, `DENNIS`, `ALEXIS`, `THOMAS`, `LUCAS`, `DALLAS`, `ROGERS`, `WALKERS`, `PHILIPS`, `SIEMENS`, `MARS`, `ROLLS`, `JACOBS`, `OWENS`, `MARTINS`, `REEVES` |
| **Semantically Invariant Words** | `OVERSEAS`, `GOODS`, `ILLINOIS`, `CHAMOIS` |
| **Invariant -ics Words** | `PHYSICS`, `ETHICS`, `ECONOMICS`, `MATHEMATICS`, `AEROBICS`, `ACOUSTICS`, `ATHLETICS`, `TACTICS` |

---

### Rule 7.2 — Layer 2: Explicit Whitelist (Verified Trade Pairs)
**What it does:** Built from 317,000+ real trade names. The system has a pre-verified lookup table of plural → singular translations for trade words. Words 4 characters or shorter always pass through unchanged (too risky to automate super short words).

**Complete Whitelist (organized by industry):**

**Chemicals & Materials:**
`ABRASIVES→ABRASIVE`, `ACIDS→ACID`, `ADDITIVES→ADDITIVE`, `ADHESIVES→ADHESIVE`, `ADSORBENTS→ADSORBENT`, `AMINES→AMINE`, `AROMATICS→AROMATIC`, `CAPSULES→CAPSULE`, `CERAMICS→CERAMIC`, `CHEMICALS→CHEMICAL`, `COATINGS→COATING`, `COLORANTS→COLORANT`, `COLORS→COLOR`, `COLOURS→COLOUR`, `COMPONENTS→COMPONENT`, `COSMETICS→COSMETIC`, `DENIMS→DENIM`, `DETERGENTS→DETERGENT`, `DIAGNOSTICS→DIAGNOSTIC`, `DYESTUFFS→DYESTUFF`, `EATABLES→EATABLE`, `ENZYMES→ENZYME`, `FABRICS→FABRIC`, `FERTILIZERS→FERTILIZER`, `FIBERS→FIBER`, `FIBRES→FIBRE`, `FLAVORS→FLAVOR`, `FLUIDS→FLUID`, `FOODSTUFFS→FOODSTUFF`, `FORMULATIONS→FORMULATION`, `FRAGRANCES→FRAGRANCE`, `GLOVES→GLOVE`, `INGREDIENTS→INGREDIENT`, `INSECTICIDES→INSECTICIDE`, `INSULATORS→INSULATOR`, `INTERMEDIATES→INTERMEDIATE`, `MATERIALS→MATERIAL`, `MEDICINES→MEDICINE`, `METALS→METAL`, `MICROELECTRONICS→MICROELECTRONIC`, `ORGANICS→ORGANIC`, `PAINTS→PAINT`, `PERFUMES→PERFUME`, `PESTICIDES→PESTICIDE`, `PETROCHEMICALS→PETROCHEMICAL`, `PHARMACEUTICALS→PHARMACEUTICAL`, `PHOSPHATES→PHOSPHATE`, `POLYMERS→POLYMER`, `ISOMERS→ISOMER`, `MONOMERS→MONOMER`, `EMULSIFIERS→EMULSIFIER`, `LUBRICANTS→LUBRICANT`, `HUMECTANTS→HUMECTANT`, `COAGULANTS→COAGULANT`, `FLOCCULANTS→FLOCCULANT`, `RETARDANTS→RETARDANT`, `ANTIOXIDANTS→ANTIOXIDANT`, `OXIDANTS→OXIDANT`, `SULFATES→SULFATE`, `SULPHATES→SULPHATE`, `NITRATES→NITRATE`, `SILICATES→SILICATE`, `CARBONATES→CARBONATE`, `ELASTOMERS→ELASTOMER`, `OLIGOMERS→OLIGOMER`, `COPOLYMERS→COPOLYMER`, `REMEDIES→REMEDY`, `RESINS→RESIN`, `SCIENCES→SCIENCE`, `SOLVENTS→SOLVENT`, `SUBSTANCES→SUBSTANCE`, `SURFACTANTS→SURFACTANT`, `SYNTHETICS→SYNTHETIC`, `TEXTILES→TEXTILE`, `TOILETRIES→TOILETRY`

**Business / Industry Descriptors:**
`ENTERPRISES→ENTERPRISE`, `ACCESSORIES→ACCESSORY`, `ACHIEVERS→ACHIEVER`, `AGENCIES→AGENCY`, `AIRLINES→AIRLINE`, `APPARELS→APPAREL`, `AUTOS→AUTO`, `BATTERIES→BATTERY`, `BEVERAGES→BEVERAGE`, `BISCUITS→BISCUIT`, `BROKERS→BROKER`, `CABLES→CABLE`, `CANDLES→CANDLE`, `COATS→COAT`, `COMMODITIES→COMMODITY`, `CONSULTANTS→CONSULTANT`, `CONTRACTORS→CONTRACTOR`, `DAIRIES→DAIRY`, `DEVICES→DEVICE`, `DISTRIBUTORS→DISTRIBUTOR`, `ENGINEERS→ENGINEER`, `EXPORTERS→EXPORTER`, `EXPORTS→EXPORT`, `FASHIONS→FASHION`, `FOODS→FOOD`, `FORWARDERS→FORWARDER`, `GARMENTS→GARMENT`, `IMPORTERS→IMPORTER`, `IMPORTS→IMPORT`, `INDIVIDUALS→INDIVIDUAL`, `INDUSTRIES→INDUSTRY`, `INFRASTRUCTURES→INFRASTRUCTURE`, `INSTRUMENTS→INSTRUMENT`, `LABORATORIES→LABORATORY`, `MANUFACTURERS→MANUFACTURER`, `MERCHANTS→MERCHANT`, `MILLS→MILL`, `PROCESSORS→PROCESSOR`, `PRODUCTS→PRODUCT`, `RELATIONS→RELATION`, `RESTAURANTS→RESTAURANT`, `SALES→SALE`, `SPECIALTIES→SPECIALTY`, `SPORTS→SPORT`, `SUPPLIERS→SUPPLIER`, `SUPPLIES→SUPPLY`, `SURFACES→SURFACE`, `TECHNOLOGIES→TECHNOLOGY`, `TRADERS→TRADER`, `TRANSFORMERS→TRANSFORMER`, `UNITS→UNIT`, `VENTURES→VENTURE`, `WHOLESALERS→WHOLESALER`, `TIRES→TYRE`, `TYRES→TYRE`, `TYRE→TYRE`, `DYEING→DYE`, `DYES→DYE`

`SONS→SON`, `BROTHERS→BROTHER`, `ASSOCIATES→ASSOCIATE`, `PARTNERS→PARTNER`, `HOLDINGS→HOLDING`, `COMMUNICATIONS→COMMUNICATION`, `DYNAMICS→DYNAMIC`, `ELECTRONICS→ELECTRONIC`, `GRAPHICS→GRAPHIC`, `DREAMERS→DREAMER`, `STREAMERS→STREAMER`, `PRIMERS→PRIMER`, `FARMERS→FARMER`, `TIMERS→TIMER`, `SWIMMERS→SWIMMER`, `TRIMMERS→TRIMMER`, `PERFORMERS→PERFORMER`, `REFORMERS→REFORMER`, `INFORMERS→INFORMER`, `STATES→STATE`, `HEADQUARTERS→HEADQUARTER`, `LOGISTICS→LOGISTIC`

**Foreign / Multilingual Corrections:**
`QUMICA→QUIMICA`, `QUMICAS→QUIMICA`, `QUIMICAS→QUIMICA`, `LABORATORIAI→LABORATORY`, `LABORATORIAIS→LABORATORY`, `INDUSTRIAS→INDUSTRY`, `INDUSTRIAL→INDUSTRY`

---

### Rule 7.3 — Layer 3: Safe Suffix Patterns (Future-Proofing for New Science Words)
**What it does:** For any new scientific compound word that isn't in the whitelist yet, a set of safe suffix patterns automatically handles it — but each pattern has a strict minimum word-length threshold to avoid false matches on short or common English words.

| Pattern | Minimum Length | Example Words | Transformation |
|---|---|---|---|
| ends in `ICALS` (≥9 chars) | 9 | `CHEMICALS`, `PHARMACEUTICALS` | Remove `ICALS` → add `ICAL` |
| ends in `IZERS` (≥9 chars) | 9 | `FERTILIZERS`, `OXIDIZERS` | Remove `IZERS` → add `IZER` |
| ends in `ISERS` (≥9 chars) | 9 | `STABILISERS`, `OXIDISERS` | Remove `ISERS` → add `ISER` |
| ends in `FIERS` (≥10 chars) | 10 | `EMULSIFIERS`, `HUMIDIFIERS` | Remove `FIERS` → add `FIER` |
| ends in `MERS` (≥9 chars) | 9 | `ELASTOMERS`, `BIOPOLYMERS` | Remove `MERS` → add `MER` |
| ends in `OLOGIES` (≥10 chars) | 10 | `TECHNOLOGIES`, `BIOTECHNOLOGIES` | Remove `OLOGIES` → add `OLOGY` |
| ends in `ICIDES` (≥10 chars) | 10 | `FUNGICIDES`, `HERBICIDES` | Remove `ICIDES` → add `ICIDE` |
| ends in `PHATES` (≥8 chars) | 8 | `SULPHATES`, `PHOSPHATES` | Remove `PHATES` → add `PHATE` |
| ends in `LICATES` (≥9 chars) | 9 | `SILICATES` | Remove `LICATES` → add `LICATE` |
| ends in `BONATES` (≥10 chars) | 10 | `CARBONATES` | Remove `BONATES` → add `BONATE` |

---

### Rule 7.4 — Layer 4: Safe Default (No Change)
**What it does:** If a word doesn't match any layer above, it is returned unchanged. This is the most important safety rule of all — when in doubt, do nothing.

---

## PART 8: WORD ORDER NORMALIZER — Jumbled Spelling Detection
**File:** `processors/word_order_normalizer.py`

Two people entering the same company name will sometimes write the words in a different order. This module detects those cases.

---

### Rule 8.1 — Word Set Fingerprinting
**What it does:** Both names have their words upper-cased and put into an unordered set (a bag of words). If the two bags are identical, the names are considered word-order variants of each other.

| Name 1 | Name 2 | Word Set 1 | Word Set 2 | Match? |
|---|---|---|---|---|
| `Tata Chemical Magadhi` | `Tata Magadhi Chemical` | `{TATA, CHEMICAL, MAGADHI}` | `{TATA, MAGADHI, CHEMICAL}` | ✅ Yes |
| `Dow Chemical India` | `India Dow Chemical` | `{DOW, CHEMICAL, INDIA}` | `{INDIA, DOW, CHEMICAL}` | ✅ Yes |
| `Tata Steel` | `Steel Tata Iron` | `{TATA, STEEL}` | `{STEEL, TATA, IRON}` | ❌ No (different word count) |

---

## PART 9: THE MERGE ENGINE — The Core Matching Brain
**File:** `core/merge_engine.py`

This is where all the individual rules above come together. It compares every pair of company names and decides whether they represent the same company. It uses a mathematical technique called "Union-Find" for efficiency. Think of it as a sorting office that puts all variations of the same company into the same box.

---

### Rule 9.1 — Pre-Scan for Global Suffix Conflicts
**What it does:** Before comparing any names, the engine first builds a global map of all legal suffix families present for each base name. This tells it which bases have multiple suffix types so that merging decisions can be smarter.

---

### Rule 9.2 — Legal Family Matching (The "Type" Compatibility Check)
Two companies can only merge if their legal types are compatible. Full logic:

| Situation | Rule | Example |
|---|---|---|
| Both have the same family | ✅ MERGE | `Tata LLC` + `Tata LLC` |
| One has a suffix, the other has none | ✅ MERGE (inherits) | `Tata PLd` + `Tata` |
| `LIMITED_FAMILY` vs `PRIVATE_LIMITED_FAMILY` | ✅ MERGE (hierarchical — both are "Limited" types) | `Tata Limited` + `Tata Private Limited` |
| `LIMITED_FAMILY` vs `CO_LIMITED_FAMILY` | ✅ MERGE (hierarchical) | `Tata Limited` + `Tata Co Limited` |
| `LLC` vs `GmbH` (unrelated types) | ❌ BLOCK | `Tata LLC` + `Tata GmbH` |
| `PRIVATE_LIMITED` vs `LLC` | ❌ BLOCK | `Tata Pvt Ltd` + `Tata LLC` |

---

### Rule 9.3 — Space-Only Check (Compound Word Test)
**What it does:** If two base names are identical when all internal spaces are removed, they are merged immediately. This check happens BEFORE descriptor checking because a spacing difference is not a real industry difference.

| Name 1 | Name 2 | After removing spaces | Match? |
|---|---|---|---|
| `BIO ENERGY` | `BIOENERGY` | `BIOENERGY` = `BIOENERGY` | ✅ MERGE |
| `AGRO CHEMICALS` | `AGROCHEMICALS` | `AGROCHEMICALS` = `AGROCHEMICALS` | ✅ MERGE |

---

### Rule 9.4 — Functional Descriptor Check (Industry Fence)
**What it does:** If base names don't share exact industry words, merge is blocked. (Full details in Part 5 above.)

---

### Rule 9.5 — Base Name Comparison (4 Sub-Rules)
After passing the above checks, the actual base names are compared. They merge if any ONE of these 4 conditions holds:

1. **Exact match:** Base names are letter-for-letter identical.
2. **Word order variant:** Same words, different order (Rule 8.1 above).
3. **Singular/plural variant:** Names are identical in word count but differ only in approved singular/plural pairs (Rule 7 above).
4. **AND/PVT/LTD variant:** When the only difference between names is the presence or absence of the words `And`, `Private`, or `Limited` (including when these are embedded into another word like `Salesprivate`).

---

### Rule 9.6 — AND/PVT/LTD Merge Logic (Medium Confidence)
**What it does:** When names differ ONLY by the words `And`, `Private`, or `Limited`, they are grouped together. The key rule is that the core letters of the name (after removing all spaces and removing AND/PRIVATE/LIMITED) must be identical.

This merge is given "Medium" confidence and automatically raises a Review Flag telling the user to double-check.

| Name 1 | Name 2 | Core 1 | Core 2 | Decision |
|---|---|---|---|---|
| `Smith Brothers Limited` | `Smith Brothers` | `SMITHBROTHERS` | `SMITHBROTHERS` | ✅ MERGE (Medium Conf.) |
| `Tata and Sons` | `Tata Sons` | `TATASNS` | `TATASNS` | ✅ MERGE (Medium Conf.) |

---

### Rule 9.7 — Geographic Compatibility Check
**What it does:** The final guard. Even if all other rules align, if both names have recognized geography tags that are different, the merge is blocked. (Full details in Part 6 above.)

---

## PART 10: CANONICAL NAME GENERATOR — Electing the Master Name
**File:** `core/canonical_generator.py`

Once a merge group is formed, a single "Standardised Name" must be chosen as the master.

---

### Rule 10.1 — Quality Score (8 Dimensions)
Every candidate in a group is scored across 8 criteria. The highest scorer wins.

| Dimension | What It Checks | Points |
|---|---|---|
| **Has Legal Suffix** | Does the name have a proper legal suffix like `Private Limited`? | 1 if yes, 0 if no |
| **Suffix Completeness** | `PRIVATE LIMITED` scores 3, `CO LIMITED` scores 3, `LIMITED` scores 2, other suffix scores 1, no suffix = 0 | 0-3 |
| **No Brackets** | If the cleaned name contains `(` or `)`, it scores lower | 1 if no brackets, 0 if brackets exist |
| **No Single-Letter Words** | If the base name has a lone letter like `I`, `P`, or `A`, it scores lower | 1 if clean, 0 if stray letter found |
| **Word Count** | More words = more complete name | 1 point per word |
| **No Trailing Artifact** | Last word should not be a stray digit or short code | 1 if clean, 0 if artifact |
| **Suffix Spelled Out** | Fully spelled-out suffix (`Limited`) beats abbreviation (`Ltd`) | 1 if full, 0 if abbreviated |
| **Character Length** | Longer character count in base name = tiebreaker | Length of base text |

**Example:** Group contains `Acme`, `Acme Pvt`, `Acme Private Limited`:
- `Acme`: Score = 0, 0, 1, 1, 1, 1, 1, 4 = low
- `Acme Pvt`: Score = 1, 1, 1, 1, 2, 1, 0, 7 = medium
- `Acme Private Limited`: Score = 1, 3, 1, 1, 3, 1, 1, 15 = **WINNER** ✅

---

### Rule 10.2 — Compound Word Normalization
**What it does:** Space-separated compound science prefixes are collapsed to solid form:

| Prefix Words | Collapses To |
|---|---|
| `BIO ENERGY` | `BIOENERGY` |
| `AGRO CHEMICALS` | `AGROCHEMICALS` |
| `PETRO CHEM` | `PETROCHEM` |

Covered Prefixes: `BIO`, `AGRO`, `CHEMO`, `PETRO`, `AERO`, `HYDRO`, `ELECTRO`, `MICRO`, `MACRO`, `NANO`, `POLY`, `AGRI`, `PHARMA`

---

### Rule 10.3 — Suffix Forcing
**What it does:** After the best base name is elected, the system forces the most appropriate suffix onto the end by looking at what legal types exist within the whole group.

| Family Priority | Rule | Output |
|---|---|---|
| `CO_LIMITED_FAMILY` present | Use `CO LIMITED` | `Tata Co Limited` |
| `PRIVATE_LIMITED_FAMILY` + at least one member explicitly had `PRIVATE LIMITED` | Use `PRIVATE LIMITED` | `Tata Private Limited` |
| `PRIVATE_LIMITED_FAMILY` but no explicit `PRIVATE LIMITED` found | Use `LIMITED` | `Tata Limited` |
| `LIMITED_FAMILY` only | Use `LIMITED` | `Tata Limited` |

---

### Rule 10.4 — AND/PVT/LTD Special Canonical Building
**What it does:** For groups merged under the AND/PVT/LTD rule, the canonical name is built from the longest member in the group and then has any AND/PRIVATE/LIMITED words from other members inserted in their natural position.

---

### Rule 10.5 — Final Title Case Formatting
Every final canonical name is converted to Title Case before being placed in the output.

| Raw Canonical | Final Output |
|---|---|
| `TATA PRIVATE LIMITED` | `Tata Private Limited` |
| `DOW CHEMICAL INDIA` | `Dow Chemical India` |

---

## PART 11: CONFIDENCE SCORER — How Trustworthy is the Result?
**File:** `core/confidence_scorer.py`  
**Shared Resource:** `config/shared.py`

Every final standardized name is given a confidence score: **High**, **Medium**, or **Low**. The score drives the "Review Flag" that tells users which rows need manual checking.

---

### Rule 11.1 — AND/PVT/LTD Auto-Medium
**What it does:** If the groups were merged specifically due to the AND/PVT/LTD rule, those rows are ALWAYS given Medium confidence, regardless of every other check.

---

### Rule 11.2 — Confidence Scoring (Point System)
Points are added for each detected issue. Final score determines the level.

| Issue Detected | Points Added | Example |
|---|---|---|
| **Unknown legal suffix** (suffix was found but not in the family dictionary) | +2 | A rare foreign suffix not in the mapping |
| **Missing legal suffix** (name has no legal form at all) | +1 | `Tata Steel` with no Ltd/LLC/etc |
| **Address was stripped** (a building/floor word was found and removed) | +1 | `Samsung Floor 3` → stripped floor |
| **More than 3 prefixes stripped** (too many messy trade tags) | +1 | `M/S On Behalf Of Notify Tata` |
| **Single-character letter word in base** (sign of data corruption) | +1 | `Tata I Steel`, `XYZ P Limited` |
| **Merged keyword detected** (legal term fused to a word without space) | +1 per issue | `INDIAPRIVATE`, `PVTLTD` |
| **Industry typo detected by spellchecker** | +1 | `Chemicla` instead of `Chemical` |

**Final Score → Confidence Level:**
- Score = 0 → **HIGH** (No Review Flag)
- Score 1-2 → **MEDIUM** (Review Flag: YES)
- Score 3+ → **LOW** (Review Flag: YES)

---

### Rule 11.3 — Smart Industry Typo Detection (Efficiency Rule)
**What it does:** The spellchecker only runs on words longer than 3 characters AND only on words whose first 3 letters match a known industry term prefix. This is a performance optimization — brand names like `Adiva` or `Aglo` are totally skipped without wasting processing time, because the system only cares about typos in known industry terms.

**Industry term prefixes watched:** `pol`, `che`, `ind`, `ser`, `tec`, `sol`, `ent`, `pro`, `res`, `hol`, `ven`, `com`, `pla`, `met`, `ste`, `pow`, `ene`, `log`, `tra`, `con`, `bui`, `dev`, `inf`, `agr`, `pha`, `hea`, `med`, `tex`, `fab`, `sys`, `eng`

---

## PART 12: SUBSET DETECTION — Catching Umbrella Brands
**Logic inside:** `app.py`

After all standardized names are assembled, the system does a final check to find cases where one company's name is fully contained inside another company's name.

---

### Rule 12.1 — Contiguous Subset Match
**What it does:** The system adds a space before and after every unique standardized name, then checks if any padded name appears completely inside another padded name. This "padding" ensures the match is at whole-word boundaries.

| Name A (padded) | Name B | Subset Found? |
|---|---|---|
| ` samsung ` | `Samsung Electronics Ltd` | ✅ YES — both highlighted |
| ` tata ` | `Tata Chemical India` | ✅ YES — both highlighted |
| ` acme ` | `Acmex Corp` | ❌ NO — "acme" not a full-word match inside "acmex" |

---

### Rule 12.2 — Confidence Downgrade for Subsets
**What it does:** If a subset match is found and the name has "High" confidence, it is automatically downgraded to "Medium" and Review Flag is set to "YES". This guarantees the user always sees subset-involved names for manual review.

---

## PART 13: AI REFINER — Smart Spell-Check for Edge Cases
**File:** `processors/ai_refiner.py`

The AI step is optional. It only activates if an API key is configured. It processes only the Medium and Low confidence names.

---

### Rule 13.1 — Who Gets Sent to AI
Only canonical names that resulted in a "Medium" or "Low" confidence score are batched for the AI. High confidence names are never sent.

---

### Rule 13.2 — AI Prompt Rules (What the AI Is Instructed to Do)
The AI is given a structured set of 10 rules to follow precisely:

| Rule # | AI Instruction |
|---|---|
| **1. Spelling & Dialect** | Fix typos. Example: `Limted → Limited`, `Tyre → Tire`, `Impex → Import And Export`, `Intl → International` |
| **2. No Translation** | DO NOT translate foreign business words. `Industria` stays `Industria`. `Comercio` stays `Comercio`. |
| **3. Geography Expansion** | Expand geography codes. Example: `Industry Vn Co → Industry Vietnam Co` |
| **4. Strip Trailing Noise** | Remove branch names and incorporation years. Example: `Acme Corp Branch In Dubai 1998 → Acme Corp` |
| **5. Brand Name Protection** | DO NOT expand unique portmanteau brand names. `Polychem` stays `Polychem`. `Pharmbutor` stays `Pharmbutor`. |
| **6. Compound Word Protection** | DO NOT split or expand compound words. `Bio Chem` stays `Bio Chem`. `Bio Energy` stays `Bio Energy`. |
| **7. No Unicode** | Convert ALL accented / Unicode characters to plain ASCII. `Ö → O`, `ç → c`, `é → e`. |
| **8. Legal Suffix Protection** | Do NOT change correct legal suffixes. `Pvt Ltd`, `Limited`, `LLC`, `Inc` etc. stay untouched. |
| **9. Perfect Names Unchanged** | If the name is already clean, return it exactly as received. |
| **10. Output Format** | Output one line per company in exact format: `Original|Refined` (pipe-separated). |

---

### Rule 13.3 — AI Processing Batch Size
**What it does:** Names are processed in batches of 50 at a time (for API efficiency and to avoid timeouts). Each batch has a 30-second timeout.

---

### Rule 13.4 — AI Fallback (Graceful Error Handling)
**What it does:** If the AI proxy server is unavailable or rate-limited, the system silently falls back to the rule-based result. No hard crash. Error categories:
- `500/502/503/504` → Proxy server down → Returns names unchanged, shows warning in UI
- `429` → Rate limited → Waits 5 seconds and retries
- Other errors → Falls back silently per name

---

### Rule 13.5 — AI Output Re-Processing
**What it does:** After the AI returns a refined name, that result is passed BACK through the full Rule-Based pipeline (Text Cleaning, Suffix Extraction, Singular/Plural). This ensures the AI output is always consistent with the system's own normalization standards.

---

## PART 14: SHARED NLP SINGLETON — Memory Management
**File:** `config/shared.py`

Not a pipeline step, but an important infrastructure rule.

---

### Rule 14.1 — Single Instance Per Session
**What it does:** The SpellChecker and `inflect` engine are loaded once when the application starts. All modules share the same instance. This prevents the same dictionary (tens of thousands of words) from being loaded into memory repeatedly for each row, which would make the app far too slow.

---

### Rule 14.2 — Custom Industry Dictionary
**What it does:** On startup, the shared spellchecker is taught a small list of standard industry compound words that are not in the default English dictionary:
- `polyplastic`
- `agrochemical`
- `petrochemical`
- `technologie`

This prevents these legitimate industry words from being flagged as misspellings.

---

## QUICK SUMMARY — The Full Flow in One Table

| Step | Module | What Happens |
|---|---|---|
| 1 | `text_cleaner.py` | Strip aliases, replace `&`, mask punctuation, Clean/Trim/Proper, expand abbreviations, Clean/Trim/Proper again |
| 2 | `address_remover.py` | Strip trailing building/floor/plot/unit info from right end |
| 3 | `prefix_remover.py` | Strip leading trade/shipment/business prefixes from left end |
| 4 | `legal_suffix_normalizer.py` | Extract legal suffix, produce clean base name, assign Legal Family |
| 5 | `descriptor_checker.py` | Tag functional industry words on the name |
| 5 | `geographic_matcher.py` | Tag country/region words on the name |
| 6 | `merge_engine.py` | Cross-compare every pair with 4 sequential rules, groups into clusters |
| 7 | `canonical_generator.py` | Elect best-quality name per cluster, force correct suffix |
| 8 | `app.py` (subset logic) | Detect and flag umbrella-brand subsets |
| 9 | `confidence_scorer.py` | Score each result, assign High/Medium/Low, set Review Flag |
| 10 | `ai_refiner.py` | (Optional) Refine Medium/Low names via Gemini AI |
| 11 | `app.py` (output logic) | Assemble final DataFrame with all columns, download as CSV/Excel |

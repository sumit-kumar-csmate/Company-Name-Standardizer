# Company Name Normalization Tool v2.1 — Complete Pipeline Documentation

## 1. Overview
The **Company Name Normalization Tool** is a robust, deterministic, rule-based data cleansing pipeline designed to standardize international trade data company names. Its primary architectural goal is to be **VLOOKUP-friendly**. It never modifies the original data column but instead appends a `"Standardised Name"` column right next to the original, accompanied by confidence scores and review flags.

The system is highly optimized and relies on a series of strictly ordered text-processing modules, ending with a smart grouping engine (Union-Find) and an optional AI-driven refinement step for edge cases.

---

## 2. Execution Sequence (High-Level)
When processing a batch of names, the system executes in the following strict order:
1. **Per-Name Processing (Stages 1 through 5):** Text is cleaned, addresses/prefixes are stripped, legal suffixes are extracted, and meta-features (descriptors/geography) are identified.
2. **Merging Engine (Stage 6):** Processed variations are cross-compared and grouped using a Union-Find algorithm based on structural similarities.
3. **Canonical Generator (Stage 7):** A single master "Standardised Name" is generated for each merged group by electing the highest-quality candidate.
4. **Confidence & Subset Detection (Stage 8 & 9):** Scores are assigned (High, Medium, Low), and nested firm identities (subsets) are flagged.
5. **AI Refinement (Stage 10):** (Optional) Only "Medium" and "Low" confidence names are routed through an LLM (Gemini) for advanced typo/logic correction.
6. **Output Assembly:** Final DataFrame is assembled and formatted.

---

## 3. Detailed Step-by-Step Processing Rules

### Stage 1: Text Cleaning (`text_cleaner.py`)
This foundational step ensures all strings are uniform before logic rules apply.
* **Alias Stripping:** Detects trailing aliases by stripping out anything placed after keywords like `Trading As`, `T/A`, `T A`, or `DBA`.
* **Symbol Replacement:** `&` is converted to `and`.
* **Punctuation Padding:** All other punctuation marks (e.g., `,`, `.`, `/`, `;`, `-`, `_`, `(`, `)`) are replaced with exactly **four spaces**. This is critical to ensure that joined words (e.g., `Tech.Ltd`) safely break apart into distinct word tokens (`Tech` and `Ltd`).
* **Clean/Trim/Proper Case:** Collapses all multiple spaces down to a single space, strips trailing/leading edges, and converts the whole string to standard `Title Case`.
* **Abbreviation Expansion:** A strict regex map expands short-hand:
  * `Pvt` / `Pte` / `Priv` → `Private`
  * `Ltd` / `Ltda` / `Limitada` → `Limited`
  * `Corpn` / `Corp` → `Corporation`
  * `Company` → `Co`
  * `Mfg` → `Manufacturing`
  * `Bros` → `Brothers`
* **Final Reclean:** A second pass of Clean/Trim collapses any hanging spaces introduced during abbreviation expansion.

### Stage 2: Address Stripping (`address_remover.py`)
Removes trailing address chunks to expose the actual company shell.
* **Rule:** It scans the very right end (tail) of the string for address keywords (`BUILDING`, `FLOOR`, `BLOCK`, `PLOT`, `STREET`, `ZONE`, `PHASE`, `NEAR`, `OPPOSITE`). 
* If found, these words are peeled off. It also automatically removes trailing numeric digits or short alphanumeric unit codes (e.g., `B12`, `A4`) that come after an address keyword.
* *Note: Does NOT strip Geographic terms (like India, UK)*.

### Stage 3: Prefix Stripping (`prefix_remover.py`)
Removes introductory trade words from the very beginning (head) of the string.
* **Rule:** Finds and removes terms like `M/S`, `MESSRS`, `SUPPLIER`, `TO ORDER OF`, `ON BEHALF OF`. 

### Stage 4: Legal Suffix Extraction & Normalization (`legal_suffix_normalizer.py`)
With the "Base Name" clear of junk, the system extracts the corporate legal structure.
* **Rule:** Scans the exact end of the string against a massive dictionary of global legal suffixes (`LLC`, `GMBH`, `LTD`, `PRIVATE LIMITED`, `INC`, `PTY`, `SA`, `SPA`, etc.).
* If found, the suffix is stripped away entirely, yielding the pristine **base_name**.
* The extracted suffix is then normalized into a global **Legal Family** (e.g., parsing both `Pvt Ltd` and `PTE` into `PRIVATE_LIMITED_FAMILY`), which is heavily utilized later during merging.

### Stage 5: Feature Extraction (Descriptors & Geography)
Meta-tags are tagged onto the object for safety checks during merging.
* **Functional Descriptors (`descriptor_checker.py`):** Identifies industry keywords (e.g., `CHEMICALS`, `MACHINERY`, `ELECTRONICS`). This prevents `Samsung Electronics` from improperly merging with `Samsung Chemicals`.
* **Geographical Matcher (`geographic_matcher.py`):** Identifies regions (e.g., `INDIA`, `USA`, `LONDON`). This prevents `Tata India` from improperly merging with `Tata UK`.

---

### Stage 6: The Merging Engine (`merge_engine.py`)
Uses highly optimized `Union-Find` graph logic to build clusters of identical companies. Two names merge **only if all** of the following sub-rules align:

1. **Rule 1 - Legal Families Match:**
   * Both have the same family (e.g., both are `LLC_FAMILY`), OR one has a suffix while the other doesn't (a missing suffix safely inherits the group's suffix). 
   * *Special Exception:* It natively handles hierarchical overlaps (e.g. successfully merging `Tata Limited` and `Tata Private Limited`).
2. **Rule 1b - Space-Only Difference:** 
   * If two base names are identical when spaces are removed (e.g., `BIOENERGY` vs `BIO ENERGY`), they merge aggressively (High Confidence).
3. **Rule 2 - Functional Descriptors Match:**
   * Must not have clashing industries.
4. **Rule 3 - Base Name Alignment:**
   * **Exact Match:** The base names match exactly.
   * **Word-Order Variance:** The base names match if words are sorted alphabetically (`Tata Chemical Magadhi` == `Tata Magadhi Chemical`).
   * **Singular/Plural Unification:** Base names differ *only* by pluralization (`Chemical` vs `Chemicals`). *See Hybrid System below*.
   * **AND/PVT/LTD Variation:** Base names are identical except for alternating use of the words `And`, `Private`, or `Limited`. These are grouped but flagged for "Medium" confidence.
5. **Rule 4 - Geographic Match:**
   * Must not have clashing country/region tags.

#### The Hybrid Singular/Plural System (`singular_plural.py`)
An ultra-safe, deterministic, 3-layer system replaces risky NLP libraries:
* **Layer 1: Protected Words:** An absolute banlist of proper nouns (`PHILIPS`, `SIEMENS`, `TEXAS`), foreign states/names (`NETHERLANDS`, `PHILIPPINES`), and legal structures (`BROTHERS`, `SONS`) that must *never* be made singular.
* **Layer 2: Explicit Whitelist:** Exact mapping of verified trade pairs (e.g., `ACCESSORIES` → `ACCESSORY`, `TIRES` → `TYRE`).
* **Layer 3: Safe Pattern Suffixes:** Future-proof regex rules with mandatory *length thresholds* that auto-singularize pure chemistry compounds (e.g., `...ICALS` → `...ICAL`, `...MERS` → `...MER`, `...IZERS` → `...IZER`).

---

### Stage 7: Canonical Name Generation (`canonical_generator.py`)
A master name must be elected for each Union-Find cluster.
* **Scoring Logic:** Every name in a cluster is put through a `_quality_score` function taking 8 dimensions into account (Has legal suffix, fully spelled-out suffix, no brackets, word count, character length, no stray single digits, etc.). 
* **The Winner:** The candidate with the highest structural completeness score is elected as the "master" Base Name.
* **Suffix Forcing:** The engine evaluates the distinct suffixes within the group and forcibly bolts the best, most descriptive legal suffix onto the end of the master base name.

### Stage 8: Subset Detection (Logic inside `app.py`)
After all unique Standardized Names are built, the pipeline pads them with spaces and checks for direct string overlaps. 
* If Company A is fully contained sequentially inside Company B (e.g. `Samsung` contained within `Samsung Electronics Limited`), **both** are flagged as "Subset Highlight: YES". 
* This warns the user that multiple entities exist under an umbrella brand name.

### Stage 9: Confidence Scoring (`confidence_scorer.py`)
Evaluates the final group construction and sets human review triggers:
* **High Confidence:** Perfect base name match, proper suffixes intact, rules cleanly aligned.
* **Medium / Low Confidence:** Triggers a **"Review Flag: YES"** if:
  * The merged reason was strictly an `AND/PVT/LTD` mismatch.
  * A legal suffix was completely missing.
  * More than 3 trade prefixes were stripped (spaghetti name).
  * A random 1-character letter exists in the base name.
  * A merged keyword exists inappropriately (e.g., `INDIAPRIVATE`).
  * The Singleton NLP spellchecker (`shared.py`) flags an industry phrase as being purely misspelled (e.g., `Chemicla` instead of `Chemical`).

### Stage 10: AI Refinement (`ai_refiner.py`) — Optional
If an API key is provided and the toggle is enabled in the UI:
* It groups all "Medium" and "Low" confidence master names into batches.
* Sends them through a secure custom proxy directly to Google's `Gemini-2.5-flash` model.
* **The Prompt Goal:** Deep semantic reasoning to remove invisible typos, clear unreadable noise/symbols, translate foreign encodings, and provide the perfect canonical name. 
* Outputs are then passed *back* right through the Base rules to ensure AI outputs remain consistent with strict normalization standards.

### Stage 11: Output Assembly (`app.py`)
The pipeline takes the user's original Excel/CSV file and splices new data in:
1. `Original Column` — Passed through 100% implicitly untouched.
2. `Standardised Name` — Bolted beside the original column (ideal for immediate `=VLOOKUP()`).
3. `Confidence Score` — (High/Medium/Low).
4. `Review Flag` — (YES for manual supervision).
5. `AI Verified Name` — Provided if the AI actively altered the canonical logic.
6. `Subset Highlight` — Hidden from Excel view but used for conditional formatting in the UI.

### The Shared NLP Singleton (`shared.py`)
Implemented for speed and resource management. Instead of instantiating `pyspellchecker` on every row iteration, `shared.py` initializes the dictionary ONE time safely at application boot. This keeps RAM consumption microscopic and eliminates hot-path delays when calculating Industry Typo tracking.

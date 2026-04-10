"""
Gemini AI refiner — optional final-pass cleanup for flagged names.
Only processes Medium / Low confidence names.
Falls back gracefully if API is unavailable.

Fallback model chain: tries each model in FALLBACK_MODELS order until one works.
If ALL fail, every name maps to itself (safe no-op).
"""

import time
import difflib
from openai import OpenAI

# ── Model fallback chain — tried in order until one succeeds ─────────────────
# Fastest/cheapest models first; more capable ones as fallbacks.
FALLBACK_MODELS = [
    "gemini-2.5-flash",
]

def group_similar_names(names: list) -> list:
    unique = list(dict.fromkeys(names))
    unique.sort()
    n = len(unique)
    
    # Use Union-Find for transitive grouping
    parent = list(range(n))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
        
    def union(i, j):
        root_i, root_j = find(i), find(j)
        if root_i != root_j:
            parent[root_j] = root_i

    # Matrix comparison for 15-char 70% similarity
    for i in range(n):
        name1 = unique[i]
        prefix1 = name1[:15].lower()
        for j in range(i + 1, n):
            name2 = unique[j]
            prefix2 = name2[:15].lower()
            
            # Calculate 70% similarity on JUST the first 15 characters
            similarity = difflib.SequenceMatcher(None, prefix1, prefix2).ratio()
            if similarity >= 0.70:
                union(i, j)
                    
    # Construct groups from roots
    group_map = {}
    for i in range(n):
        root = find(i)
        group_map.setdefault(root, []).append(unique[i])
        
    return list(group_map.values())


_PROMPT = """You are a data-cleaning expert for international trade data.
Fix spelling errors, standardise minor formatting, and strip extraneous branch data.

Rules:
1. SPELLING & DIALECT ALIGNMENT: Fix typos (e.g. "Limted" → "Limited"). Unify dialects and standard trade abbreviations (e.g., "Tyre" → "Tire", "Impex" → "Import And Export", "Intl" → "International").
2. DO NOT TRANSLATE: Strictly DO NOT translate foreign business names or words (like Industria, Comercio) into English. Maintain their original language, spelling, and structure natively.
3. GEOGRAPHY UNIFICATION: Expand geography abbreviations perfectly. If a geographic code like "Vn" sits inside the name (e.g., "Industry Vn Co"), safely expand it to "Vietnam" and format structurally.
4. STRIP NOISE (BRANCHES/YEARS): Completely remove trailing branches (e.g., "Branch In Binh Duong") AND stray incorporation years (e.g., "1949", "1998") from the company name.
5. STRICT PORTMANTEAU PROTECTION: DO NOT attempt to expand ANY unique business portmanteaus or distinct non-dictionary brand names (e.g., "Techno", "Pharmbutor", "Polychem"). Only translate/standardise STANDARD business nouns.
6. COMPOUND WORD PROTECTION: DO NOT expand or split compound science/industry words. For example, "Bio Chem" must stay "Bio Chem" — do NOT change it to "Biochemical". "Bio Energy" must stay "Bio Energy" — do NOT change it to "Bioenergy". Preserve the exact compound word tokens as-is.
7. NO UNICODE/DIACRITICS: ALWAYS output using standard English alphabets (A-Z) only. Transliterate any unicode characters or diacritics (e.g., "Ö" -> "O", "ç" -> "c") into their standard ASCII Latin equivalents.
8. STRICT LEGAL SUFFIX PRESERVATION: Do NOT change correct legal suffixes (Pvt Ltd, Limited, LLC, Inc, Corp, DP, etc.). DO NOT merge names that have fundamentally different legal entities/suffixes (e.g., "Adeline Chemical DP" vs "Adeline Chemical LLC", or "Company Inc" vs "Company LLC"). Keep them as distinct outputs.
9. INTELLIGENT UNIFICATION & NOISE REMOVAL: The input is provided in groups of similar names. Examine each group carefully. If multiple names in a group represent the same company—even if they differ by NTN numbers, tax IDs, bank account details, addresses, or geographic locations—you MUST unify them to the exact same Refined name.
    *   DROP ONLY banking/payment noise: If a company name is appended with ONLY a bank name (e.g., "... & Faysal Bank", "... & HBL"), drop that bank appendage as NOISE.
    *   KEEP ALL LOGISTICS / SUPPLY CHAIN DATA: NEVER drop trailing text if it refers to logistics, shipping, or supply chain operators (like "UPS Supply Chain Solutions", "Logistik", etc.). Keep the entire name exactly as is.
    *   KEEP "Trading As" aliases intact: If a name contains "Trading As", "T/A", or "DBA" followed by a trade name (e.g., "Ab Agri Limited Trading As Trident Feeds"), KEEP the full name exactly. Do NOT strip the alias.
    *   KEEP co-entities and joint ventures: If a name connects two distinct legal entities via "And" (e.g., "Apical M Sdn Bhd And Syarikat Logistik Petikemas Sdn Bhd"), KEEP the full name. Do NOT drop the second entity even if it is a logistics, shipping, or subsidiary company.
    *   ONLY keep entries as different outputs if they differ by valid legal entity markers (e.g., Parent vs. Subsidiary with different suffixes).
10. TYPO UNIFICATION & SPELLING VARIANTS (CRITICAL): Within each group, closely inspect for typos (e.g., "LIANSHHUO" vs "LIANSHUO") or variations involving generic words (e.g., one name has "Trade" or "Group" and the other doesn't). Unify ALL of these variations to ONE single authoritative spelling, UNLESS they have different legal suffixes (e.g., Inc vs LLC, DP vs LLC) which means they are distinct entities. To choose the correct spelling: prefer the version that appears most frequently in the group, or the one that most closely matches a plausible real-world registered company name. Every entry in the group that is a typo or subset variant MUST output that exact same Refined name. Never leave near-identical spellings as separate outputs within the same group.
11. Output ONLY lines in the format:  N|Refined   where N is the input number (e.g. 1|Best Care Solutions). One line per input name, no extra text, no group headers.
"""


def _try_one_batch(client: OpenAI, batch_groups: list, model: str, timeout: int) -> tuple:
    """
    Send one batch of groups to the API using the given model.
    Returns (raw_content_string, num_to_name dict).
    Raises on any error.
    """
    num_to_name = {}   # position number → original name
    input_lines = []
    counter = 1
    
    for idx, group in enumerate(batch_groups, 1):
        input_lines.append(f"Group {idx}:")
        for name in group:
            input_lines.append(f"{counter}. {name}")
            num_to_name[counter] = name
            counter += 1
        input_lines.append("")
        
    prompt = _PROMPT + "\n\nInput List:\n" + "\n".join(input_lines)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        timeout=timeout,
    )
    content = resp.choices[0].message.content
    return content, num_to_name


def refine_company_names(names: list, api_key: str,
                         model_name: str = "gemini-2.5-flash",
                         progress_callback=None) -> tuple:
    """
    Refine *names* via OpenAI custom proxy. Returns ({original: refined}, status_msg).

    Model fallback: tries *model_name* first, then walks FALLBACK_MODELS.
    If a model works for one batch it is reused for subsequent batches.
    On any unrecoverable error, every name maps to itself (safe no-op fallback).
    """
    if not api_key or not names:
        return {n: n for n in names}, "No API Key or no names provided"

    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://proxy.abhibots.com/v1",
        )
    except Exception as e:
        err = f"Client config error: {e}"
        print(f"[AI Refiner] {err}")
        return {n: n for n in names}, err

    # Build the fallback chain: preferred model first, then defaults (skip duplicates)
    chain = [model_name] + [m for m in FALLBACK_MODELS if m != model_name]

    unique    = list(dict.fromkeys(names))
    total_uni = len(unique)
    result    = {}
    BATCH     = 25
    TIMEOUT   = 60  # seconds per request
    status    = "OK"
    working_model: str | None = None   # once a model works, reuse it

    groups = group_similar_names(unique)
    
    # Build sub-batches of groups up to BATCH elements
    batches_of_groups = []
    current_batch = []
    current_count = 0
    for g in groups:
        if current_count + len(g) > BATCH and current_batch:
            batches_of_groups.append(current_batch)
            current_batch = [g]
            current_count = len(g)
        else:
            current_batch.append(g)
            current_count += len(g)
            
    if current_batch:
        batches_of_groups.append(current_batch)

    start_time = time.time()
    processed_count = 0

    for batch_groups in batches_of_groups:
        batch_size = sum(len(g) for g in batch_groups)
        
        if progress_callback:
            elapsed = time.time() - start_time
            time_per_item = (elapsed / processed_count) if processed_count > 0 else 0.0
            eta_seconds   = (total_uni - processed_count) * time_per_item if processed_count > 0 else 0.0
            progress_callback(processed_count, total_uni, eta_seconds)

        batch_ok = False

        # Try working_model first to avoid repeated fallback probing
        models_to_try = ([working_model] + [m for m in chain if m != working_model]
                         if working_model else chain)

        for model in models_to_try:
            try:
                print(f"[AI Refiner] Trying model: {model}  batch [{processed_count}:{processed_count+batch_size}]")
                content, num_to_name = _try_one_batch(client, batch_groups, model, TIMEOUT)

                # Parse N|Refined format — mapping by number, not by echoed text
                for line in content.strip().splitlines():
                    parts = line.split("|")
                    if len(parts) >= 2:
                        try:
                            num = int(parts[0].strip().rstrip('.'))
                            if num in num_to_name:
                                result[num_to_name[num]] = parts[1].strip()
                        except ValueError:
                            pass  # skip malformed lines

                working_model = model   # remember the model that worked
                batch_ok = True
                time.sleep(0.3)
                break   # batch succeeded — move to next batch

            except Exception as e:
                err_msg = str(e)
                print(f"[AI Refiner] Model {model} failed: {err_msg[:120]}")
                # Distinguish proxy-down vs rate-limit vs bad model
                if any(code in err_msg for code in ["500", "502", "503", "504"]) or "Bad Gateway" in err_msg:
                    # Proxy-level failure (e.g. NGINX 502 or backend 500) — no point trying other local models
                    status = (
                        f"Proxy Error: The AI proxy server is currently unavailable/offline ({err_msg[:30]}). "
                        "Please try again later or check your network."
                    )
                    for g in batch_groups:
                        for n in g:
                            result[n] = n
                    batch_ok = True   # mark as handled (fallback applied)
                    break
                elif "429" in err_msg:
                    status = f"Rate limited on {model}. Retrying after delay..."
                    time.sleep(5)
                    # continue to next model in chain
                else:
                    status = f"{model} error: {err_msg[:120]}"
                    # try next model in chain

        if not batch_ok:
            # Exhausted all models for this batch
            print(f"[AI Refiner] All models exhausted for batch [{processed_count}:{processed_count+batch_size}]")
            for g in batch_groups:
                for n in g:
                    result[n] = n
            status = "All AI models failed. Names returned unchanged."
            
        processed_count += batch_size

    if progress_callback:
        progress_callback(total_uni, total_uni, 0.0)

    for n in names:
        result.setdefault(n, n)

    return result, status

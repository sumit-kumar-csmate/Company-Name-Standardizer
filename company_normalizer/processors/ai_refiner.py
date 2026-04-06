"""
Gemini AI refiner — optional final-pass cleanup for flagged names.
Only processes Medium / Low confidence names.
Falls back gracefully if API is unavailable.

Fallback model chain: tries each model in FALLBACK_MODELS order until one works.
If ALL fail, every name maps to itself (safe no-op).
"""

import time
from openai import OpenAI

# ── Model fallback chain — tried in order until one succeeds ─────────────────
# Fastest/cheapest models first; more capable ones as fallbacks.
FALLBACK_MODELS = [
    "gemini-2.5-flash",
]

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
8. Do NOT change correct legal suffixes (Pvt Ltd, Limited, LLC, Inc, Corp, …).
9. If the name is already perfect, return it unchanged.
10. Output ONLY lines in the format:  Original|Refined   (one per input, no extra text).
"""


def _try_one_batch(client: OpenAI, batch: list, model: str, timeout: int) -> str:
    """
    Send one batch to the API using the given model.
    Returns the raw content string.
    Raises on any error.
    """
    prompt = _PROMPT + "\n\nInput List:\n" + "\n".join(batch)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        timeout=timeout,
    )
    return resp.choices[0].message.content


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
    BATCH     = 50
    TIMEOUT   = 30  # seconds per request
    status    = "OK"
    working_model: str | None = None   # once a model works, reuse it

    start_time = time.time()
    for start in range(0, total_uni, BATCH):
        if progress_callback:
            elapsed = time.time() - start_time
            time_per_item = (elapsed / start) if start > 0 else 0.0
            eta_seconds   = (total_uni - start) * time_per_item if start > 0 else 0.0
            progress_callback(start, total_uni, eta_seconds)

        batch = unique[start: start + BATCH]
        batch_ok = False

        # Try working_model first to avoid repeated fallback probing
        models_to_try = ([working_model] + [m for m in chain if m != working_model]
                         if working_model else chain)

        for model in models_to_try:
            try:
                print(f"[AI Refiner] Trying model: {model}  batch [{start}:{start+len(batch)}]")
                content = _try_one_batch(client, batch, model, TIMEOUT)

                for line in content.strip().splitlines():
                    parts = line.split("|")
                    if len(parts) >= 2:
                        result[parts[0].strip()] = parts[1].strip()

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
                    for n in batch:
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
            print(f"[AI Refiner] All models exhausted for batch [{start}:{start+len(batch)}]")
            for n in batch:
                result[n] = n
            status = "All AI models failed. Names returned unchanged."

    if progress_callback:
        progress_callback(total_uni, total_uni, 0.0)

    for n in names:
        result.setdefault(n, n)

    return result, status

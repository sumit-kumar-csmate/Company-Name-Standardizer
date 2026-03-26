"""
Gemini AI refiner — optional final-pass cleanup for flagged names.
Only processes Medium / Low confidence names.
Falls back gracefully if API is unavailable.
"""

import time
from openai import OpenAI

_PROMPT = """You are a data-cleaning expert for international trade data.
Fix spelling errors, remove stray artefacts, and expand specific geography abbreviation initials from company names.

Rules:
1. Fix spelling errors (e.g. "Limted" → "Limited", "Indsutries" → "Industries").
2. Remove trailing random chars/digits that are data artefacts.
3. INITIALLY EXPAND: If you see a solitary letter that obviously stands for a country or region (e.g. "I" standing for "India", "Intl" for "International"), expand it appropriately based on context. 
4. STRICT PORTMANTEAU PROTECTION: DO NOT attempt to expand ANY valid business portmanteaus, industry shorthand, abbreviations, or non-dictionary terms into full English words! If a word is not a standard English dictionary word but forms part of a company's unique identity (e.g., "Techno", "Exim", "Pharmbutor", "Polychem", "Chem", "Agri", or any similar shorthand), you MUST leave it EXACTLY as it is. Only correct undeniable, obvious typographical misspellings.
5. Do NOT change correct legal suffixes (Pvt Ltd, Limited, LLC, Inc, Corp, …).
6. Do NOT invent words not conceptually present in the original abbreviations.
7. If the name is already perfect, return it unchanged.
8. Output ONLY lines in the format:  Original|Refined   (one per input, no extra text).
"""

def refine_company_names(names: list, api_key: str,
                         model_name: str = "gemini-2.5-flash") -> tuple[dict, str]:
    """
    Refine *names* via OpenAI custom proxy. Returns ({original: refined}, status_msg).
    On any error, every name maps to itself (safe no-op fallback).
    """
    if not api_key or not names:
        return {n: n for n in names}, "No API Key or no names provided"

    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://proxy.abhibots.com/v1"
        )
    except Exception as e:
        err = f"Config error: {e}"
        print(f"[AI Refiner] {err}")
        return {n: n for n in names}, err

    unique    = list(dict.fromkeys(names))
    result    = {}
    BATCH     = 50  # safer batch size for OpenAI chat endpoint
    status    = "OK"

    for start in range(0, len(unique), BATCH):
        batch  = unique[start: start + BATCH]
        prompt = _PROMPT + "\n\nInput List:\n" + "\n".join(batch)
        
        try:
            resp = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            content = resp.choices[0].message.content
            
            for line in content.strip().splitlines():
                parts = line.split("|")
                if len(parts) >= 2:
                    result[parts[0].strip()] = parts[1].strip()
            time.sleep(0.5)
        except Exception as e:
            err = f"Batch error: {e}"
            print(f"[AI Refiner] {err}")
            for n in batch:
                result[n] = n
            status = err

    for n in names:
        result.setdefault(n, n)

    return result, status

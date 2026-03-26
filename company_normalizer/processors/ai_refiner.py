"""
Gemini AI refiner — optional final-pass cleanup for flagged names.
Only processes Medium / Low confidence names.
Falls back gracefully if API is unavailable.
"""

import time
from openai import OpenAI

_PROMPT = """You are a data-cleaning expert for international trade data.
Fix obvious spelling errors and remove stray artefact characters from company names.

Rules:
1. Fix spelling errors (e.g. "Limted" → "Limited", "Indsutries" → "Industries").
2. Remove trailing random chars/digits that look like data artefacts.
3. Do NOT change correct legal suffixes (Pvt Ltd, Limited, LLC, Inc, Corp, …).
4. Do NOT add or invent words not present in the original.
5. If the name is already correct, return it unchanged.
6. Output ONLY lines in the format:  Original|Refined   (one per input, nothing else).
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

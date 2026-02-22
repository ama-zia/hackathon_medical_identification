# gemini_client.py
import os
import json
import re
from google import genai

GEMINI_MODEL = "gemini-3-flash-preview"  # to have good response

_api_key = os.environ.get("GEMINI_API_KEY")
if not _api_key:
    raise RuntimeError("GEMINI_API_KEY not set in environment")

_client = genai.Client(api_key=_api_key)


def _extract_json_from_text(text: str):
    """
    
    1) try direct json.loads
    2) try to find first "{" and last "}" and parse substring
    3) fallback -> None
    """
    try:
        return json.loads(text)
    except Exception:
        # try to find substring that looks like JSON object
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            sub = text[start:end+1]
            try:
                return json.loads(sub)
            except Exception:
                pass
    return None


def generate_medication_summary(raw_text: str) -> dict:
    """
    Ask Gemini to return STRICT JSON for the 4 cards:
    - purpose (string)
    - side_effects (array of strings)
    - warnings (array of strings)   (when to seek help)
    - usage (string)               (how to take safely)
    - disclaimer (string)
    If parsing fails, return 'raw' field with full text for frontend fallback.
    """
    prompt = f"""
You are a medical-communication assistant. The user is an elderly patient and will paste a prescription text or a medicine name.
Produce a JSON object ONLY (no extra commentary, in easy to understand words) with exactly these fields:
- purpose: short sentence explaining what the medicine is for
- side_effects: an array of common side effects (each a short sentence)
- warnings: an array of things that should prompt immediate medical attention
- usage: a short clear explanation of how to take it safely (include common timing/food notes if present)
- disclaimer: a short sentence explicitly saying this is not medical advice and to consult a doctor or pharmacist.

Input: \"\"\"{raw_text}\"\"\"

Return valid JSON only.
"""
    resp = _client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )

    # gemini response object may have .text or be string-like
    text = getattr(resp, "text", None) or str(resp)
    parsed = _extract_json_from_text(text)

    if parsed:
        # ensure minimal keys exist
        for k in ("purpose", "side_effects", "warnings", "usage", "disclaimer"):
            if k not in parsed:
                parsed[k] = "" if k in ("purpose", "usage", "disclaimer") else []
        return parsed
    # fallback
    return {
        "purpose": "",
        "side_effects": [],
        "warnings": [],
        "usage": "",
        "disclaimer": "This is not medical advice. Consult a clinician.",
        "raw": text
    }
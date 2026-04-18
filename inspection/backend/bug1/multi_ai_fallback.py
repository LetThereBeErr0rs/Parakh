import os
from dotenv import load_dotenv

load_dotenv()

API_KEYS = [
    os.getenv("GEMINI_API_KEY_1"),
    os.getenv("GEMINI_API_KEY_2"),
    os.getenv("GEMINI_API_KEY_3"),
    os.getenv("GEMINI_API_KEY_4"),
]

# MODELS (all free-tier supported)
MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-8b",
    "gemini-2.0-pro",
    "gemini-2.5-pro"
]


def _generate_with_new_sdk(api_key: str, model_name: str, prompt: str):
    from google import genai

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )
    return getattr(response, "text", None)


def _generate_with_legacy_sdk(api_key: str, model_name: str, prompt: str):
    import google.generativeai as legacy_genai

    legacy_genai.configure(api_key=api_key)
    model = legacy_genai.GenerativeModel(model_name)
    response = model.generate_content(prompt)
    return getattr(response, "text", None)


def generate_prompt(text):
    return f"""
You are a strict fact-checking AI.

Verify this claim:

{text}

Return STRICT JSON:
{{
  "status": "Supported / Refuted / Uncertain",
  "confidence": number (0-100),
  "summary": "short explanation"
}}
"""


def multi_model_verify(text):
    prompt = generate_prompt(text)
    valid_keys = [key for key in API_KEYS if key]

    if not valid_keys:
        return """
{
  "status": "Uncertain",
  "confidence": 50,
  "summary": "No valid Gemini API key is configured. Set GEMINI_API_KEY_n in environment variables.",
  "evidence": []
}
"""

    # Try all keys + models
    for key in valid_keys:
        for model_name in MODELS:
            try:
                try:
                    text_response = _generate_with_new_sdk(key, model_name, prompt)
                except Exception:
                    text_response = _generate_with_legacy_sdk(key, model_name, prompt)

                if text_response:
                    print(f"[INFO] Used {model_name} with key")
                    return text_response
            except Exception as model_error:
                print(f"[WARN] Model failed: {model_name}", model_error)
                continue

    # FINAL FALLBACK
    return """
{
  "status": "Uncertain",
  "confidence": 50,
  "summary": "No external Gemini model produced a usable response.",
  "evidence": []
}
"""
import os
from dotenv import load_dotenv

load_dotenv()

_model = None

def _get_model():
    global _model
    if _model is None:
        import google.generativeai as genai
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "your_gemini_key_here":
            return None
        genai.configure(api_key=api_key)
        _model = genai.GenerativeModel("gemini-1.5-flash")
    return _model

def ask_gemini(prompt: str) -> str | None:
    """Returns Gemini response, or None if key not configured / API fails."""
    try:
        model = _get_model()
        if model is None:
            return None
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"[Gemini] API error: {e}")
        return None

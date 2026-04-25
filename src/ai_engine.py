import os
from dotenv import load_dotenv

load_dotenv()

_client = None

def _get_client():
    global _client
    if _client is None:
        from google import genai
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "your_gemini_key_here":
            return None
        _client = genai.Client(api_key=api_key)
    return _client

def ask_gemini(prompt: str) -> str | None:
    """Returns Gemini response, or None if key not configured / API fails."""
    try:
        client = _get_client()
        if client is None:
            return None
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        print(f"[Gemini] API error: {e}")
        return None

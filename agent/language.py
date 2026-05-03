"""
Safar AI — Language Detection
Detects whether user input is Urdu or English.
"""

from langdetect import detect, LangDetectException


def detect_language(text):
    """
    Detect language of input text.
    Returns 'ur' for Urdu, 'en' for English, or detected ISO code.
    """
    if not text or len(text.strip()) < 3:
        return "en"
    
    try:
        lang = detect(text)
        # langdetect returns 'ur' for Urdu, 'en' for English
        return lang
    except LangDetectException:
        return "en"


def is_urdu(text):
    """Check if text is in Urdu."""
    return detect_language(text) == "ur"


def get_response_language_instruction(text):
    """Get instruction for LLM to respond in the detected language."""
    lang = detect_language(text)
    if lang == "ur":
        return "Respond in Urdu (Roman Urdu transliteration is fine). Be helpful and friendly."
    return "Respond in English. Be helpful and friendly."

"""
Safar AI — Groq Chat Completion Wrapper
Handles all Groq API calls with error handling and retry logic.
"""

import os
import streamlit as st
from groq import Groq


def _get_client():
    """Get Groq client with API key from secrets or env."""
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        api_key = os.getenv("GROQ_API_KEY", "")
    
    if not api_key:
        return None
    return Groq(api_key=api_key)


def chat_with_groq(messages, model="llama-3.3-70b-versatile", temperature=0.7, max_tokens=2048):
    """
    Send chat completion request to Groq API.
    
    Args:
        messages: list of message dicts with role and content
        model: Groq model name
        temperature: creativity level
        max_tokens: max response length
    
    Returns:
        str response content or error message
    """
    client = _get_client()
    if not client:
        return "⚠️ Groq API key not configured. Please add GROQ_API_KEY to your secrets."
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        error_msg = str(e)
        if "rate_limit" in error_msg.lower() or "429" in error_msg:
            return "⚠️ Rate limit reached. Please wait a moment and try again."
        elif "401" in error_msg or "auth" in error_msg.lower():
            return "⚠️ Invalid Groq API key. Please check your configuration."
        else:
            return f"⚠️ Groq API error: {error_msg}"

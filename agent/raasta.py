"""
Safar AI — Raasta Chatbot
AI travel assistant powered by Groq, with route context awareness.
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from groq_ai.chat import chat_with_groq
from agent.language import get_response_language_instruction
from agent.intent import classify_intent, get_intent_context


RAASTA_SYSTEM_PROMPT = """You are "Raasta" (راستہ) — Safar AI's intelligent travel assistant for Pakistan.

Your personality:
- Friendly, knowledgeable, and professional
- Expert on Pakistan roads, routes, cities, and travel conditions
- You can respond in English or Roman Urdu based on the user's language
- You use relevant emojis to make responses engaging

Your capabilities:
- Answer questions about route safety, travel times, costs, weather
- Provide Pakistan-specific travel advice
- Reference the current trip context when available
- Give fuel-saving tips, best travel times, and safety advisories

Rules:
- Keep responses concise (3-5 sentences max unless detail is requested)
- Always use PKR for costs
- Be honest about limitations — if you don't know, say so
- Never make up safety information"""


def raasta_chat(user_message, route_context=None, chat_history=None):
    """
    Process a user message through the Raasta chatbot.
    
    Args:
        user_message: user's chat input
        route_context: optional dict with current trip/route data
        chat_history: list of previous messages for continuity
    
    Returns:
        str: Raasta's response
    """
    # Detect language and intent
    lang_instruction = get_response_language_instruction(user_message)
    intent, confidence = classify_intent(user_message)
    intent_context = get_intent_context(intent)
    
    # Build system prompt with context
    system_content = RAASTA_SYSTEM_PROMPT + f"\n\n{lang_instruction}\n\nFocus area: {intent_context}"
    
    # Add route context if available
    if route_context:
        context_str = _format_route_context(route_context)
        system_content += f"\n\nCurrent Trip Context:\n{context_str}"
    
    # Build messages
    messages = [{"role": "system", "content": system_content}]
    
    # Add chat history (last 6 messages to stay within limits)
    if chat_history:
        for msg in chat_history[-6:]:
            messages.append(msg)
    
    messages.append({"role": "user", "content": user_message})
    
    response = chat_with_groq(messages, temperature=0.7, max_tokens=500)
    return response


def _format_route_context(ctx):
    """Format route context for the system prompt."""
    if not ctx:
        return "No trip data available."
    
    parts = []
    if "origin" in ctx:
        parts.append(f"Origin: {ctx['origin']}")
    if "destination" in ctx:
        parts.append(f"Destination: {ctx['destination']}")
    if "best_route" in ctx:
        r = ctx["best_route"]
        parts.append(f"Recommended Route: {r.get('summary', 'N/A')}")
        parts.append(f"Distance: {r.get('distance_km', 'N/A')} km")
        if "eta" in r:
            parts.append(f"ETA: {r['eta'].get('eta_min', 'N/A')} min")
        if "safety" in r:
            parts.append(f"Safety Score: {r['safety'].get('score', 'N/A')}/100")
        if "cost" in r:
            parts.append(f"Cost: PKR {r['cost'].get('total_cost_pkr', 'N/A')}")
    
    return "\n".join(parts)

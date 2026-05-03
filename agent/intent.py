"""
Safar AI — Intent Classification
Classifies user chat queries into intent categories.
"""


INTENT_KEYWORDS = {
    "safety": ["safe", "danger", "risk", "night", "secure", "security", "crime", "mehfooz", "khatrnak"],
    "time": ["best time", "when", "time to travel", "kab", "waqt", "peak", "rush hour"],
    "cost": ["cost", "fuel", "petrol", "diesel", "toll", "kitna kharch", "paisa", "budget", "save money"],
    "weather": ["weather", "rain", "monsoon", "fog", "barish", "mausam", "dhund"],
    "route": ["route", "road", "path", "motorway", "highway", "rasta", "raasta", "alternative"],
    "food": ["food", "restaurant", "hotel", "rest area", "dhaba", "khana", "rest stop"],
    "general": []
}


def classify_intent(text):
    """
    Classify user query into an intent category.
    Returns (intent_name, confidence).
    """
    text_lower = text.lower().strip()
    
    scores = {}
    for intent, keywords in INTENT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[intent] = score
    
    if not scores:
        return "general", 0.5
    
    best_intent = max(scores, key=scores.get)
    confidence = min(1.0, scores[best_intent] / 3)
    
    return best_intent, round(confidence, 2)


def get_intent_context(intent):
    """Get additional context prompt for a given intent."""
    context_map = {
        "safety": "Focus on safety information, night travel risks, and security advisories for Pakistan roads.",
        "time": "Focus on best travel times, rush hour patterns, and Pakistan-specific timing (Friday prayers, etc).",
        "cost": "Focus on fuel costs in PKR, toll charges, and money-saving tips for Pakistan travel.",
        "weather": "Focus on weather conditions, monsoon risks, fog seasons, and seasonal travel advice.",
        "route": "Focus on route options, road conditions, motorway vs highway pros/cons.",
        "food": "Focus on rest areas, food stops, dhabas, and amenities along the route.",
        "general": "Provide helpful travel information about Pakistan routes."
    }
    return context_map.get(intent, context_map["general"])

"""
Safar AI — Smart Travel Report Generator
Sends scored route data to Groq LLM for deep analysis.
"""

import json
from groq_ai.chat import chat_with_groq


REPORT_SYSTEM_PROMPT = """You are Safar AI — Pakistan's premier AI travel intelligence system. 
You analyze route data and produce professional Smart Travel Reports.

Your report MUST include these sections with the exact headers:
## 🏆 Recommended Route
## 📊 Route Analysis  
## ⚠️ Risk Assessment
## 🔄 Alternative Routes
## 💡 Personalized Travel Tips
## 💰 Cost Breakdown

Guidelines:
- Be specific with numbers, distances, and times
- Mention Pakistan-specific factors (monsoon, fog, Friday prayers, security checkpoints)
- Give actionable advice
- Use PKR for all costs
- Keep the tone professional but friendly
- Write in English
- Use bullet points for readability"""


def generate_travel_report(scored_routes, trip_info):
    """
    Generate a Smart Travel Report using Groq LLM.
    
    Args:
        scored_routes: list of scored route dicts from scoring engine
        trip_info: dict with origin, destination, mode, departure, vehicle
    
    Returns:
        str: formatted travel report markdown
    """
    # Build condensed route data for the prompt
    routes_summary = []
    for r in scored_routes:
        routes_summary.append({
            "route_id": r["route_id"],
            "summary": r["summary"],
            "distance_km": r["distance_km"],
            "eta_min": r["eta"]["eta_min"],
            "arrival_time": r["eta"]["arrival_time"],
            "score": r["final_score"],
            "safety_score": r["safety"]["score"],
            "safety_rating": r["safety"]["rating"],
            "congestion_prob": r["ml_congestion"],
            "fuel_cost_pkr": r["cost"]["fuel_cost_pkr"],
            "toll_cost_pkr": r["cost"]["toll_cost_pkr"],
            "total_cost_pkr": r["cost"]["total_cost_pkr"],
            "blockages_nearby": r["blockage_info"]["blockage_count"],
            "is_recommended": r["is_recommended"],
            "rank": r["rank"]
        })
    
    payload = {
        "trip_info": trip_info,
        "scored_routes": routes_summary
    }
    
    user_prompt = f"""Analyze the following route data and generate a comprehensive Smart Travel Report.

ROUTE DATA (JSON):
```json
{json.dumps(payload, indent=2)}
```

Generate the full report with all required sections."""
    
    messages = [
        {"role": "system", "content": REPORT_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]
    
    report = chat_with_groq(messages, temperature=0.6, max_tokens=3000)
    return report


def generate_quick_summary(scored_routes, trip_info):
    """Generate a one-paragraph quick summary for the dashboard header."""
    best = scored_routes[0] if scored_routes else None
    if not best:
        return "No routes available."
    
    prompt = f"""In exactly 2 sentences, summarize this trip:
From {trip_info['origin']} to {trip_info['destination']} via {best['summary']}.
Distance: {best['distance_km']}km, ETA: {best['eta']['eta_min']}min, 
Safety: {best['safety']['score']}/100, Cost: PKR {best['cost']['total_cost_pkr']:,}.
Be concise and mention the key highlight and one tip."""
    
    messages = [
        {"role": "system", "content": "You are Safar AI. Give ultra-brief trip summaries."},
        {"role": "user", "content": prompt}
    ]
    
    return chat_with_groq(messages, temperature=0.5, max_tokens=200)

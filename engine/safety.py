"""
Safar AI — Safety Score Calculator
Computes route safety rating from region data, time of day, and road type.
"""

from datetime import datetime
from utils.helpers import get_safety_index, get_time_period


def calculate_safety_score(
    origin_province: str,
    destination_province: str,
    departure_hour: int,
    distance_km: float,
    route_summary: str = ""
) -> dict:
    """
    Calculate safety score (0-100) for a route.
    
    Args:
        origin_province: province/territory of origin
        destination_province: province/territory of destination
        departure_hour: hour of departure (0-23)
        distance_km: route distance
        route_summary: route description for road type detection
    
    Returns:
        dict with score, rating_label, factors breakdown
    """
    safety_data = get_safety_index()
    regions = safety_data.get("regions", {})
    road_modifiers = safety_data.get("road_type_modifiers", {})
    time_modifiers = safety_data.get("time_modifiers", {})
    
    # Get base scores for origin and destination regions
    origin_info = regions.get(origin_province, regions.get("Punjab", {"base_score": 70}))
    dest_info = regions.get(destination_province, regions.get("Punjab", {"base_score": 70}))
    
    # Average the two region scores
    base_score = (origin_info["base_score"] + dest_info["base_score"]) / 2
    
    # Detect road type from route summary
    road_type = _detect_road_type(route_summary, distance_km)
    road_modifier = road_modifiers.get(road_type, 0)
    
    # Get time-of-day modifier
    time_modifier = 0
    time_period = get_time_period(departure_hour)
    for period_key, period_data in time_modifiers.items():
        if departure_hour in period_data.get("hours", []):
            time_modifier = period_data["modifier"]
            break
    
    # Night penalty from region data
    night_penalty = 0
    if departure_hour >= 20 or departure_hour <= 5:
        night_penalty = (origin_info.get("night_penalty", -15) + dest_info.get("night_penalty", -15)) / 2
    
    # Long distance fatigue penalty
    fatigue_penalty = 0
    if distance_km > 500:
        fatigue_penalty = -10
    elif distance_km > 300:
        fatigue_penalty = -5
    
    # Calculate final score
    final_score = base_score + road_modifier + time_modifier + night_penalty + fatigue_penalty
    final_score = max(0, min(100, final_score))
    
    # Rating label
    if final_score >= 80:
        rating = "🟢 Safe"
    elif final_score >= 60:
        rating = "🟡 Moderate"
    elif final_score >= 40:
        rating = "🟠 Caution"
    else:
        rating = "🔴 Risky"
    
    return {
        "score": round(final_score),
        "rating": rating,
        "base_score": base_score,
        "road_type": road_type,
        "road_modifier": road_modifier,
        "time_modifier": time_modifier,
        "night_penalty": night_penalty,
        "fatigue_penalty": fatigue_penalty,
        "time_period": time_period,
        "factors": {
            "Region Safety": f"{base_score}/100",
            "Road Type": f"{road_type.title()} ({'+' if road_modifier >= 0 else ''}{road_modifier})",
            "Time of Day": f"{time_period.replace('_', ' ').title()} ({'+' if time_modifier >= 0 else ''}{time_modifier})",
            "Night Travel": f"{night_penalty}" if night_penalty else "N/A",
            "Long Distance": f"{fatigue_penalty}" if fatigue_penalty else "N/A"
        }
    }


def _detect_road_type(route_summary: str, distance_km: float) -> str:
    """Detect road type from route summary text."""
    summary_lower = route_summary.lower()
    
    if any(kw in summary_lower for kw in ["motorway", "m-1", "m-2", "m-3", "m-4", "m-9", "m-11", "m-14"]):
        return "motorway"
    elif any(kw in summary_lower for kw in ["highway", "national", "n-5", "n-55", "gt road"]):
        return "highway"
    elif any(kw in summary_lower for kw in ["karakoram", "mountain", "pass", "babusar", "lowari", "khunjerab"]):
        return "mountain"
    elif distance_km > 200:
        return "highway"
    elif distance_km > 50:
        return "urban"
    else:
        return "urban"


def get_province_for_city(city_name: str) -> str:
    """Get province for a city from the local database."""
    from utils.helpers import get_cities_data
    cities = get_cities_data()
    
    for name, info in cities.items():
        if name.lower() == city_name.lower():
            return info.get("province", "Punjab")
    
    return "Punjab"  # Default fallback

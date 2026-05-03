"""
Safar AI — ETA Calculator
Adjusts raw route duration based on time-of-day congestion patterns.
"""

from datetime import datetime
from utils.helpers import is_rush_hour, get_time_period


def calculate_eta(
    base_duration_min: float,
    departure_time: datetime,
    distance_km: float,
    zone: str = "urban"
) -> dict:
    """
    Calculate adjusted ETA based on departure time and congestion patterns.
    
    Args:
        base_duration_min: raw duration from ORS in minutes
        departure_time: planned departure datetime
        distance_km: route distance
        zone: urban / semi_urban / rural
    
    Returns:
        dict with eta_min, arrival_time, congestion_factor, delay_min
    """
    hour = departure_time.hour
    day = departure_time.weekday()
    
    # Base congestion multiplier
    congestion_factor = 1.0
    
    # Rush hour adjustments
    if is_rush_hour(hour):
        if zone == "urban":
            congestion_factor = 1.35  # 35% longer in urban rush
        elif zone == "semi_urban":
            congestion_factor = 1.20
        else:
            congestion_factor = 1.05
    
    # Friday prayer time (12:30 PM - 2:00 PM)
    if day == 4 and 12 <= hour <= 14:
        congestion_factor *= 1.15
    
    # Late night — slightly faster (less traffic)
    if hour >= 22 or hour <= 4:
        congestion_factor *= 0.85
    
    # Weekend bonus (less commuter traffic, except Sunday bazaars)
    if day in [5, 6] and not is_rush_hour(hour):
        congestion_factor *= 0.92
    
    # Calculate adjusted duration
    adjusted_min = base_duration_min * congestion_factor
    delay_min = adjusted_min - base_duration_min
    
    # Calculate arrival time
    from datetime import timedelta
    arrival_time = departure_time + timedelta(minutes=adjusted_min)
    
    return {
        "eta_min": round(adjusted_min, 1),
        "arrival_time": arrival_time.strftime("%I:%M %p"),
        "arrival_datetime": arrival_time,
        "congestion_factor": round(congestion_factor, 2),
        "delay_min": round(max(0, delay_min), 1),
        "time_period": get_time_period(hour),
        "base_duration_min": base_duration_min
    }

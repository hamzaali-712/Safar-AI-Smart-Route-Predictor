"""
Safar AI — Shared Utility Functions
Geocoding, validation, formatting, and data loading helpers.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from fuzzywuzzy import process

# ──────────────────────────────────────────────────────────────
# PATH HELPERS
# ──────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def load_json(filename: str) -> dict:
    """Load a JSON file from the data/ directory."""
    filepath = DATA_DIR / filename
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def get_cities_data() -> dict:
    """Load Pakistan cities with coordinates."""
    data = load_json("pakistan_cities.json")
    return data.get("cities", {})


def get_fuel_prices() -> dict:
    """Load fuel price data."""
    return load_json("fuel_prices.json")


def get_vehicle_config() -> dict:
    """Load vehicle configuration data."""
    data = load_json("vehicle_config.json")
    return data.get("vehicles", {})


def get_safety_index() -> dict:
    """Load safety index data."""
    return load_json("safety_index.json")


def get_blockages() -> list:
    """Load known blockage data."""
    data = load_json("blockages.json")
    return data.get("known_blockages", [])


def get_rest_areas() -> list:
    """Load rest area data."""
    data = load_json("rest_areas.json")
    return data.get("rest_areas", [])


# ──────────────────────────────────────────────────────────────
# GEOCODING
# ──────────────────────────────────────────────────────────────

def geocode_location(place_name: str) -> tuple:
    """
    Convert a place name to (lat, lng) coordinates.
    First tries local city data, then falls back to Nominatim.
    Returns (lat, lng) or (None, None) on failure.
    """
    # Try local city database first
    cities = get_cities_data()
    
    # Fuzzy match against city names
    city_names = list(cities.keys())
    match, score = process.extractOne(place_name, city_names)
    
    if score >= 75:
        city = cities[match]
        return city["lat"], city["lng"]
    
    # Fallback to Nominatim geocoding
    try:
        geolocator = Nominatim(user_agent="safar-ai-route-predictor")
        location = geolocator.geocode(place_name + ", Pakistan", timeout=10)
        if location:
            return location.latitude, location.longitude
    except GeocoderTimedOut:
        pass
    except Exception:
        pass
    
    return None, None


def fuzzy_match_city(query: str) -> str:
    """Find the best matching city name from the database."""
    cities = get_cities_data()
    city_names = list(cities.keys())
    match, score = process.extractOne(query, city_names)
    return match if score >= 60 else query


# ──────────────────────────────────────────────────────────────
# FORMATTING
# ──────────────────────────────────────────────────────────────

def format_duration(minutes: float) -> str:
    """Convert minutes to human-readable duration string."""
    if minutes < 60:
        return f"{int(minutes)} min"
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    if mins == 0:
        return f"{hours}h"
    return f"{hours}h {mins}m"


def format_distance(km: float) -> str:
    """Format distance in km with one decimal place."""
    if km < 1:
        return f"{int(km * 1000)} m"
    return f"{km:.1f} km"


def format_cost(amount: float) -> str:
    """Format cost in PKR with comma separators."""
    return f"PKR {amount:,.0f}"


def get_time_period(hour: int) -> str:
    """Get the time period label for a given hour."""
    if 5 <= hour <= 6:
        return "early_morning"
    elif 7 <= hour <= 9:
        return "morning"
    elif 10 <= hour <= 15:
        return "daytime"
    elif 16 <= hour <= 19:
        return "evening"
    else:
        return "night"


def is_rush_hour(hour: int) -> bool:
    """Check if the hour is during rush hour."""
    return hour in [7, 8, 9, 17, 18, 19]


def is_weekend(day_of_week: int) -> bool:
    """Check if it's a weekend (Friday=4 or Saturday=5 in Pakistan context; Sunday=6)."""
    return day_of_week in [4, 5, 6]  # Fri, Sat, Sun


def get_weather_risk(month: int) -> float:
    """
    Get seasonal weather risk factor (0.0 - 1.0).
    Higher during monsoon months (Jul-Sep) and winter fog (Dec-Jan).
    """
    weather_risks = {
        1: 0.5,   # January — fog
        2: 0.3,   # February — mild
        3: 0.2,   # March — clear
        4: 0.2,   # April — clear
        5: 0.3,   # May — heat
        6: 0.4,   # June — pre-monsoon
        7: 0.8,   # July — monsoon peak
        8: 0.85,  # August — monsoon peak
        9: 0.6,   # September — monsoon tail
        10: 0.2,  # October — clear
        11: 0.3,  # November — smog
        12: 0.55  # December — fog
    }
    return weather_risks.get(month, 0.3)


# ──────────────────────────────────────────────────────────────
# TRAVEL MODE MAPPING
# ──────────────────────────────────────────────────────────────

ORS_PROFILES = {
    "Driving (Car)": "driving-car",
    "Driving (HGV/Truck)": "driving-hgv",
    "Cycling": "cycling-regular",
    "Walking": "foot-walking",
}

def get_ors_profile(mode_label: str) -> str:
    """Map user-friendly label to ORS profile string."""
    return ORS_PROFILES.get(mode_label, "driving-car")


def get_travel_modes() -> list:
    """Return list of available travel mode labels."""
    return list(ORS_PROFILES.keys())

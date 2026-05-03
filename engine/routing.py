"""
Safar AI — ORS Route Fetching Engine
Fetches multiple route alternatives from OpenRouteService API.
"""

import os
import requests
import streamlit as st


ORS_BASE_URL = "https://api.openrouteservice.org/v2/directions"


def _get_api_key() -> str:
    """Get ORS API key from Streamlit secrets or environment."""
    try:
        return st.secrets["ORS_API_KEY"]
    except Exception:
        return os.getenv("ORS_API_KEY", "")


def fetch_routes(
    origin_coords: tuple,
    destination_coords: tuple,
    profile: str = "driving-car",
    alternatives: int = 3
) -> list:
    """
    Fetch multiple route alternatives from OpenRouteService.
    
    Args:
        origin_coords: (lat, lng) of origin
        destination_coords: (lat, lng) of destination
        profile: ORS routing profile (driving-car, foot-walking, etc.)
        alternatives: number of alternative routes to request
    
    Returns:
        List of route dicts with distance_km, duration_min, geometry, steps, summary, bbox
    """
    api_key = _get_api_key()
    if not api_key:
        st.error("⚠️ OpenRouteService API key not configured. Add ORS_API_KEY to your .env or Streamlit secrets.")
        return []

    # ORS expects [lng, lat] format
    origin_lng_lat = [origin_coords[1], origin_coords[0]]
    dest_lng_lat = [destination_coords[1], destination_coords[0]]

    url = f"{ORS_BASE_URL}/{profile}/json"
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json; charset=utf-8"
    }
    body = {
        "coordinates": [origin_lng_lat, dest_lng_lat],
        "alternative_routes": {
            "share_factor": 0.6,
            "target_count": alternatives,
            "weight_factor": 1.6
        },
        "geometry": True,
        "instructions": True,
        "units": "km"
    }

    try:
        response = requests.post(url, json=body, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            st.warning("⚠️ Route not found. The locations may not be routable with this travel mode.")
        elif response.status_code == 401:
            st.error("⚠️ Invalid ORS API key. Please check your configuration.")
        else:
            st.error(f"⚠️ ORS API error: {e}")
        return []
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Could not connect to OpenRouteService. Check your internet connection.")
        return []
    except requests.exceptions.Timeout:
        st.error("⚠️ ORS API request timed out. Please try again.")
        return []
    except Exception as e:
        st.error(f"⚠️ Unexpected error fetching routes: {e}")
        return []

    routes = []
    for idx, route in enumerate(data.get("routes", [])):
        summary = route.get("summary", {})
        segments = route.get("segments", [{}])
        
        # Extract step-by-step instructions
        steps = []
        for segment in segments:
            for step in segment.get("steps", []):
                steps.append({
                    "instruction": step.get("instruction", ""),
                    "distance_km": round(step.get("distance", 0) / 1000, 2),
                    "duration_min": round(step.get("duration", 0) / 60, 1),
                    "type": step.get("type", 0),
                    "name": step.get("name", "")
                })

        # Decode geometry (ORS returns encoded polyline)
        geometry = _decode_geometry(route.get("geometry", ""))

        # Build route label
        road_names = [s.get("name", "") for s in steps if s.get("name")]
        unique_roads = list(dict.fromkeys(road_names))[:3]
        route_label = " → ".join(unique_roads) if unique_roads else f"Route {idx + 1}"

        routes.append({
            "route_id": idx + 1,
            "summary": route_label,
            "distance_km": round(summary.get("distance", 0) / 1000, 1),
            "duration_min": round(summary.get("duration", 0) / 60, 1),
            "geometry": geometry,
            "steps": steps,
            "bbox": route.get("bbox", []),
            "ascent": summary.get("ascent", 0),
            "descent": summary.get("descent", 0)
        })

    return routes


def _decode_geometry(encoded: str) -> list:
    """
    Decode ORS encoded polyline geometry to list of [lat, lng] pairs.
    Uses the standard Google Polyline encoding algorithm.
    """
    if not encoded:
        return []
    
    decoded = []
    index = 0
    lat = 0
    lng = 0

    while index < len(encoded):
        # Decode latitude
        shift = 0
        result = 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        dlat = ~(result >> 1) if (result & 1) else (result >> 1)
        lat += dlat

        # Decode longitude
        shift = 0
        result = 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1F) << shift
            shift += 5
            if b < 0x20:
                break
        dlng = ~(result >> 1) if (result & 1) else (result >> 1)
        lng += dlng

        decoded.append([lat / 1e5, lng / 1e5])

    return decoded

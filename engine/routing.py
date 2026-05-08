"""
Safar AI — ORS Route Fetching Engine
Fetches multiple route alternatives from OpenRouteService API.
Includes automatic fallback to OSRM when ORS fails.
"""

import os
import requests
import streamlit as st


ORS_BASE_URL = "https://api.openrouteservice.org/v2/directions"
OSRM_BASE_URL = "https://router.project-osrm.org/route/v1"


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
    Fetch multiple route alternatives. Tries ORS first, falls back to OSRM.

    Args:
        origin_coords: (lat, lng) of origin
        destination_coords: (lat, lng) of destination
        profile: ORS routing profile (driving-car, foot-walking, etc.)
        alternatives: number of alternative routes to request

    Returns:
        List of route dicts with distance_km, duration_min, geometry, steps, summary, bbox
    """
    # Validate coordinates
    if not _validate_coords(origin_coords) or not _validate_coords(destination_coords):
        st.error("⚠️ Invalid coordinates. Please select valid cities.")
        return []

    api_key = _get_api_key()

    # Strategy 1: Try ORS with alternatives
    if api_key:
        routes = _fetch_ors_routes(origin_coords, destination_coords, profile, api_key, alternatives)
        if routes:
            return routes

        # Strategy 2: Try ORS WITHOUT alternatives (simpler request)
        routes = _fetch_ors_routes(origin_coords, destination_coords, profile, api_key, 0)
        if routes:
            return routes

    # Strategy 3: Fallback to OSRM (free, no API key needed)
    st.info("🔄 Using free OSRM routing as fallback...")
    routes = _fetch_osrm_routes(origin_coords, destination_coords, profile, alternatives)
    if routes:
        return routes

    return []


def _validate_coords(coords: tuple) -> bool:
    """Validate that coordinates are reasonable lat/lng values."""
    if not coords or len(coords) < 2:
        return False
    lat, lng = coords
    return -90 <= lat <= 90 and -180 <= lng <= 180


def _fetch_ors_routes(origin_coords, destination_coords, profile, api_key, alternatives):
    """Fetch routes from OpenRouteService API."""
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
        "geometry": True,
        "instructions": True
    }

    # Only add alternative_routes if requesting > 0 alternatives
    if alternatives > 0:
        body["alternative_routes"] = {
            "share_factor": 0.6,
            "target_count": alternatives,
            "weight_factor": 1.6
        }

    try:
        response = requests.post(url, json=body, headers=headers, timeout=20)

        # Parse error details from response body before raising
        if response.status_code != 200:
            error_detail = ""
            try:
                err_json = response.json()
                error_detail = err_json.get("error", {})
                if isinstance(error_detail, dict):
                    error_detail = error_detail.get("message", str(err_json))
                else:
                    error_detail = str(error_detail)
            except Exception:
                error_detail = response.text[:200]

            if response.status_code == 400:
                st.warning(f"⚠️ ORS rejected request: {error_detail}")
                return []
            elif response.status_code == 401 or response.status_code == 403:
                st.error("⚠️ Invalid or expired ORS API key. Please check your configuration.")
                return []
            elif response.status_code == 404:
                st.warning("⚠️ Route not found. The locations may not be routable with this travel mode.")
                return []
            elif response.status_code == 429:
                st.warning("⚠️ ORS rate limit exceeded. Falling back to alternative routing...")
                return []
            else:
                st.error(f"⚠️ ORS API error ({response.status_code}): {error_detail}")
                return []

        data = response.json()

    except requests.exceptions.ConnectionError:
        st.warning("⚠️ Could not connect to OpenRouteService. Trying fallback...")
        return []
    except requests.exceptions.Timeout:
        st.warning("⚠️ ORS API request timed out. Trying fallback...")
        return []
    except Exception as e:
        st.warning(f"⚠️ ORS error: {e}")
        return []

    return _parse_ors_response(data)


def _parse_ors_response(data: dict) -> list:
    """Parse ORS API response into standardized route list."""
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
            "descent": summary.get("descent", 0),
            "source": "ORS"
        })

    return routes


# ──────────────────────────────────────────────────────────────
# OSRM FALLBACK (Free, no API key required)
# ──────────────────────────────────────────────────────────────

def _get_osrm_profile(ors_profile: str) -> str:
    """Map ORS profile to OSRM profile."""
    mapping = {
        "driving-car": "driving",
        "driving-hgv": "driving",
        "cycling-regular": "cycling",
        "cycling-road": "cycling",
        "cycling-mountain": "cycling",
        "foot-walking": "foot",
        "foot-hiking": "foot",
    }
    return mapping.get(ors_profile, "driving")


def _fetch_osrm_routes(origin_coords, destination_coords, ors_profile, alternatives):
    """Fetch routes from free OSRM API as fallback."""
    osrm_profile = _get_osrm_profile(ors_profile)

    # OSRM uses lng,lat format in URL
    coords_str = f"{origin_coords[1]},{origin_coords[0]};{destination_coords[1]},{destination_coords[0]}"

    url = f"{OSRM_BASE_URL}/{osrm_profile}/{coords_str}"
    params = {
        "overview": "full",
        "geometries": "polyline",
        "steps": "true",
        "alternatives": "true" if alternatives > 0 else "false"
    }

    try:
        response = requests.get(url, params=params, timeout=20)

        if response.status_code != 200:
            st.error(f"⚠️ OSRM routing failed (HTTP {response.status_code})")
            return []

        data = response.json()

        if data.get("code") != "Ok":
            st.error(f"⚠️ OSRM error: {data.get('message', 'Unknown error')}")
            return []

    except requests.exceptions.ConnectionError:
        st.error("⚠️ Could not connect to routing service. Check your internet connection.")
        return []
    except requests.exceptions.Timeout:
        st.error("⚠️ Routing request timed out. Please try again.")
        return []
    except Exception as e:
        st.error(f"⚠️ Routing error: {e}")
        return []

    return _parse_osrm_response(data)


def _parse_osrm_response(data: dict) -> list:
    """Parse OSRM API response into standardized route list."""
    routes = []
    for idx, route in enumerate(data.get("routes", [])):
        # Decode OSRM polyline geometry
        geometry = _decode_geometry(route.get("geometry", ""))

        # Extract step-by-step instructions from legs
        steps = []
        for leg in route.get("legs", []):
            for step in leg.get("steps", []):
                name = step.get("name", "")
                instruction = step.get("maneuver", {}).get("type", "continue")
                modifier = step.get("maneuver", {}).get("modifier", "")

                # Build readable instruction
                if name:
                    inst_text = f"{instruction.replace('-', ' ').title()} onto {name}"
                else:
                    inst_text = f"{instruction.replace('-', ' ').title()}"
                if modifier:
                    inst_text = f"{modifier.replace('-', ' ').title()} — {inst_text}"

                steps.append({
                    "instruction": inst_text,
                    "distance_km": round(step.get("distance", 0) / 1000, 2),
                    "duration_min": round(step.get("duration", 0) / 60, 1),
                    "type": 0,
                    "name": name
                })

        # Build route label from major road names
        road_names = [s["name"] for s in steps if s["name"] and len(s["name"]) > 1]
        unique_roads = list(dict.fromkeys(road_names))[:3]
        route_label = " → ".join(unique_roads) if unique_roads else f"Route {idx + 1}"

        distance_km = round(route.get("distance", 0) / 1000, 1)
        duration_min = round(route.get("duration", 0) / 60, 1)

        routes.append({
            "route_id": idx + 1,
            "summary": route_label,
            "distance_km": distance_km,
            "duration_min": duration_min,
            "geometry": geometry,
            "steps": steps,
            "bbox": [],
            "ascent": 0,
            "descent": 0,
            "source": "OSRM"
        })

    return routes


# ──────────────────────────────────────────────────────────────
# GEOMETRY DECODING
# ──────────────────────────────────────────────────────────────

def _decode_geometry(encoded: str) -> list:
    """
    Decode encoded polyline geometry to list of [lat, lng] pairs.
    Uses the standard Google Polyline encoding algorithm (precision 5).
    Works for both ORS and OSRM encoded polylines.
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

"""
Safar AI — Blockage Zone Checker
Checks if a route passes through known blockage hotspots.
"""

import math
from utils.helpers import get_blockages


def check_blockages(route_geometry, departure_hour, radius_km=2.0):
    """Check if route passes near known blockage hotspots."""
    known_blockages = get_blockages()
    nearby = []
    
    for blockage in known_blockages:
        b_lat, b_lng = blockage["lat"], blockage["lng"]
        peak_hours = blockage.get("peak_hours", [])
        base_severity = blockage.get("severity", 0.5)
        
        is_near = False
        min_distance = float("inf")
        
        for i in range(0, len(route_geometry), 5):
            point = route_geometry[i]
            dist = _haversine_km(point[0], point[1], b_lat, b_lng)
            min_distance = min(min_distance, dist)
            if dist <= radius_km:
                is_near = True
                break
        
        if is_near:
            if departure_hour in peak_hours:
                adjusted_severity = min(1.0, base_severity * 1.3)
                is_active = True
            else:
                adjusted_severity = base_severity * 0.4
                is_active = False
            
            nearby.append({
                "city": blockage["city"],
                "description": blockage["description"],
                "severity": round(adjusted_severity, 2),
                "is_active": is_active,
                "lat": b_lat, "lng": b_lng,
                "distance_km": round(min_distance, 1)
            })
    
    total_severity = sum(b["severity"] for b in nearby)
    return {
        "nearby_blockages": nearby,
        "blockage_count": len(nearby),
        "total_severity": round(min(total_severity, 3.0), 2),
        "has_active_blockages": any(b["is_active"] for b in nearby)
    }


def _haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(lat1_r)*math.cos(lat2_r)*math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

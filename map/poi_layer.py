"""
Safar AI — POI Layer
Adds rest areas & fuel station markers.
"""

import folium
from utils.helpers import get_rest_areas
from engine.blockage import _haversine_km


def add_poi_markers(folium_map, route_geometry, radius_km=15.0):
    """Add nearby rest areas and fuel stations along the route."""
    rest_areas = get_rest_areas()
    
    for area in rest_areas:
        # Check if rest area is near the route
        is_near = False
        for i in range(0, len(route_geometry), 10):
            pt = route_geometry[i]
            dist = _haversine_km(pt[0], pt[1], area["lat"], area["lng"])
            if dist <= radius_km:
                is_near = True
                break
        
        if is_near:
            facilities = ", ".join(area.get("facilities", []))
            popup_html = f"""
            <div style='font-family:sans-serif;'>
                <b>🅿️ {area['name']}</b><br>
                🛣️ {area.get('motorway', 'N/A')}<br>
                🏪 {facilities}
            </div>
            """
            folium.Marker(
                location=[area["lat"], area["lng"]],
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"🅿️ {area['name']}",
                icon=folium.Icon(color="blue", icon="parking", prefix="fa")
            ).add_to(folium_map)
    
    return folium_map

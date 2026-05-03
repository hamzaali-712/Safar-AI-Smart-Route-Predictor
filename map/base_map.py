"""
Safar AI — Base Map Creator
Creates the Folium map centered on the route area.
"""

import folium


def create_base_map(origin_coords, destination_coords):
    """Create a Folium base map centered between origin and destination."""
    center_lat = (origin_coords[0] + destination_coords[0]) / 2
    center_lng = (origin_coords[1] + destination_coords[1]) / 2
    
    # Calculate zoom based on distance
    lat_diff = abs(origin_coords[0] - destination_coords[0])
    lng_diff = abs(origin_coords[1] - destination_coords[1])
    max_diff = max(lat_diff, lng_diff)
    
    if max_diff > 5:
        zoom = 6
    elif max_diff > 2:
        zoom = 7
    elif max_diff > 1:
        zoom = 9
    elif max_diff > 0.5:
        zoom = 10
    else:
        zoom = 12
    
    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        control_scale=True
    )
    
    # Origin marker
    folium.Marker(
        location=[origin_coords[0], origin_coords[1]],
        popup="📍 Origin",
        tooltip="Start Point",
        icon=folium.Icon(color="green", icon="play", prefix="fa")
    ).add_to(m)
    
    # Destination marker
    folium.Marker(
        location=[destination_coords[0], destination_coords[1]],
        popup="🏁 Destination",
        tooltip="End Point",
        icon=folium.Icon(color="red", icon="flag-checkered", prefix="fa")
    ).add_to(m)
    
    return m

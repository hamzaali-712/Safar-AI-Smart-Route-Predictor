"""
Safar AI — Route Layer
Draws scored routes on the Folium map with color-coded lines.
"""

import folium


ROUTE_COLORS = ["#00D4AA", "#FFB74D", "#90A4AE", "#CE93D8", "#EF5350"]


def add_route_layers(folium_map, scored_routes):
    """Add all routes to the map. Best route is highlighted green, others are grey/muted."""
    for i, route in enumerate(scored_routes):
        geometry = route.get("geometry", [])
        if not geometry:
            continue
        
        is_best = route.get("is_recommended", False)
        color = ROUTE_COLORS[0] if is_best else ROUTE_COLORS[min(i, len(ROUTE_COLORS)-1)]
        weight = 6 if is_best else 3
        opacity = 1.0 if is_best else 0.5
        
        # Route label
        label = f"{'⭐ ' if is_best else ''}Route {route['rank']}: {route['summary']}"
        popup_html = f"""
        <div style='font-family:sans-serif; min-width:200px;'>
            <b>{label}</b><br>
            📏 Distance: {route['distance_km']} km<br>
            ⏱️ ETA: {route['eta']['eta_min']} min<br>
            🛡️ Safety: {route['safety']['score']}/100<br>
            💰 Cost: PKR {route['cost']['total_cost_pkr']:,}<br>
            🏆 Score: {route['final_score']}/100
        </div>
        """
        
        folium.PolyLine(
            locations=geometry,
            color=color,
            weight=weight,
            opacity=opacity,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"Route {route['rank']} — Score: {route['final_score']}"
        ).add_to(folium_map)
    
    return folium_map

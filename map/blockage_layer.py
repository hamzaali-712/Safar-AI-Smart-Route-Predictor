"""
Safar AI — Blockage Layer
Adds blockage warning markers to the map.
"""

import folium


def add_blockage_markers(folium_map, blockage_info):
    """Add blockage markers for nearby blockages on the route."""
    for blockage in blockage_info.get("nearby_blockages", []):
        color = "red" if blockage["is_active"] else "orange"
        icon_name = "exclamation-triangle" if blockage["is_active"] else "info-circle"
        status = "🔴 ACTIVE" if blockage["is_active"] else "🟡 Low Risk"
        
        popup_html = f"""
        <div style='font-family:sans-serif; min-width:180px;'>
            <b>⚠️ {blockage['description']}</b><br>
            📍 {blockage['city']}<br>
            Status: {status}<br>
            Severity: {blockage['severity']:.0%}
        </div>
        """
        
        folium.Marker(
            location=[blockage["lat"], blockage["lng"]],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"⚠️ {blockage['description']}",
            icon=folium.Icon(color=color, icon=icon_name, prefix="fa")
        ).add_to(folium_map)
    
    return folium_map

"""
Safar AI — Session Route History (JSON-based)
Stores route search history in Streamlit session state.
"""

import streamlit as st
from datetime import datetime
from utils.helpers import format_duration, format_cost


def _ensure_history():
    """Ensure history list exists in session state."""
    if "route_history" not in st.session_state:
        st.session_state.route_history = []


def save_to_history(trip_info, best_route, scored_routes):
    """Save a route search result to session history."""
    _ensure_history()
    
    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "origin": trip_info.get("origin", ""),
        "destination": trip_info.get("destination", ""),
        "mode": trip_info.get("mode", ""),
        "vehicle": trip_info.get("vehicle", ""),
        "best_route": best_route.get("summary", ""),
        "score": best_route.get("final_score", 0),
        "distance_km": best_route.get("distance_km", 0),
        "eta_min": best_route["eta"]["eta_min"] if "eta" in best_route else 0,
        "safety_score": best_route["safety"]["score"] if "safety" in best_route else 0,
        "total_cost_pkr": best_route["cost"]["total_cost_pkr"] if "cost" in best_route else 0,
        "routes_count": len(scored_routes)
    }
    
    st.session_state.route_history.insert(0, record)
    
    # Keep only last 20 records
    if len(st.session_state.route_history) > 20:
        st.session_state.route_history = st.session_state.route_history[:20]


def get_history():
    """Get all route history records."""
    _ensure_history()
    return st.session_state.route_history


def clear_history():
    """Clear all route history."""
    st.session_state.route_history = []


def render_history_table():
    """Render the route history as a styled table in Streamlit."""
    history = get_history()
    
    if not history:
        st.info("📭 No route history yet. Search for a route to get started!")
        return
    
    st.markdown(f"**📋 {len(history)} past searches**")
    
    for i, record in enumerate(history):
        with st.expander(
            f"🕐 {record['timestamp']} — {record['origin']} → {record['destination']} "
            f"(Score: {record['score']})",
            expanded=(i == 0)
        ):
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("📏 Distance", f"{record['distance_km']} km")
            with c2:
                st.metric("⏱️ ETA", format_duration(record["eta_min"]))
            with c3:
                st.metric("🛡️ Safety", f"{record['safety_score']}/100")
            with c4:
                st.metric("💰 Cost", format_cost(record["total_cost_pkr"]))
            
            st.caption(f"Route: {record['best_route']} | Mode: {record['mode']} | Vehicle: {record['vehicle']}")

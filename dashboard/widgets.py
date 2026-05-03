"""
Safar AI — Dashboard Widgets
Reusable Streamlit UI components for the dashboard.
"""

import streamlit as st
from utils.helpers import format_duration, format_distance, format_cost


def render_metric_row(scored_route):
    """Render a row of key metric cards for the best route."""
    r = scored_route
    
    c1, c2, c3, c4, c5 = st.columns(5)
    
    with c1:
        st.metric("🏆 Score", f"{r['final_score']}/100")
    with c2:
        st.metric("📏 Distance", format_distance(r["distance_km"]))
    with c3:
        st.metric("⏱️ ETA", format_duration(r["eta"]["eta_min"]))
    with c4:
        st.metric("🛡️ Safety", f"{r['safety']['score']}/100")
    with c5:
        st.metric("💰 Cost", format_cost(r["cost"]["total_cost_pkr"]))


def render_route_card(route, expanded=False):
    """Render a detailed route info card as an expander."""
    icon = "⭐" if route["is_recommended"] else f"#{route['rank']}"
    label = f"{icon} Route {route['rank']}: {route['summary']} — Score: {route['final_score']}/100"
    
    with st.expander(label, expanded=expanded):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**📏 Distance & Time**")
            st.write(f"• Distance: {format_distance(route['distance_km'])}")
            st.write(f"• Base Duration: {format_duration(route['duration_min'])}")
            st.write(f"• Adjusted ETA: {format_duration(route['eta']['eta_min'])}")
            st.write(f"• Arrival: {route['eta']['arrival_time']}")
            if route["eta"]["delay_min"] > 0:
                st.write(f"• ⚠️ Delay: +{route['eta']['delay_min']:.0f} min")
        
        with col2:
            st.markdown("**🛡️ Safety & Congestion**")
            st.write(f"• Safety: {route['safety']['rating']}")
            st.write(f"• Score: {route['safety']['score']}/100")
            st.write(f"• Congestion Risk: {route['ml_congestion']:.0%}")
            st.write(f"• Time Period: {route['eta']['time_period'].replace('_', ' ').title()}")
            blockages = route["blockage_info"]["blockage_count"]
            if blockages > 0:
                st.write(f"• ⚠️ {blockages} blockage zone(s) nearby")
        
        with col3:
            st.markdown("**💰 Cost Breakdown**")
            st.write(f"• Fuel: {format_cost(route['cost']['fuel_cost_pkr'])}")
            st.write(f"• Toll: {format_cost(route['cost']['toll_cost_pkr'])}")
            st.write(f"• **Total: {format_cost(route['cost']['total_cost_pkr'])}**")
            st.write(f"• Vehicle: {route['cost']['vehicle_label']}")
            st.write(f"• Rate: {route['cost']['cost_per_km']} PKR/km")
        
        # Score breakdown bar
        st.markdown("---")
        st.markdown("**📊 Score Breakdown**")
        sb = route["score_breakdown"]
        score_cols = st.columns(5)
        labels = ["⏱️ Time", "📏 Distance", "🛡️ Safety", "🚗 Congestion", "💰 Cost"]
        values = [sb["time"], sb["distance"], sb["safety"], sb["congestion"], sb["cost"]]
        
        for col, label, val in zip(score_cols, labels, values):
            with col:
                st.metric(label, f"{val:.0f}")
        
        # Turn-by-turn directions
        if route.get("steps"):
            st.markdown("---")
            with st.expander("🧭 Turn-by-Turn Directions"):
                for i, step in enumerate(route["steps"][:20], 1):
                    if step["instruction"]:
                        st.write(f"{i}. {step['instruction']} ({step['distance_km']} km)")

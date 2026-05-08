"""
🧭 Safar AI — Smart Route Predictor
Pakistan's first AI-powered travel intelligence system.
Main Streamlit application entry point.
"""

import sys
from pathlib import Path
_PROJECT_ROOT = str(Path(__file__).resolve().parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import streamlit as st
from datetime import datetime, time
from streamlit_folium import st_folium

from utils.helpers import (
    get_cities_data, get_travel_modes, get_ors_profile,
    get_vehicle_config, geocode_location, fuzzy_match_city,
    format_duration, format_cost
)
from engine.routing import fetch_routes
from engine.scoring import score_routes
from map.base_map import create_base_map
from map.route_layer import add_route_layers
from map.blockage_layer import add_blockage_markers
from map.poi_layer import add_poi_markers
from dashboard.charts import (
    create_route_comparison_chart, create_safety_gauge,
    create_cost_breakdown_chart, create_eta_comparison_chart
)
from dashboard.widgets import render_metric_row, render_route_card
from groq_ai.report import generate_travel_report
from agent.raasta import raasta_chat
from email_service.sender import build_downloadable_report
from database.db import save_to_history, get_history, render_history_table, clear_history

# ──────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Safar AI — Smart Route Predictor",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ──────────────────────────────────────────────────────────────
# CUSTOM CSS
# ──────────────────────────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    
    .main-header {
        background: linear-gradient(135deg, #0a2e2a 0%, #1A1F2E 50%, #1a1025 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(0,212,170,0.15);
        text-align: center;
    }
    .main-header h1 {
        background: linear-gradient(90deg, #00D4AA, #4FC3F7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        font-weight: 700;
        margin: 0;
    }
    .main-header p {
        color: #90A4AE;
        font-size: 1.1rem;
        margin-top: 0.3rem;
    }
    
    .stMetric {
        background: #1A1F2E;
        padding: 12px 16px;
        border-radius: 12px;
        border: 1px solid #2A2F3E;
    }
    
    .sidebar-badge {
        background: linear-gradient(135deg, #00D4AA, #00B894);
        color: #0E1117;
        padding: 4px 14px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
        margin-bottom: 8px;
    }
    
    div[data-testid="stExpander"] {
        background: #1A1F2E;
        border: 1px solid #2A2F3E;
        border-radius: 12px;
    }
    
    .chat-bubble-user {
        background: #1A3A4A;
        padding: 10px 16px;
        border-radius: 12px 12px 4px 12px;
        margin: 6px 0;
        color: #FAFAFA;
    }
    .chat-bubble-bot {
        background: #1A2E1A;
        padding: 10px 16px;
        border-radius: 12px 12px 12px 4px;
        margin: 6px 0;
        color: #FAFAFA;
    }
    
    section[data-testid="stSidebar"] {
        background: #12161F;
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────────────────────

st.markdown("""
<div class="main-header">
    <h1>🧭 Safar AI</h1>
    <p>Pakistan's Smart Route Predictor — Powered by AI & Real Routing Data</p>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# SIDEBAR — User Inputs
# ──────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown('<span class="sidebar-badge">🛰️ SAFAR AI</span>', unsafe_allow_html=True)
    st.markdown("### 🗺️ Plan Your Trip")
    st.markdown("---")
    
    cities = get_cities_data()
    city_names = sorted(cities.keys())
    
    origin = st.selectbox("📍 Origin City", city_names, index=city_names.index("Lahore") if "Lahore" in city_names else 0)
    destination = st.selectbox("🏁 Destination City", city_names, index=city_names.index("Islamabad") if "Islamabad" in city_names else 1)
    
    st.markdown("---")
    
    travel_mode = st.selectbox("🚗 Travel Mode", get_travel_modes())
    
    vehicles = get_vehicle_config()
    vehicle_labels = {v["label"]: k for k, v in vehicles.items()}
    vehicle_label = st.selectbox("🚙 Vehicle Type", list(vehicle_labels.keys()))
    vehicle_type = vehicle_labels[vehicle_label]
    
    st.markdown("---")
    
    departure_date = st.date_input("📅 Departure Date", datetime.now())
    departure_time_input = st.time_input("🕐 Departure Time", time(8, 0))
    
    departure_datetime = datetime.combine(departure_date, departure_time_input)
    
    st.markdown("---")
    
    search_clicked = st.button("🔍 Find Best Route", use_container_width=True, type="primary")
    
    st.markdown("---")
    st.markdown("### 📜 Route History")
    
    if st.button("🗑️ Clear History", use_container_width=True):
        clear_history()
        st.rerun()
    
    history = get_history()
    if history:
        for rec in history[:5]:
            st.caption(f"🕐 {rec['timestamp']}")
            st.caption(f"   {rec['origin']} → {rec['destination']} ({rec['score']}/100)")
    else:
        st.caption("No searches yet.")

# ──────────────────────────────────────────────────────────────
# MAIN CONTENT
# ──────────────────────────────────────────────────────────────

if origin == destination:
    st.warning("⚠️ Origin and destination must be different.")
    st.stop()

# Process route search
if search_clicked or "scored_routes" in st.session_state:
    
    if search_clicked:
        # Geocode
        origin_data = cities[origin]
        dest_data = cities[destination]
        origin_coords = (origin_data["lat"], origin_data["lng"])
        dest_coords = (dest_data["lat"], dest_data["lng"])
        
        profile = get_ors_profile(travel_mode)
        
        with st.spinner("🛰️ Fetching routes..."):
            raw_routes = fetch_routes(origin_coords, dest_coords, profile, alternatives=3)
        
        if not raw_routes:
            st.error("❌ No routes found. Please check:")
            st.markdown("""
            - Your **ORS_API_KEY** in `.streamlit/secrets.toml` is valid
            - The cities are **routable** with the selected travel mode
            - Your **internet connection** is working
            - Try a different **travel mode** (e.g. Driving instead of Walking for long distances)
            """)
            st.stop()
        
        # Show routing source
        route_source = raw_routes[0].get("source", "ORS")
        if route_source == "OSRM":
            st.info("ℹ️ Routes provided by OSRM (free fallback). Add a valid ORS_API_KEY for enhanced routing.")
        
        with st.spinner("🧠 Running AI Scoring Engine..."):
            scored = score_routes(
                raw_routes, origin, destination,
                departure_datetime, vehicle_type, profile
            )
        
        if not scored:
            st.error("❌ Scoring failed. Please try again.")
            st.stop()
        
        # Store in session
        st.session_state.scored_routes = scored
        st.session_state.trip_info = {
            "origin": origin,
            "destination": destination,
            "mode": travel_mode,
            "departure": departure_datetime.strftime("%Y-%m-%d %H:%M"),
            "vehicle": vehicle_label
        }
        st.session_state.origin_coords = origin_coords
        st.session_state.dest_coords = dest_coords
        
        # Save to history
        save_to_history(st.session_state.trip_info, scored[0], scored)
    
    # Retrieve from session
    scored = st.session_state.scored_routes
    trip_info = st.session_state.trip_info
    origin_coords = st.session_state.origin_coords
    dest_coords = st.session_state.dest_coords
    best = scored[0]
    
    # ── METRIC ROW ──
    st.markdown(f"### ⭐ Recommended: {best['summary']}")
    render_metric_row(best)
    
    # ── TABS ──
    tab_map, tab_charts, tab_report, tab_details, tab_chat, tab_history = st.tabs([
        "🗺️ Map", "📊 Analytics", "📝 AI Report", "📋 Route Details", "💬 Raasta Chat", "📜 History"
    ])
    
    # ── TAB: MAP ──
    with tab_map:
        m = create_base_map(origin_coords, dest_coords)
        m = add_route_layers(m, scored)
        m = add_blockage_markers(m, best["blockage_info"])
        if best.get("geometry"):
            m = add_poi_markers(m, best["geometry"])
        
        st_folium(m, use_container_width=True, height=520)
        
        st.caption(f"🟢 Green = Recommended Route | 🟡 Orange = Alternative | 📍 Blue = Rest Areas | 🔴 Red = Blockages")
    
    # ── TAB: CHARTS ──
    with tab_charts:
        col_left, col_right = st.columns([3, 2])
        
        with col_left:
            fig_compare = create_route_comparison_chart(scored)
            st.plotly_chart(fig_compare, use_container_width=True)
            
            fig_eta = create_eta_comparison_chart(scored)
            st.plotly_chart(fig_eta, use_container_width=True)
        
        with col_right:
            fig_gauge = create_safety_gauge(best["safety"]["score"])
            st.plotly_chart(fig_gauge, use_container_width=True)
            
            fig_cost = create_cost_breakdown_chart(best["cost"])
            if fig_cost:
                st.plotly_chart(fig_cost, use_container_width=True)
    
    # ── TAB: AI REPORT ──
    with tab_report:
        if "travel_report" not in st.session_state or search_clicked:
            with st.spinner("🤖 Generating Smart Travel Report via Groq AI..."):
                report = generate_travel_report(scored, trip_info)
                st.session_state.travel_report = report
        
        st.markdown(st.session_state.travel_report)
        
        # Download report section
        st.markdown("---")
        st.markdown("### 📥 Download Report")
        
        report_html = build_downloadable_report(
            trip_info, best, st.session_state.travel_report
        )
        
        file_name = f"Safar_AI_Report_{trip_info['origin']}_to_{trip_info['destination']}.html"
        
        st.download_button(
            label="📥 Download Smart Travel Report",
            data=report_html,
            file_name=file_name,
            mime="text/html",
            use_container_width=True
        )
    
    # ── TAB: ROUTE DETAILS ──
    with tab_details:
        for i, route in enumerate(scored):
            render_route_card(route, expanded=(i == 0))
    
    # ── TAB: RAASTA CHAT ──
    with tab_chat:
        st.markdown("### 💬 Ask Raasta — Your AI Travel Assistant")
        st.caption("Ask about safety, best times, fuel savings, weather — in English or Urdu!")
        
        # Initialize chat history
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = []
        
        # Display chat history
        for msg in st.session_state.chat_messages:
            css_class = "chat-bubble-user" if msg["role"] == "user" else "chat-bubble-bot"
            label = "🧑 You" if msg["role"] == "user" else "🤖 Raasta"
            st.markdown(f"**{label}**")
            st.markdown(f'<div class="{css_class}">{msg["content"]}</div>', unsafe_allow_html=True)
        
        # Chat input
        user_input = st.chat_input("Ask Raasta anything about your trip...")
        
        if user_input:
            st.session_state.chat_messages.append({"role": "user", "content": user_input})
            
            route_context = {
                "origin": trip_info["origin"],
                "destination": trip_info["destination"],
                "best_route": best
            }
            
            with st.spinner("🤖 Raasta is thinking..."):
                response = raasta_chat(
                    user_input,
                    route_context=route_context,
                    chat_history=st.session_state.chat_messages[:-1]
                )
            
            st.session_state.chat_messages.append({"role": "assistant", "content": response})
            st.rerun()
    
    # ── TAB: HISTORY ──
    with tab_history:
        st.markdown("### 📜 Route Search History")
        render_history_table()

else:
    # Landing state
    st.markdown("""
    <div style="text-align:center; padding:60px 20px;">
        <h2 style="color:#90A4AE;">👈 Select your trip details in the sidebar</h2>
        <p style="color:#546E7A; font-size:1.1rem;">
            Choose origin, destination, travel mode & departure time, then hit <strong style="color:#00D4AA;">Find Best Route</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature showcase
    st.markdown("---")
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        st.markdown("### 🛰️ Smart Routing")
        st.write("AI-scored multi-route comparison via OpenRouteService")
    with f2:
        st.markdown("### 🧠 ML Predictions")
        st.write("XGBoost congestion & blockage probability forecasting")
    with f3:
        st.markdown("### 📝 Groq AI Reports")
        st.write("Deep travel analysis with personalized tips")
    with f4:
        st.markdown("### 💬 Raasta Chatbot")
        st.write("Ask anything about your route in English or Urdu")

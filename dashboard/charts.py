"""
Safar AI — Plotly Dashboard Charts
Bar charts, gauges, and comparison visuals for route analysis.
"""

import plotly.graph_objects as go
import plotly.express as px


THEME = {
    "bg": "#0E1117", "card_bg": "#1A1F2E",
    "text": "#FAFAFA", "accent": "#00D4AA",
    "warn": "#FFB74D", "danger": "#EF5350",
    "colors": ["#00D4AA", "#FFB74D", "#90A4AE", "#CE93D8", "#EF5350"]
}


def create_route_comparison_chart(scored_routes):
    """Create a grouped bar chart comparing all routes across key metrics."""
    labels = [f"Route {r['rank']}" for r in scored_routes]
    
    fig = go.Figure()
    
    metrics = [
        ("Score", [r["final_score"] for r in scored_routes], THEME["accent"]),
        ("Safety", [r["safety"]["score"] for r in scored_routes], "#4FC3F7"),
        ("ETA (min)", [r["eta"]["eta_min"] for r in scored_routes], THEME["warn"]),
    ]
    
    for name, values, color in metrics:
        fig.add_trace(go.Bar(name=name, x=labels, y=values, marker_color=color,
                             text=[f"{v:.0f}" for v in values], textposition="auto"))
    
    fig.update_layout(
        title="📊 Route Comparison",
        barmode="group",
        template="plotly_dark",
        paper_bgcolor=THEME["bg"],
        plot_bgcolor=THEME["card_bg"],
        font=dict(color=THEME["text"]),
        height=380,
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig


def create_safety_gauge(score):
    """Create a safety index gauge chart (0-100)."""
    if score >= 80:
        color = "#00D4AA"
    elif score >= 60:
        color = "#FFB74D"
    elif score >= 40:
        color = "#FF8A65"
    else:
        color = "#EF5350"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        title={"text": "🛡️ Safety Index", "font": {"size": 18, "color": THEME["text"]}},
        number={"suffix": "/100", "font": {"color": THEME["text"]}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": THEME["text"]},
            "bar": {"color": color},
            "bgcolor": THEME["card_bg"],
            "steps": [
                {"range": [0, 40], "color": "rgba(239,83,80,0.2)"},
                {"range": [40, 60], "color": "rgba(255,138,101,0.2)"},
                {"range": [60, 80], "color": "rgba(255,183,77,0.2)"},
                {"range": [80, 100], "color": "rgba(0,212,170,0.2)"}
            ],
            "threshold": {"line": {"color": "white", "width": 2}, "thickness": 0.75, "value": score}
        }
    ))
    
    fig.update_layout(
        paper_bgcolor=THEME["bg"],
        font=dict(color=THEME["text"]),
        height=280,
        margin=dict(l=30, r=30, t=60, b=20)
    )
    
    return fig


def create_cost_breakdown_chart(cost_data):
    """Create a pie/donut chart for cost breakdown."""
    labels = ["Fuel", "Toll"]
    values = [cost_data["fuel_cost_pkr"], cost_data["toll_cost_pkr"]]
    colors = [THEME["accent"], THEME["warn"]]
    
    # Filter zero values
    filtered = [(l, v, c) for l, v, c in zip(labels, values, colors) if v > 0]
    if not filtered:
        return None
    
    labels, values, colors = zip(*filtered)
    
    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        hole=0.55,
        marker=dict(colors=colors),
        textinfo="label+value",
        texttemplate="%{label}<br>PKR %{value:,.0f}",
        textfont=dict(color="white")
    ))
    
    fig.update_layout(
        title="💰 Cost Breakdown (PKR)",
        template="plotly_dark",
        paper_bgcolor=THEME["bg"],
        font=dict(color=THEME["text"]),
        height=300,
        margin=dict(l=20, r=20, t=60, b=20),
        showlegend=False
    )
    
    return fig


def create_eta_comparison_chart(scored_routes):
    """Create horizontal bar chart comparing ETA across routes."""
    labels = [f"Route {r['rank']}" for r in scored_routes]
    etas = [r["eta"]["eta_min"] for r in scored_routes]
    colors = [THEME["accent"] if r["is_recommended"] else THEME["colors"][2] for r in scored_routes]
    
    fig = go.Figure(go.Bar(
        x=etas, y=labels, orientation="h",
        marker_color=colors,
        text=[f"{e:.0f} min" for e in etas],
        textposition="auto"
    ))
    
    fig.update_layout(
        title="⏱️ ETA Comparison",
        template="plotly_dark",
        paper_bgcolor=THEME["bg"],
        plot_bgcolor=THEME["card_bg"],
        font=dict(color=THEME["text"]),
        height=250,
        margin=dict(l=80, r=40, t=60, b=40),
        xaxis_title="Minutes"
    )
    
    return fig

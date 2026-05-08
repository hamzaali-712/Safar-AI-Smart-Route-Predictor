"""
Safar AI — Route Scoring Engine
Weighted multi-factor scoring algorithm to rank routes.
"""

from datetime import datetime
from engine.eta import calculate_eta
from engine.cost import calculate_trip_cost
from engine.safety import calculate_safety_score, get_province_for_city
from engine.blockage import check_blockages
from ml.predict import predict_blockage
from utils.helpers import get_cities_data, fuzzy_match_city


def score_routes(
    routes, origin_name, destination_name,
    departure_time, vehicle_type="sedan", profile="driving-car"
):
    """
    Score and rank all routes using weighted multi-factor algorithm.
    
    Score = (0.30 * time) + (0.15 * distance) + (0.25 * safety) + (0.20 * congestion) + (0.10 * cost)
    """
    if not routes:
        return []
    
    origin_city = fuzzy_match_city(origin_name)
    dest_city = fuzzy_match_city(destination_name)
    cities = get_cities_data()
    
    origin_zone = cities.get(origin_city, {}).get("zone", "urban")
    origin_province = get_province_for_city(origin_city)
    dest_province = get_province_for_city(dest_city)
    
    # Collect raw values for normalization
    max_time = max(r["duration_min"] for r in routes)
    max_dist = max(r["distance_km"] for r in routes)
    
    scored = []
    cost_values = []
    
    for route in routes:
        # 1. ETA
        eta = calculate_eta(route["duration_min"], departure_time, route["distance_km"], origin_zone)
        
        # 2. Cost
        cost = calculate_trip_cost(route["distance_km"], vehicle_type, route["summary"])
        cost_values.append(cost["total_cost_pkr"])
        
        # 3. Safety
        safety = calculate_safety_score(
            origin_province, dest_province,
            departure_time.hour, route["distance_km"], route["summary"]
        )
        
        # 4. Blockage check
        blockage_info = check_blockages(route["geometry"], departure_time.hour)
        
        # 5. ML congestion prediction
        ml_congestion = predict_blockage(
            departure_time.hour, departure_time.weekday(),
            departure_time.month, route["distance_km"], origin_zone
        )
        
        scored.append({
            **route,
            "eta": eta,
            "cost": cost,
            "safety": safety,
            "blockage_info": blockage_info,
            "ml_congestion": ml_congestion
        })
    
    max_cost = max(cost_values) if cost_values else 1
    min_time = min(r["eta"]["eta_min"] for r in scored) if scored else 1
    min_dist = min(r["distance_km"] for r in scored) if scored else 1
    min_cost = min(cost_values) if cost_values else 1
    
    # Calculate final weighted scores
    for route in scored:
        # Use ratio-based scoring: best route gets 1.0, worse routes get proportionally less
        time_score = min_time / max(route["eta"]["eta_min"], 1)
        dist_score = min_dist / max(route["distance_km"], 1)
        safety_score = route["safety"]["score"] / 100
        congestion_score = 1 - route["ml_congestion"]
        cost_score = min_cost / max(route["cost"]["total_cost_pkr"], 1)
        
        # Weighted sum
        final = (
            0.30 * max(0, time_score) +
            0.15 * max(0, dist_score) +
            0.25 * max(0, safety_score) +
            0.20 * max(0, congestion_score) +
            0.10 * max(0, cost_score)
        )
        
        route["final_score"] = round(final * 100, 1)
        route["score_breakdown"] = {
            "time": round(time_score * 100, 1),
            "distance": round(dist_score * 100, 1),
            "safety": round(safety_score * 100, 1),
            "congestion": round(congestion_score * 100, 1),
            "cost": round(cost_score * 100, 1)
        }
    
    # Sort by score descending
    scored.sort(key=lambda x: x["final_score"], reverse=True)
    
    # Mark recommended route
    for i, route in enumerate(scored):
        route["is_recommended"] = (i == 0)
        route["rank"] = i + 1
    
    return scored

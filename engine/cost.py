"""
Safar AI — Trip Cost Calculator
Calculates fuel cost and toll charges in PKR.
"""

from utils.helpers import get_fuel_prices, get_vehicle_config


def calculate_trip_cost(
    distance_km: float,
    vehicle_type: str = "sedan",
    route_summary: str = ""
) -> dict:
    """
    Calculate total trip cost including fuel and estimated tolls.
    
    Args:
        distance_km: total route distance
        vehicle_type: key from vehicle_config.json
        route_summary: route label to detect motorway for toll estimation
    
    Returns:
        dict with fuel_cost, toll_cost, total_cost, fuel_liters, breakdown details
    """
    fuel_data = get_fuel_prices()
    vehicles = get_vehicle_config()
    
    vehicle = vehicles.get(vehicle_type, vehicles["sedan"])
    fuel_type = vehicle["fuel_type"]
    consumption_per_100km = vehicle["consumption_per_100km"]
    
    # Fuel price per unit
    fuel_info = fuel_data["fuel_types"].get(fuel_type, {"price_per_liter": 275.0})
    
    if fuel_type == "electric":
        kwh_needed = (distance_km / 100) * consumption_per_100km
        fuel_cost = kwh_needed * fuel_info["price_per_kwh"]
        fuel_units = round(kwh_needed, 1)
        fuel_unit_label = "kWh"
    elif fuel_type == "cng":
        kg_needed = (distance_km / 100) * consumption_per_100km
        fuel_cost = kg_needed * fuel_info["price_per_kg"]
        fuel_units = round(kg_needed, 1)
        fuel_unit_label = "kg"
    else:
        liters_needed = (distance_km / 100) * consumption_per_100km
        fuel_cost = liters_needed * fuel_info["price_per_liter"]
        fuel_units = round(liters_needed, 1)
        fuel_unit_label = "liters"
    
    # Estimate toll charges based on distance and vehicle type
    toll_cost = _estimate_toll(distance_km, vehicle_type, route_summary, fuel_data)
    
    total_cost = fuel_cost + toll_cost
    
    return {
        "fuel_cost_pkr": round(fuel_cost),
        "toll_cost_pkr": round(toll_cost),
        "total_cost_pkr": round(total_cost),
        "fuel_units": fuel_units,
        "fuel_unit_label": fuel_unit_label,
        "fuel_type": fuel_type,
        "vehicle_label": vehicle["label"],
        "consumption_rate": f"{consumption_per_100km} {fuel_unit_label}/100km",
        "cost_per_km": round(total_cost / max(distance_km, 1), 1)
    }


def _estimate_toll(
    distance_km: float,
    vehicle_type: str,
    route_summary: str,
    fuel_data: dict
) -> float:
    """Estimate toll charges based on motorway detection and distance."""
    toll_rates = fuel_data.get("toll_rates", {})
    summary_lower = route_summary.lower()
    
    # Map vehicle types to toll categories
    toll_category = "car"
    if vehicle_type == "motorcycle":
        toll_category = "motorcycle"
    elif vehicle_type in ["bus", "truck"]:
        toll_category = "bus"
    
    # Check if any known motorway is in the route summary
    for motorway, rates in toll_rates.items():
        if motorway.lower() in summary_lower and motorway != "default":
            return rates.get(toll_category, 200)
    
    # Estimate toll for long-distance routes (likely motorway usage)
    if distance_km > 100:
        base_toll = toll_rates.get("default", {}).get(toll_category, 200)
        # Scale based on distance segments
        segments = int(distance_km / 150)
        return base_toll * max(1, segments)
    
    return 0  # No toll for short urban routes

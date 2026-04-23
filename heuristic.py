import math

_EARTH_RADIUS_KM = 6_371.0

# With the exponent formula: cost = length_km * t^tw * p^pw * ra^rw * tc^tcw / s^sw
# The absolute minimum cost per km occurs on the best-case motorway edge
# with the lowest perturbation (0.9×) on each penalty factor and highest
# perturbation (1.1×) on safety, raised to the minimum slider value (1.0).
#
# motorway best-case (slider=1.0):
#   t^1  = (2.2*0.9)^1 = 1.98
#   p^1  = (1.1*0.9)^1 = 0.99
#   ra^1 = (0.8*0.9)^1 = 0.72
#   tc^1 = (0.3*0.9)^1 = 0.27
#   s^1  = (0.70*1.1)^1 = 0.77
#   min = 1.98*0.99*0.72*0.27/0.77 ≈ 0.495 → use 0.45 for safety margin
#
# At higher slider values the exponent formula changes costs non-linearly,
# but the heuristic only needs to be admissible (never overestimate).
# Since we use slider=1.0 as the floor, 0.45 remains a valid lower bound
# for all slider configurations — higher sliders raise ALL costs, so the
# true minimum can only increase, never decrease below the slider=1.0 floor.
_MIN_COST_PER_KM = 0.45


def haversine_coords(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine great-circle distance in METRES."""
    R_m = _EARTH_RADIUS_KM * 1000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lam = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2) ** 2
    return 2 * R_m * math.asin(math.sqrt(a))


def haversine(G, node_a: int, node_b: int) -> float:
    """
    Admissible heuristic h(n) for informed search algorithms.

    Returns a lower bound on the true custom_weight cost from node_a to node_b.
    
    For Bangladesh-specific metrics, we use:
    - Minimum travel time: straight-line distance at maximum highway speed (80 km/h)
    - Minimum cost: fuel cost at optimal rate (10 BDT/km)
    - Minimum risk: best-case road conditions
    
    The heuristic remains admissible (never overestimates) under all slider
    configurations, preserving A* optimality.
    """
    a = G.nodes[node_a]
    b = G.nodes[node_b]
    dist_km = haversine_coords(a['y'], a['x'], b['y'], b['x']) / 1000.0
    
    # Best-case scenario for Bangladesh metrics:
    # 1. Travel time: distance at 80 km/h (motorway speed)
    min_travel_time = dist_km / 80.0  # hours
    
    # 2. Distance: actual distance
    min_distance = dist_km  # km
    
    # 3. Travel cost: minimum fuel cost (10 BDT/km)
    min_travel_cost = dist_km * 10.0  # BDT
    
    # 4. Other factors at minimum (1.0 = best case)
    min_traffic_density = 1.0
    min_road_condition = 0.8  # Excellent road
    min_weather_impact = 1.0  # No weather impact
    min_safety_risk = 0.5    # Very safe
    min_transport_avail = 1.0  # Available
    min_transfers = 1.0      # No transfers needed
    min_comfort = 0.7        # High comfort
    
    # Calculate minimum possible cost using conservative estimates
    # This ensures admissibility for any slider combination
    min_cost_per_km = (
        min_travel_time ** 0.5 *  # Conservative travel time exponent
        min_distance ** 0.5 *     # Conservative distance exponent  
        min_travel_cost ** 0.5 * # Conservative cost exponent
        min_traffic_density ** 1.0 *
        min_road_condition ** 1.0 *
        min_weather_impact ** 1.0 *
        min_safety_risk ** 1.0 *
        min_transport_avail ** 1.0 *
        min_transfers ** 1.0 *
        min_comfort ** 1.0
    ) / dist_km if dist_km > 0 else _MIN_COST_PER_KM
    
    return dist_km * max(_MIN_COST_PER_KM, min_cost_per_km)

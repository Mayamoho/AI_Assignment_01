import networkx as nx
from heuristic import haversine


def compute_g(path: list, G: nx.MultiDiGraph, weight: str = 'custom_weight') -> float:
    """
    g(n): cumulative cost from start to the last node in path.
    Sums the edge weights along the given path.
    
    For Bangladesh-specific metrics, this includes all factors:
    travel_time, distance, travel_cost, traffic_density, road_condition,
    weather_impact, safety_risk, transport_availability, transfers, comfort
    """
    total = 0.0
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        # MultiDiGraph may have parallel edges; take the minimum weight edge
        edge_data = G[u][v]
        min_w = min(data.get(weight, 1.0) for data in edge_data.values())
        total += min_w
    return total


def compute_detailed_metrics(path: list, G: nx.MultiDiGraph) -> dict:
    """
    Compute detailed metrics for a path including all Bangladesh-specific factors.
    Returns a dictionary with individual metric values.
    """
    metrics = {
        'travel_time': 0.0,      # hours
        'distance': 0.0,         # km
        'travel_cost': 0.0,      # BDT
        'traffic_density': 0.0,  # congestion factor
        'road_condition': 0.0,   # quality factor
        'weather_impact': 0.0,   # weather penalty
        'safety_risk': 0.0,      # risk factor
        'transport_avail': 0.0,  # availability factor
        'transfers': 0.0,        # number of transfers
        'comfort': 0.0,          # comfort factor
        'total_cost': 0.0        # composite custom_weight
    }
    
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        edge_data = G[u][v]
        
        # Find the minimum weight edge (for parallel edges)
        min_edge = min(edge_data.values(), key=lambda d: d.get('custom_weight', float('inf')))
        
        # Accumulate each metric
        metrics['travel_time'] += min_edge.get('travel_time', 0)
        metrics['distance'] += min_edge.get('distance', 0)
        metrics['travel_cost'] += min_edge.get('travel_cost', 0)
        metrics['traffic_density'] += min_edge.get('traffic_density', 0)
        metrics['road_condition'] += min_edge.get('road_condition', 0)
        metrics['weather_impact'] += min_edge.get('weather_impact', 0)
        metrics['safety_risk'] += min_edge.get('safety_risk', 0)
        metrics['transport_avail'] += min_edge.get('transport_availability', 0)
        metrics['transfers'] += min_edge.get('transfers', 0)
        metrics['comfort'] += min_edge.get('comfort', 0)
        metrics['total_cost'] += min_edge.get('custom_weight', 0)
    
    return metrics


def compute_h(G: nx.MultiDiGraph, node: int, goal: int) -> float:
    """
    h(n): haversine straight-line distance in meters from node to goal.
    Admissible and consistent — never overestimates actual road cost.
    """
    return haversine(G, node, goal)


def compute_f(path: list, G: nx.MultiDiGraph, weight: str, goal: int) -> float:
    """
    f(n) = g(n) + h(n)
    Used by A*, IDA*, Greedy, and Bidirectional A* to prioritize nodes.
    """
    return compute_g(path, G, weight) + compute_h(G, path[-1], goal)

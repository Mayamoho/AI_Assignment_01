import networkx as nx
from models import SearchResult
from evaluation import compute_detailed_metrics


def compute_path_cost(G: nx.MultiDiGraph, path: list, weight: str = 'custom_weight') -> float:
    """Sum of edge weights along the path. Returns 0 for empty or single-node paths."""
    total = 0.0
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        edge_data = G[u][v]
        total += min(d.get(weight, 1.0) for d in edge_data.values())
    return total


def compute_hop_count(path: list) -> int:
    """Number of edges in the path (nodes - 1)."""
    return max(0, len(path) - 1)


def build_comparison_record(name: str, result: SearchResult,
                           G: nx.MultiDiGraph, weight: str = 'custom_weight') -> dict:
    """Build a standardized comparison dict for one algorithm run."""
    record = {
        'algorithm': name,
        'path_cost': round(compute_path_cost(G, result.path, weight), 4) if result.path else None,
        'hop_count': compute_hop_count(result.path),
        'nodes_expanded': result.nodes_expanded,
        'path': result.path,
    }
    
    # Add detailed Bangladesh-specific metrics if path exists
    if result.path and len(result.path) > 1:
        detailed = compute_detailed_metrics(result.path, G)
        record.update({
            'travel_time_hours': round(detailed['travel_time'], 2),
            'distance_km': round(detailed['distance'], 2),
            'travel_cost_bdt': round(detailed['travel_cost'], 0),
            'traffic_density': round(detailed['traffic_density'], 2),
            'road_condition': round(detailed['road_condition'], 2),
            'weather_impact': round(detailed['weather_impact'], 2),
            'safety_risk': round(detailed['safety_risk'], 2),
            'transport_availability': round(detailed['transport_avail'], 2),
            'transfers': round(detailed['transfers'], 1),
            'comfort': round(detailed['comfort'], 2),
        })
    else:
        # Default values for no path
        record.update({
            'travel_time_hours': None,
            'distance_km': None,
            'travel_cost_bdt': None,
            'traffic_density': None,
            'road_condition': None,
            'weather_impact': None,
            'safety_risk': None,
            'transport_availability': None,
            'transfers': None,
            'comfort': None,
        })
    
    return record


def build_metrics_summary(records: list) -> dict:
    """Build a summary of all metrics across algorithms for dashboard display."""
    if not records:
        return {}
    
    # Filter to only records with valid paths
    valid_records = [r for r in records if r.get('path_cost') is not None]
    
    if not valid_records:
        return {}
    
    summary = {
        'algorithms': [r['algorithm'] for r in valid_records],
        'path_costs': [r['path_cost'] for r in valid_records],
        'hop_counts': [r['hop_count'] for r in valid_records],
        'nodes_expanded': [r['nodes_expanded'] for r in valid_records],
        
        # Bangladesh-specific metrics
        'travel_times': [r.get('travel_time_hours', 0) for r in valid_records],
        'distances': [r.get('distance_km', 0) for r in valid_records],
        'travel_costs': [r.get('travel_cost_bdt', 0) for r in valid_records],
        'traffic_densities': [r.get('traffic_density', 0) for r in valid_records],
        'road_conditions': [r.get('road_condition', 0) for r in valid_records],
        'weather_impacts': [r.get('weather_impact', 0) for r in valid_records],
        'safety_risks': [r.get('safety_risk', 0) for r in valid_records],
        'transport_availabilities': [r.get('transport_availability', 0) for r in valid_records],
        'transfers': [r.get('transfers', 0) for r in valid_records],
        'comforts': [r.get('comfort', 0) for r in valid_records],
    }
    
    # Find best values for each metric
    summary['best'] = {
        'min_cost': min(summary['path_costs']),
        'min_time': min(summary['travel_times']),
        'min_distance': min(summary['distances']),
        'min_cost_bdt': min(summary['travel_costs']),
        'min_traffic': min(summary['traffic_densities']),
        'best_road_condition': min(summary['road_conditions']),
        'min_weather_impact': min(summary['weather_impacts']),
        'min_safety_risk': min(summary['safety_risks']),
        'max_transport_avail': max(summary['transport_availabilities']),
        'min_transfers': min(summary['transfers']),
        'max_comfort': max(summary['comforts']),
    }
    
    return summary

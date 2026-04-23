"""
FastAPI backend for dynamic pathfinding dashboard.
Allows real-time weight adjustment and live node placement without re-running main.py.
"""
import json
import os
import pickle
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
import networkx as nx

from comparison import run_all
from heuristic import haversine_coords
from map_loader import load_graph, build_search_graph
from visualization import generate_path_map, generate_complexity_graphs, generate_expansion_maps, generate_comparison_graph

# ── Global state ──────────────────────────────────────────────────────────────
OSM_G: Optional[nx.MultiDiGraph] = None   # full OSM graph for snapping
GRAPH: Optional[nx.MultiDiGraph] = None   # current search subgraph
NODES: list = []                           # chosen nodes [{id, lat, lon, label}]
START: Optional[int] = None
GOAL:  Optional[int] = None
GEOCACHE: dict = {}
_KDTREE = None        # pre-built KD-tree for fast nearest-node lookup
_KDTREE_IDS = None    # node IDs corresponding to KD-tree entries
_SEED = 42
_CENTER = (23.7766, 90.4227)
_GRAPH_CACHE: dict = {}   # frozenset(node_ids) → subgraph, avoids rebuild on same nodes


def _load_state():
    global GRAPH, NODES, START, GOAL, GEOCACHE, OSM_G, _KDTREE, _KDTREE_IDS, _GRAPH_CACHE

    print("  Loading OSM graph for node snapping...")
    OSM_G = load_graph(center=_CENTER, dist=15000, seed=_SEED)
    print(f"  OSM graph ready: {OSM_G.number_of_nodes()} nodes")

    # Build KD-tree once for O(log n) nearest-node lookup
    from scipy.spatial import KDTree
    import numpy as np
    node_ids = list(OSM_G.nodes)
    coords = np.array([[OSM_G.nodes[n]['y'], OSM_G.nodes[n]['x']] for n in node_ids])
    _KDTREE = KDTree(coords)
    _KDTREE_IDS = node_ids
    print(f"  KD-tree built for {len(node_ids)} nodes")

    # Clear subgraph cache so new diversity-aware build_search_graph is used
    _GRAPH_CACHE.clear()

    # Load last saved search state if available
    state_file = "cache/app_state.pkl"
    geocache_file = "cache/geocache.json"
    if os.path.exists(state_file):
        with open(state_file, 'rb') as f:
            data = pickle.load(f)
            NODES = data['nodes']
            START = data['start']
            GOAL  = data['goal']
        # Rebuild subgraph with current logic (not the stale cached version)
        if NODES and len(NODES) >= 2:
            print(f"  Rebuilding search graph for saved START→GOAL...")
            GRAPH = build_search_graph(OSM_G, NODES, seed=_SEED)
            _GRAPH_CACHE[(NODES[0]['id'], NODES[-1]['id'])] = GRAPH
            print(f"  Search graph ready: {GRAPH.number_of_nodes()} nodes")
    if os.path.exists(geocache_file):
        with open(geocache_file) as f:
            GEOCACHE = {int(k): v for k, v in json.load(f).items()}


@asynccontextmanager
async def lifespan(app):
    _load_state()
    yield


app = FastAPI(title="AI Pathfinding API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class WeightParams(BaseModel):
    # Primary Metrics
    travel_time_weight:    float = 1.5   # Travel Time (Most Important)
    distance_weight:       float = 1.0   # Distance in km
    travel_cost_weight:    float = 1.2  # Travel Cost (BDT) - fuel, tolls
    
    # Bangladesh-Specific Factors
    traffic_density_weight: float = 1.3   # Traffic Density / Jam Probability
    road_condition_weight:  float = 1.1   # Road Condition Quality
    weather_impact_weight:  float = 1.0   # Weather Impact (rain/flooding)
    safety_risk_weight:     float = 1.2   # Safety / Risk (accidents, lighting)
    
    # Context-Specific Metrics
    transport_availability_weight: float = 1.0   # Transport Availability
    transfers_weight:       float = 0.8   # Number of Transfers (public transport)
    comfort_weight:          float = 0.5   # Comfort / Convenience
    
    # Legacy weights (for backward compatibility)
    traffic_weight:  float = 1.0   # Legacy Traffic Intensity exponent
    safety_weight:   float = 1.0   # Legacy Safety Index exponent
    road_age_weight: float = 1.0   # Legacy Road Quality exponent
    turn_weight:     float = 1.0   # Legacy Turn Complexity exponent


class SnapRequest(BaseModel):
    lat: float
    lon: float


class SetNodesRequest(BaseModel):
    node_ids: list[int]
    params: WeightParams = WeightParams()


# Road type sensitivity dicts removed — no longer needed after switching
# to the exponent-based weight formula in _apply_weights.


def _apply_weights(G: nx.MultiDiGraph, params: WeightParams) -> nx.MultiDiGraph:
    """
    Recompute custom_weight using comprehensive Bangladesh-specific metrics.

    Primary Metrics:
      travel_time     - Travel time including traffic, signals, jams (most important)
      distance        - Total kilometers of the route
      travel_cost     - BDT cost: fuel, CNG, tolls (Padma Bridge, etc.)

    Bangladesh-Specific Factors:
      traffic_density - Time-dependent congestion (rush hour vs midnight)
      road_condition  - Road quality: good vs broken, rural vs highway
      weather_impact  - Rain/flooding effects, monsoon route usability
      safety_risk     - Accident-prone roads, poor lighting, local disruptions

    Context-Specific Metrics:
      transport_availability - Bus routes, ride-sharing availability
      transfers       - Number of transfers for public transport
      comfort         - Road congestion, waiting time, walking distance

    Formula:
      custom_weight = length_km
                      * travel_time ^ travel_time_weight
                      * distance ^ distance_weight
                      * travel_cost ^ travel_cost_weight
                      * traffic_density ^ traffic_density_weight
                      * road_condition ^ road_condition_weight
                      * weather_impact ^ weather_impact_weight
                      * safety_risk ^ safety_risk_weight
                      * transport_availability ^ transport_availability_weight
                      * transfers ^ transfers_weight
                      * comfort ^ comfort_weight
    """
    G = G.copy()
    for u, v, key, data in G.edges(keys=True, data=True):
        lkm = data.get('length', 100) / 1000.0
        
        # Base metrics from existing data
        traffic_factor   = max(data.get('traffic_factor',   1.4), 1e-6)  # Congestion
        safety_factor    = max(data.get('safety_factor',    0.8), 1e-6)  # Safety index
        road_age_factor  = max(data.get('road_age_factor',  1.1), 1e-6)  # Road quality
        turn_complexity  = max(data.get('turn_complexity',  0.7), 1e-6)  # Turn complexity
        speed_limit      = max(data.get('speed_limit',      30), 1e-6)   # km/h
        
        # Calculate derived Bangladesh-specific metrics
        travel_time      = lkm  *  traffic_factor/ speed_limit  # hours
        distance         = lkm  # km
        travel_cost      = lkm * 7  # BDT (fuel cost ~7 BDT/km average)
        traffic_density  = traffic_factor * (2.0 if rush_hour_factor() else 1.0)
        road_condition   = road_age_factor * surface_quality_factor(data)
        weather_impact   = 0.7 + 0.3 * flood_risk_factor(data)  # +30% in flood-prone areas
        safety_risk      = 2.0 - safety_factor  # Invert: higher = more risk
        transport_avail = 1.0 if is_public_transport_corridor(data) else 2.0
        transfers        = 1.0  # Base transfers, can be modified per route
        comfort          = traffic_factor * 0.7 + turn_complexity * 0.3  # Congestion + complexity

        # Apply exponential weighting based on user preferences
        G[u][v][key]['custom_weight'] = round(
            travel_time      ** params.travel_time_weight
            * distance       ** params.distance_weight
            * travel_cost    ** params.travel_cost_weight
            * traffic_density ** params.traffic_density_weight
            * road_condition  ** params.road_condition_weight
            * weather_impact  ** params.weather_impact_weight
            * safety_risk     ** params.safety_risk_weight
            * transport_avail ** params.transport_availability_weight
            * transfers       ** params.transfers_weight
            * comfort         ** params.comfort_weight,
            6
        )
        
        # Store individual metrics for dashboard display
        G[u][v][key].update({
            'travel_time': round(travel_time, 3),
            'distance': round(distance, 3),
            'travel_cost': round(travel_cost, 2),
            'traffic_density': round(traffic_density, 3),
            'road_condition': round(road_condition, 3),
            'weather_impact': round(weather_impact, 3),
            'safety_risk': round(safety_risk, 3),
            'transport_availability': round(transport_avail, 3),
            'transfers': round(transfers, 3),
            'comfort': round(comfort, 3)
        })
        
    return G


def rush_hour_factor() -> float:
    """Simulate rush hour timing (7-9 AM, 5-7 PM)."""
    import datetime
    now = datetime.datetime.now()
    hour = now.hour
    return 2.0 if (8 <= hour <= 10) or (16 <= hour <= 20) else 1.0


def surface_quality_factor(edge_data: dict) -> float:
    """Calculate road surface quality based on road type."""
    highway_type = edge_data.get('highway', 'unclassified')
    
    # Handle case where highway_type might be a list (OSM sometimes stores multiple values)
    if isinstance(highway_type, list):
        highway_type = highway_type[0] if highway_type else 'unclassified'
    
    quality_map = {
        'motorway': 0.8,     # Excellent
        'trunk': 0.85,       # Very Good
        'primary': 0.9,      # Good
        'secondary': 1.0,     # Average
        'tertiary': 1.2,     # Fair
        'residential': 1.4,  # Poor
        'service': 1.6,      # Very Poor
        'unclassified': 1.3  # Below Average
    }
    return quality_map.get(highway_type, 1.0)


def flood_risk_factor(edge_data: dict) -> float:
    """Calculate flood risk based on road elevation and type."""
    # Simplified: lower elevation roads have higher flood risk
    elevation = edge_data.get('elevation', 10)  # meters above sea level
    highway_type = edge_data.get('highway', 'unclassified')
    
    # Handle case where highway_type might be a list
    if isinstance(highway_type, list):
        highway_type = highway_type[0] if highway_type else 'unclassified'
    
    # Dhaka average elevation ~10m, low-lying areas flood easily
    base_risk = max(0, (10 - elevation) / 10)
    
    # Underground/overpass roads have lower flood risk
    if highway_type in ['motorway', 'trunk']:
        base_risk *= 0.5
    
    return min(base_risk, 1.0)


def is_public_transport_corridor(edge_data: dict) -> bool:
    """Check if road is on major public transport corridor."""
    highway_type = edge_data.get('highway', 'unclassified')
    
    # Handle case where highway_type might be a list
    if isinstance(highway_type, list):
        highway_type = highway_type[0] if highway_type else 'unclassified'
    
    # Major roads typically have better public transport
    return highway_type in ['motorway', 'trunk', 'primary', 'secondary']


def _reverse_geocode(lat: float, lon: float, node_id: int) -> str:
    """
    Return a human-readable place name for (lat, lon) using Nominatim.
    Falls back to cached value, then to coordinate string.
    """
    if node_id in GEOCACHE:
        return GEOCACHE[node_id]
    try:
        import urllib.request, urllib.parse
        params = urllib.parse.urlencode({'lat': lat, 'lon': lon, 'format': 'json', 'zoom': 17, 'addressdetails': 1})
        url = f"https://nominatim.openstreetmap.org/reverse?{params}"
        req = urllib.request.Request(url, headers={'User-Agent': 'AI-Pathfinding-Dashboard/1.0'})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read())
        addr = data.get('address', {})
        # Build a short readable name: road/suburb/neighbourhood
        name = (addr.get('road') or addr.get('pedestrian') or
                addr.get('neighbourhood') or addr.get('suburb') or
                addr.get('city_district') or data.get('display_name', '')[:60])
        GEOCACHE[node_id] = name
        # Persist cache
        os.makedirs('cache', exist_ok=True)
        with open('cache/geocache.json', 'w') as f:
            json.dump({str(k): v for k, v in GEOCACHE.items()}, f)
        return name
    except Exception:
        fallback = f"{lat:.4f}, {lon:.4f}"
        GEOCACHE[node_id] = fallback
        return fallback


@app.post("/api/snap-node")
def snap_node(req: SnapRequest):
    """Snap a lat/lon click to the nearest OSM road node using pre-built KD-tree — O(log n)."""
    if OSM_G is None or _KDTREE is None:
        raise HTTPException(400, "OSM graph not loaded")
    _, idx = _KDTREE.query([req.lat, req.lon])
    nid = _KDTREE_IDS[idx]
    data = OSM_G.nodes[nid]
    lat, lon = data['y'], data['x']
    name = _reverse_geocode(lat, lon, nid)
    return {"id": nid, "lat": lat, "lon": lon, "name": name}


@app.post("/api/set-nodes")
async def set_nodes(req: SetNodesRequest):
    """
    Rebuild the search graph from a new set of chosen node IDs,
    run all algorithms, and return results + graph data in one shot.
    """
    global GRAPH, NODES, START, GOAL

    if OSM_G is None:
        raise HTTPException(400, "OSM graph not loaded")
    if len(req.node_ids) < 2:
        raise HTTPException(400, "Need at least 2 nodes")

    # Build chosen_nodes list with labels and geocoded names
    chosen = []
    for i, nid in enumerate(req.node_ids):
        if nid not in OSM_G.nodes:
            raise HTTPException(400, f"Node {nid} not in OSM graph")
        d = OSM_G.nodes[nid]
        label = 'START' if i == 0 else ('GOAL' if i == len(req.node_ids) - 1 else f'N{i}')
        name = _reverse_geocode(d['y'], d['x'], nid)
        chosen.append({'id': nid, 'lat': d['y'], 'lon': d['x'], 'label': label, 'name': name})

    # Cache subgraph by START+GOAL only — intermediate nodes don't affect the subgraph
    cache_key = (req.node_ids[0], req.node_ids[-1])
    if cache_key not in _GRAPH_CACHE:
        GRAPH = await run_in_threadpool(build_search_graph, OSM_G, chosen, _SEED)
        _GRAPH_CACHE[cache_key] = GRAPH
    else:
        GRAPH = _GRAPH_CACHE[cache_key]

    NODES = chosen
    START = chosen[0]['id']
    GOAL  = chosen[-1]['id']

    # Intermediate nodes enrich the subgraph with more road options,
    # but are NOT forced waypoints — algorithms find the best path freely from START to GOAL.
    G = _apply_weights(GRAPH, req.params)
    records = await run_in_threadpool(run_all, G, START, GOAL, None)

    # Build graph data response
    pos = {nid: d for nid, d in GRAPH.nodes(data=True)}
    nodes_data = [
        {"id": nid, "lat": d.get('y'), "lon": d.get('x'),
         "label": d.get('label', ''), "name": GEOCACHE.get(nid, f"{d.get('y'):.4f},{d.get('x'):.4f}")}
        for nid, d in GRAPH.nodes(data=True)
    ]

    return {
        "records": records,
        "nodes": nodes_data,
        "start": START,
        "goal": GOAL,
        "chosen_nodes": NODES,
    }


@app.post("/api/run")
async def run_algorithms(params: WeightParams):
    """Re-run all algorithms with adjusted weights on the current graph."""
    if GRAPH is None:
        raise HTTPException(400, "No graph loaded. Place nodes first.")
    G = _apply_weights(GRAPH, params)
    records = await run_in_threadpool(run_all, G, START, GOAL, None)
    return {"records": records, "params": params.model_dump()}


@app.get("/api/graph-data")
def get_graph_data():
    """
    Return graph structure, nodes, edges, and geocoded names.
    Returns empty state if no graph is loaded yet (no nodes placed).
    """
    if GRAPH is None:
        return {
            "nodes": [], "edges": [],
            "start": None, "goal": None, "chosen_nodes": []
        }
    
    nodes_data = []
    for nid, data in GRAPH.nodes(data=True):
        nodes_data.append({
            "id": nid,
            "lat": data.get('y'),
            "lon": data.get('x'),
            "label": data.get('label', ''),
            "name": GEOCACHE.get(nid, f"{data.get('y'):.4f},{data.get('x'):.4f}")
        })
    
    edges_data = []
    for u, v, key, data in GRAPH.edges(keys=True, data=True):
        edges_data.append({
            "source": u,
            "target": v,
            "length": data.get('length'),
            "traffic": data.get('traffic_factor'),
            "safety": data.get('safety_factor'),
            "pothole": data.get('pothole_factor'),
            "weight": data.get('custom_weight'),
            # Bangladesh-specific detailed metrics
            "travel_time": data.get('travel_time'),
            "distance": data.get('distance'),
            "travel_cost": data.get('travel_cost'),
            "traffic_density": data.get('traffic_density'),
            "road_condition": data.get('road_condition'),
            "weather_impact": data.get('weather_impact'),
            "safety_risk": data.get('safety_risk'),
            "transport_availability": data.get('transport_availability'),
            "transfers": data.get('transfers'),
            "comfort": data.get('comfort')
        })
    
    return {
        "nodes": nodes_data,
        "edges": edges_data,
        "start": START,
        "goal": GOAL,
        "chosen_nodes": NODES
    }


@app.get("/api/metrics-summary")
def get_metrics_summary():
    """
    Return comprehensive Bangladesh-specific metrics summary for all algorithms.
    Includes travel time, cost, safety, weather impact, and other factors.
    """
    if GRAPH is None:
        return {"error": "No graph loaded. Place nodes first."}
    
    # Run algorithms with current weights to get latest results
    from comparison import run_all
    records = run_all(GRAPH, START, GOAL, None)
    
    # Build detailed metrics summary
    from metrics import build_metrics_summary
    summary = build_metrics_summary(records)
    
    return summary


@app.get("/api/weight-sliders")
def get_weight_sliders():
    """
    Return default weight slider configurations for Bangladesh-specific metrics.
    """
    return {
        "primary_metrics": {
            "travel_time": {
                "name": "Travel Time (Most Important)",
                "description": "Includes traffic congestion, signals, intersections, jams",
                "default": 1.5,
                "min": 0.0,
                "max": 3.0,
                "step": 0.1,
                "unit": "priority"
            },
            "distance": {
                "name": "Distance",
                "description": "Total kilometers of the route",
                "default": 1.0,
                "min": 0.0,
                "max": 3.0,
                "step": 0.1,
                "unit": "priority"
            },
            "travel_cost": {
                "name": "Travel Cost (BDT)",
                "description": "Fuel cost, CNG fare, tolls (Padma Bridge, etc.)",
                "default": 1.2,
                "min": 0.0,
                "max": 3.0,
                "step": 0.1,
                "unit": "priority"
            }
        },
        "bangladesh_factors": {
            "traffic_density": {
                "name": "Traffic Density / Jam Probability",
                "description": "Time-dependent congestion (rush hour vs midnight)",
                "default": 1.3,
                "min": 0.0,
                "max": 3.0,
                "step": 0.1,
                "unit": "priority"
            },
            "road_condition": {
                "name": "Road Condition Quality",
                "description": "Good road vs broken road, rural vs highway",
                "default": 1.1,
                "min": 0.0,
                "max": 3.0,
                "step": 0.1,
                "unit": "priority"
            },
            "weather_impact": {
                "name": "Weather Impact",
                "description": "Rain/flooding effects, monsoon route usability",
                "default": 1.0,
                "min": 0.0,
                "max": 3.0,
                "step": 0.1,
                "unit": "priority"
            },
            "safety_risk": {
                "name": "Safety / Risk",
                "description": "Accident-prone roads, poor lighting, local disruptions",
                "default": 1.2,
                "min": 0.0,
                "max": 3.0,
                "step": 0.1,
                "unit": "priority"
            }
        },
        "context_metrics": {
            "transport_availability": {
                "name": "Transport Availability",
                "description": "Bus routes, ride-sharing availability",
                "default": 1.0,
                "min": 0.0,
                "max": 3.0,
                "step": 0.1,
                "unit": "priority"
            },
            "transfers": {
                "name": "Number of Transfers",
                "description": "For public transport routes",
                "default": 0.8,
                "min": 0.0,
                "max": 3.0,
                "step": 0.1,
                "unit": "priority"
            },
            "comfort": {
                "name": "Comfort / Convenience",
                "description": "Road congestion, waiting time, walking distance",
                "default": 0.5,
                "min": 0.0,
                "max": 3.0,
                "step": 0.1,
                "unit": "priority"
            }
        }
    }


class SaveSnapshotRequest(BaseModel):
    image: str        # base64 data-URL: "data:image/png;base64,..."
    label: str = ''   # e.g. 'all', 'A*', 'BFS' — used in filename


@app.post("/api/save-map-snapshot")
async def save_map_snapshot(req: SaveSnapshotRequest):
    """Receive a base64 PNG data-URL from the frontend and save it to disk."""
    import base64, re
    match = re.match(r'data:image/\w+;base64,(.*)', req.image, re.DOTALL)
    if not match:
        raise HTTPException(400, "Invalid image data")
    img_bytes = base64.b64decode(match.group(1))
    # Sanitise label for use in filename
    safe_label = re.sub(r'[^\w\-]', '_', req.label) if req.label else 'snapshot'
    out_path = f"output_map_{safe_label}.png"
    with open(out_path, "wb") as f:
        f.write(img_bytes)
    return {"file": out_path, "message": f"Snapshot saved as {out_path}"}


@app.post("/api/generate-graphs")
async def generate_graphs(params: WeightParams):
    """
    Generate matplotlib visualisations:
      - output_path_map.png           : all algorithm paths on OSM basemap
      - output_complexity.png         : nodes expanded, time, memory, theory table
      - output_expansion_<algo>.png   : per-algorithm expansion order map with POIs
    """
    if GRAPH is None or START is None or GOAL is None:
        raise HTTPException(400, "No graph loaded. Place nodes first.")

    G = _apply_weights(GRAPH, params)
    records = await run_in_threadpool(run_all, G, START, GOAL, None)

    path_map_file = await run_in_threadpool(
        generate_path_map, OSM_G, GRAPH, G, records, START, GOAL, NODES
    )
    complexity_file = await run_in_threadpool(
        generate_complexity_graphs, G, START, GOAL, records
    )
    expansion_files = await run_in_threadpool(
        generate_expansion_maps, OSM_G, GRAPH, records, START, GOAL, '.'
    )
    comparison_file = await run_in_threadpool(
        generate_comparison_graph, G, START, GOAL, records
    )

    return {
        "path_map":        path_map_file,
        "complexity":      complexity_file,
        "expansion_maps":  expansion_files,
        "comparison":      comparison_file,
        "message":         f"Saved {3 + len(expansion_files)} graphs.",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Bangladesh AI Pathfinding System - Comprehensive Documentation

## 📋 **Table of Contents**

1. [System Overview](#system-overview)
2. [Core Components](#core-components)
3. [Cost Function](#cost-function)
4. [Heuristic Function](#heuristic-function)
5. [Evaluation Functions](#evaluation-functions)
6. [Algorithm Implementations](#algorithm-implementations)
7. [Bangladesh-Specific Metrics](#bangladesh-specific-metrics)
8. [API Endpoints](#api-endpoints)
9. [Frontend Architecture](#frontend-architecture)
10. [Data Flow](#data-flow)

---

## 🎯 **System Overview**

The Bangladesh AI Pathfinding System is a comprehensive route optimization platform that combines traditional pathfinding algorithms with Bangladesh-specific real-world factors. It provides both algorithmic comparison and practical route planning for Dhaka's unique transportation challenges.

### **Key Features:**
- **6 Core Pathfinding Algorithms** with Bangladesh-specific cost weighting
- **Real-time Dynamic Factors** (rush hour, weather, flooding risk)
- **Interactive Web Dashboard** with algorithm comparison
- **Bangladesh-Specific Metrics** (traffic density, road conditions, safety risks)
- **Exponential Weight System** for fine-tuned route preferences

---

## 🔧 **Core Components**

### **1. API Layer (`api.py`)**
**Purpose**: FastAPI backend serving algorithm execution and data management

**Key Responsibilities:**
- Algorithm orchestration and execution
- Bangladesh metrics calculation and weighting
- Real-time graph processing with custom weights
- HTTP endpoints for frontend communication
- State management for nodes, paths, and results

**Critical Functions:**
```python
# Main algorithm execution endpoint
@app.post("/api/run")
async def run_algorithms(params: WeightParams)

# Graph data with Bangladesh metrics
@app.get("/api/graph-data") 
def get_graph_data()

# Weight configuration for Bangladesh metrics
@app.get("/api/weight-sliders")
def get_weight_sliders()

# Comprehensive metrics summary
@app.get("/api/metrics-summary")
def get_metrics_summary()
```

### **2. Algorithm Engine (`comparison.py`)**
**Purpose**: Algorithm execution coordination and result comparison

**Key Functions:**
```python
def run_all(G, start, goal, waypoints=None):
    """Execute all algorithms and compare results"""
    
def build_comparison_record(name, result, G, weight='custom_weight'):
    """Build standardized result records"""
```

### **3. Graph Processing (`map_loader.py`)**
**Purpose**: OSM data loading and Bangladesh-specific metric assignment

**Key Functions:**
```python
def assign_metrics(G, seed=42):
    """Assign Bangladesh-specific road metrics to OSM edges"""

def load_graph(center, dist=8000):
    """Load OSM road network for Dhaka region"""
```

### **4. Individual Algorithms (`algorithms/`)**
**Purpose**: Specific search algorithm implementations

**Available Algorithms:**
- BFS (Breadth-First Search)
- DFS (Depth-First Search)
- IDS (Iterative Deepening Search)
- UCS (Uniform Cost Search)
- A* (A-star Search)
- Greedy (Greedy Best-First Search)
- Best-First (Pure heuristic search)
- DLS (Depth-Limited Search) - Backend only
- Bidirectional A* - Backend only

---

## 💰 **Cost Function**

### **Bangladesh-Specific Cost Formula**

The system uses a comprehensive exponential weighting system that combines multiple real-world factors:

```python
custom_weight = (
    travel_time ^ travel_time_weight *
    distance ^ distance_weight *
    travel_cost ^ travel_cost_weight *
    traffic_density ^ traffic_density_weight *
    road_condition ^ road_condition_weight *
    weather_impact ^ weather_impact_weight *
    safety_risk ^ safety_risk_weight *
    transport_availability ^ transport_availability_weight *
    transfers ^ transfers_weight *
    comfort ^ comfort_weight
)
```

### **Metric Components**

#### **Primary Metrics**
1. **Travel Time** (`travel_time`)
   - **Calculation**: `distance_km / (speed_limit/60) * traffic_factor`
   - **Units**: Hours
   - **Bangladesh Context**: Includes Dhaka traffic congestion, signal delays
   - **Default Weight**: 1.5

2. **Distance** (`distance`) 
   - **Calculation**: `length_km` from OSM data
   - **Units**: Kilometers
   - **Bangladesh Context**: Actual road distance
   - **Default Weight**: 1.0

3. **Travel Cost** (`travel_cost`)
   - **Calculation**: `distance_km * 15` BDT/km average
   - **Units**: Bangladeshi Taka (BDT)
   - **Bangladesh Context**: Fuel costs, CNG fares, Padma Bridge tolls
   - **Default Weight**: 1.2

#### **Bangladesh-Specific Factors**

4. **Traffic Density** (`traffic_density`)
   - **Calculation**: `traffic_factor * rush_hour_factor()`
   - **Dynamic Factor**: Rush hour detection (7-9 AM, 5-7 PM)
   - **Bangladesh Context**: Dhaka's world-class traffic congestion
   - **Default Weight**: 1.3

5. **Road Condition** (`road_condition`)
   - **Calculation**: `road_age_factor * surface_quality_factor(edge_data)`
   - **Surface Mapping**: Highway type to quality factor
   - **Bangladesh Context**: Variable road quality in different areas
   - **Default Weight**: 1.1

6. **Weather Impact** (`weather_impact`)
   - **Calculation**: `1.0 + 0.5 * flood_risk_factor(edge_data)`
   - **Flood Risk**: Based on elevation and road type
   - **Bangladesh Context**: Monsoon flooding impact
   - **Default Weight**: 1.0

7. **Safety Risk** (`safety_risk`)
   - **Calculation**: `2.0 - safety_factor` (inverted for risk)
   - **Bangladesh Context**: Accident-prone areas, poor lighting
   - **Default Weight**: 1.2

#### **Context-Specific Metrics**

8. **Transport Availability** (`transport_availability`)
   - **Calculation**: `1.0` on major corridors, `2.0` otherwise
   - **Corridor Detection**: Major road identification
   - **Bangladesh Context**: Public transport accessibility
   - **Default Weight**: 1.0

9. **Transfers** (`transfers`)
   - **Calculation**: Base transfer count (modifiable per route)
   - **Bangladesh Context**: Public transport connection changes
   - **Default Weight**: 0.8

10. **Comfort** (`comfort`)
   - **Calculation**: `traffic_factor * 0.7 + turn_complexity * 0.3`
   - **Bangladesh Context**: Congestion and intersection complexity
   - **Default Weight**: 0.5

### **Helper Functions**

```python
def rush_hour_factor():
    """Returns 2.0 during rush hours, 1.0 otherwise"""
    
def surface_quality_factor(edge_data):
    """Maps highway type to surface quality factor"""
    
def flood_risk_factor(edge_data):
    """Calculates flood risk based on elevation and road type"""
    
def is_public_transport_corridor(edge_data):
    """Identifies major public transport routes"""
```

---

## 🧭 **Heuristic Function**

### **Haversine Distance Heuristic**

**File**: `heuristic.py`

**Purpose**: Provides admissible heuristic estimates for informed search algorithms

**Key Function**:
```python
def haversine(G, node_a, node_b):
    """
    Calculate great-circle distance between two geographic coordinates.
    Returns lower bound on true path cost, ensuring A* optimality.
    """
```

**Bangladesh-Specific Enhancements:**
```python
# Conservative minimum cost calculation for Bangladesh context
min_cost_per_km = max(
    _MIN_COST_PER_KM,  # Base minimum (0.45)
    calculated_minimum  # Based on best-case Bangladesh factors
)

# Factors considered:
- Minimum travel time: distance at 80 km/h (motorway speed)
- Minimum cost: 10 BDT/km (optimal fuel rate)
- Minimum risk: Excellent road conditions
- Conservative exponents for all metrics
```

**Admissibility Guarantee**: The heuristic never overestimates actual path cost, maintaining A* optimality.

---

## 📊 **Evaluation Functions**

### **Path Evaluation Components**

**File**: `evaluation.py`

#### **1. g(n) - Path Cost Function**
```python
def compute_g(path, G, weight='custom_weight'):
    """
    Calculate cumulative cost from start to current node.
    Sums Bangladesh-weighted custom_weight along path edges.
    """
```

#### **2. h(n) - Heuristic Function**
```python
def compute_h(G, node, goal):
    """
    Calculate haversine distance heuristic estimate.
    Returns straight-line distance to goal.
    """
```

#### **3. f(n) - Total Evaluation Function**
```python
def compute_f(path, G, weight, goal):
    """
    f(n) = g(n) + h(n)
    Used by A*, IDA*, and other informed algorithms.
    """
```

#### **4. Detailed Metrics Function**
```python
def compute_detailed_metrics(path, G):
    """
    Calculate all Bangladesh-specific metrics for a path.
    Returns comprehensive breakdown for route analysis.
    """
```

---

## 🤖 **Algorithm Implementations**

### **Frontend Available Algorithms (6)**

#### **1. BFS - Breadth-First Search**
- **File**: `algorithms/bfs.py`
- **Complexity**: O(b^d) - Exponential in depth, linear in branching
- **Optimality**: ✅ Guaranteed optimal for uniform edge costs
- **Bangladesh Use**: Finds shortest path regardless of traffic conditions

#### **2. DFS - Depth-First Search**
- **File**: `algorithms/dfs.py`
- **Complexity**: O(bm) - Linear in depth, exponential in branching
- **Optimality**: ❌ Not optimal, may find long paths
- **Bangladesh Use**: Deep exploration of route alternatives

#### **3. IDS - Iterative Deepening Search**
- **File**: `algorithms/ids.py`
- **Complexity**: O(b^d) - Depth-limited with iterative increase
- **Optimality**: ✅ Optimal within depth limit
- **Bangladesh Use**: Memory-efficient complete search

#### **4. UCS - Uniform Cost Search**
- **File**: `algorithms/ucs.py`
- **Complexity**: O(b^(1+C*/ε)) - Optimal with logarithmic factors
- **Optimality**: ✅ Guaranteed optimal
- **Bangladesh Use**: Considers actual weighted costs

#### **5. A* - A-Star Search**
- **File**: `algorithms/astar.py`
- **Complexity**: O(b^d) - Optimal with heuristic guidance
- **Optimality**: ✅ Guaranteed optimal with admissible heuristic
- **Bangladesh Use**: Balances cost and distance estimates

#### **6. Greedy - Greedy Best-First Search**
- **File**: `algorithms/greedy.py`
- **Complexity**: O(b^m) - Fast but not optimal
- **Optimality**: ❌ Not optimal, purely heuristic-driven
- **Bangladesh Use**: Always expands toward goal geographically

### **Backend-Only Algorithms**

#### **7. Best-First - Pure Heuristic Search**
- **File**: `algorithms/best_first.py`
- **Complexity**: O(b^m) - Similar to Greedy but different heuristic
- **Optimality**: ❌ Not optimal, ignores path costs
- **Bangladesh Use**: Geographic proximity to goal

#### **8. DLS - Depth-Limited Search**
- **File**: `algorithms/dls.py`
- **Complexity**: O(b^d) - DFS with depth cutoff
- **Optimality**: ❌ Not optimal if solution is deeper than limit
- **Bangladesh Use**: Prevents infinite loops in cyclic graphs

#### **9. Bidirectional A* - Two-Way A-Star**
- **File**: `algorithms/bidirectional_astar.py`
- **Complexity**: O(b^(d/2)) - Theoretically faster than A*
- **Optimality**: ✅ Optimal with proper meeting point detection
- **Bangladesh Use**: Simultaneous search from start and goal

---

## 🇧🇩 **Bangladesh-Specific Metrics**

### **Dynamic Real-World Factors**

#### **Time-Based Factors**
```python
def rush_hour_factor():
    """Doubles traffic weight during Dhaka rush hours"""
    # 7-9 AM and 5-7 PM: highest congestion
    # Returns 2.0 during rush, 1.0 otherwise
```

#### **Weather-Based Factors**
```python
def flood_risk_factor(edge_data):
    """
    Calculates monsoon and flood vulnerability.
    Lower elevation = higher flood risk.
    Major roads (motorway, trunk) have reduced risk.
    """
```

#### **Infrastructure Factors**
```python
def surface_quality_factor(edge_data):
    """
    Maps OSM highway types to Bangladesh road conditions:
    motorway: 0.8 (excellent)
    primary: 0.9 (good)
    residential: 1.4 (poor)
    service: 1.6 (very poor)
    """
```

#### **Transportation Factors**
```python
def is_public_transport_corridor(edge_data):
    """
    Identifies routes with:
    - Bus services
    - Ride-sharing availability  
    - CNG accessibility
    """
```

### **Cultural and Geographic Adaptations**

- **Left-Hand Traffic**: Bangladesh drives on left, affecting intersection complexity
- **Rickshaw Factors**: Informal transport affects route choices
- **Monsoon Routes**: Seasonal road closures and detours
- **Urban Density**: High population density affects all metrics
- **Bridge Tolls**: Padma Bridge and other toll roads impact costs

---

## 🌐 **API Endpoints**

### **Core Algorithm Endpoints**

#### **POST /api/run**
```python
@app.post("/api/run")
async def run_algorithms(params: WeightParams):
    """
    Execute all 6 frontend algorithms with Bangladesh weights.
    Returns: {records: AlgorithmRecord[], params: WeightParams}
    """
```

#### **POST /api/set-nodes**
```python
@app.post("/api/set-nodes")
async def set_nodes(req: SetNodesRequest):
    """
    Set start/goal nodes and run complete analysis.
    Builds search graph from OSM subgraph.
    Returns: {records, nodes, start, goal, chosen_nodes}
    """
```

#### **GET /api/graph-data**
```python
@app.get("/api/graph-data")
def get_graph_data():
    """
    Return current graph structure with all Bangladesh metrics.
    Includes: nodes, edges with detailed metric breakdowns
    """
```

### **Configuration Endpoints**

#### **GET /api/weight-sliders**
```python
@app.get("/api/weight-sliders")
def get_weight_sliders():
    """
    Return Bangladesh-specific weight configurations.
    Structure: {primary_metrics, bangladesh_factors, context_metrics}
    Each metric has: name, description, default, min, max, step
    """
```

#### **GET /api/metrics-summary**
```python
@app.get("/api/metrics-summary")
def get_metrics_summary():
    """
    Return comprehensive metrics comparison across algorithms.
    Includes: best values, algorithm rankings, detailed breakdowns
    """
```

#### **POST /api/save-map-snapshot**
```python
@app.post("/api/save-map-snapshot")
async def save_map_snapshot(req: SaveSnapshotRequest):
    """
    Save current map visualization as image.
    Supports: algorithm-specific snapshots and comparisons
    """
```

---

## 💻 **Frontend Architecture**

### **Technology Stack**
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Maps**: Leaflet + OpenStreetMap
- **Charts**: Recharts for algorithm comparison
- **Styling**: CSS with component-based architecture

### **Component Structure**

#### **1. App.tsx - Main Application**
```typescript
// Core state management
const [records, setRecords] = useState<AlgorithmRecord[]>([])
const [params, setParams] = useState<WeightParams>({
    // Bangladesh-specific defaults
    travel_time_weight: 1.5,
    traffic_density_weight: 1.3,
    safety_risk_weight: 1.2,
    // ... other metrics
})

// Algorithm color coding
const COLORS: Record<string, string> = {
    'BFS': '#1f77b4', 'DFS': '#9467bd', 'IDS': '#17becf',
    'UCS': '#2ca02c', 'A*': '#d62728', 'Greedy': '#ff7f0e'
}
```

#### **2. WeightControls.tsx - Bangladesh Metrics Interface**
```typescript
// Dynamic slider loading from API
// Grouped by category:
// - Primary Metrics (Time, Distance, Cost)
// - Bangladesh Factors (Traffic, Road, Weather, Safety)  
// - Context Metrics (Transport, Transfers, Comfort)
```

#### **3. ResultsTable.tsx - Algorithm Comparison**
```typescript
// Displays algorithm performance:
// - Path costs with Bangladesh metrics
// - Hop counts and nodes expanded
// - Optimal path identification
// - Real-time algorithm status
```

#### **4. Charts.tsx - Visual Analytics**
```typescript
// Bar charts for:
// - Path cost comparison
// - Hop count analysis  
// - Node expansion metrics
// - Bangladesh-specific factor analysis
```

#### **5. MapView.tsx - Interactive Map**
```typescript
// Leaflet integration with:
// - OSM tile layers for Dhaka
// - Algorithm path visualization
// - Node placement and snapping
// - Real-time route rendering
```

---

## 🔄 **Data Flow**

### **1. User Interaction Flow**
```
User places nodes → Snap to OSM → Build search graph → Run algorithms → Display results
     ↓                ↓              ↓              ↓              ↓
   Click →   API call →   Graph processing →   Algorithm execution →   UI update
```

### **2. Weight Adjustment Flow**
```
User adjusts slider → API call → Recalculate weights → Re-run algorithms → Update display
        ↓              ↓              ↓              ↓              ↓
   Slider change → POST /api/run → Apply new weights → Execute all algorithms → Update charts
```

### **3. Bangladesh Metrics Integration**
```
OSM Data → Road type assignment → Bangladesh factor calculation → Weighted cost → Algorithm consideration
      ↓              ↓                    ↓              ↓              ↓
   highway='primary' → surface_quality=0.9 → road_condition=1.1 → custom_weight calculation → Path selection
```

### **4. Real-Time Dynamic Updates**
```
Time check → Rush hour detection → Traffic density adjustment → Cost recalculation → Route optimization
     ↓         ↓                    ↓              ↓              ↓
   Current time → is_rush_hour() → traffic_density *= 2.0 → Update weights → New paths
```

---

## 🎯 **Key Optimizations**

### **1. Exponential Weight Balancing**
- Prevents weight explosion (previous issue: costs > 1,000,000)
- Uses reasonable weight ranges (0.5-1.5)
- Maintains algorithm performance while preserving user preferences

### **2. Caching Strategy**
- OSM graph caching for faster startup
- KD-tree for O(1) node snapping
- Algorithm result caching for repeated queries

### **3. Bangladesh-Specific Tuning**
- Rush hour timing aligned with Dhaka traffic patterns
- Flood risk modeling for monsoon conditions
- Road quality mapping for Bangladeshi infrastructure
- Transport corridor detection for public transit routing

---

## 📈 **Performance Characteristics**

### **Algorithm Complexity Summary**
| Algorithm | Time | Space | Optimal | Bangladesh Use |
|-------------|--------|---------|-----------|----------------|
| BFS | O(b^d) | O(b^d) | ✅ | Finds shortest distance path |
| DFS | O(bm) | O(bm) | ❌ | Deep exploration, ignores costs |
| IDS | O(b^d) | O(bd) | ✅ | Memory-efficient complete search |
| UCS | O(b^(1+C*/ε)) | O(b^(1+C*/ε)) | ✅ | Considers actual weighted costs |
| A* | O(b^d) | O(b^d) | ✅ | Balances cost and distance |
| Greedy | O(b^m) | O(bm) | ❌ | Fast but ignores actual costs |
| Best-First | O(b^m) | O(bm) | ❌ | Pure heuristic guidance |

### **Scalability Considerations**
- **Graph Size**: Optimized for Dhaka metropolitan area
- **Real-Time Updates**: Debounced weight changes (400ms)
- **Memory Usage**: Efficient data structures for large graphs
- **Network Latency**: Local processing minimizes API delays

---

## 🚀 **System Benefits**

### **For Bangladesh Context**
1. **Traffic-Aware Routing**: Considers Dhaka's severe congestion
2. **Weather Adaptation**: Monsoon and flood risk modeling
3. **Infrastructure Awareness**: Road quality and public transport mapping
4. **Cost Optimization**: Fuel, time, and safety factor balancing
5. **Cultural Adaptation**: Local transportation patterns and preferences

### **For Algorithm Research**
1. **Comparative Analysis**: Side-by-side algorithm performance
2. **Parameter Tuning**: Real-time weight adjustment experiments
3. **Heuristic Testing**: Bangladesh-specific heuristic improvements
4. **Complexity Validation**: Real-world performance measurement
5. **Optimization Studies**: Route quality vs. computational efficiency

---

## 📚 **Conclusion**

The Bangladesh AI Pathfinding System represents a comprehensive integration of classical pathfinding algorithms with real-world local factors. It provides both practical route planning for daily use and a research platform for algorithm development in the context of developing world transportation challenges.

**Key Innovation**: The exponential weighting system allows fine-tuned route preferences that reflect actual Bangladeshi transportation realities while maintaining algorithmic optimality guarantees.

**Impact**: Enables data-driven transportation decisions for one of the world's most complex urban environments.

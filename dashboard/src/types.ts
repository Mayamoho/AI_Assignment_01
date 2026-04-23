export interface AlgorithmRecord {
  algorithm: string
  path_cost: number | null
  hop_count: number
  nodes_expanded: number
  path: number[]
  is_optimal: boolean
  
  // Bangladesh-specific detailed metrics
  travel_time_hours?: number | null
  distance_km?: number | null
  travel_cost_bdt?: number | null
  traffic_density?: number | null
  road_condition?: number | null
  weather_impact?: number | null
  safety_risk?: number | null
  transport_availability?: number | null
  transfers?: number | null
  comfort?: number | null
}

export interface NodeData {
  id: number
  lat: number
  lon: number
  label: string
  name: string
}

export interface EdgeData {
  source: number
  target: number
  length: number
  traffic: number
  safety: number
  pothole: number
  weight: number
  
  // Bangladesh-specific detailed metrics
  travel_time?: number
  distance?: number
  travel_cost?: number
  traffic_density?: number
  road_condition?: number
  weather_impact?: number
  safety_risk?: number
  transport_availability?: number
  transfers?: number
  comfort?: number
}

export interface GraphData {
  nodes: NodeData[]
  edges: EdgeData[]
  start: number
  goal: number
  chosen_nodes: NodeData[]
}

export interface WeightParams {
  // Primary Metrics
  travel_time_weight:    number   // Travel Time (Most Important)
  distance_weight:       number   // Distance in km
  travel_cost_weight:    number   // Travel Cost (BDT) - fuel, tolls
  
  // Bangladesh-Specific Factors
  traffic_density_weight: number   // Traffic Density / Jam Probability
  road_condition_weight:  number   // Road Condition Quality
  weather_impact_weight:  number   // Weather Impact (rain/flooding)
  safety_risk_weight:     number   // Safety / Risk (accidents, lighting)
  
  // Context-Specific Metrics
  transport_availability_weight: number   // Transport Availability
  transfers_weight:       number   // Number of Transfers (public transport)
  comfort_weight:          number   // Comfort / Convenience
  
  // Legacy weights (for backward compatibility)
  traffic_weight:  number   // Legacy Traffic Intensity exponent
  safety_weight:   number   // Legacy Safety Index exponent
  road_age_weight: number   // Legacy Road Quality exponent
  turn_weight:     number   // Legacy Turn Complexity exponent
}

export interface WeightSliderConfig {
  name: string
  description: string
  default: number
  min: number
  max: number
  step: number
  unit: string
}

export interface WeightSlidersResponse {
  primary_metrics: {
    travel_time: WeightSliderConfig
    distance: WeightSliderConfig
    travel_cost: WeightSliderConfig
  }
  bangladesh_factors: {
    traffic_density: WeightSliderConfig
    road_condition: WeightSliderConfig
    weather_impact: WeightSliderConfig
    safety_risk: WeightSliderConfig
  }
  context_metrics: {
    transport_availability: WeightSliderConfig
    transfers: WeightSliderConfig
    comfort: WeightSliderConfig
  }
}

export interface MetricsSummary {
  algorithms: string[]
  path_costs: number[]
  hop_counts: number[]
  nodes_expanded: number[]
  
  // Bangladesh-specific metrics
  travel_times: number[]
  distances: number[]
  travel_costs: number[]
  traffic_densities: number[]
  road_conditions: number[]
  weather_impacts: number[]
  safety_risks: number[]
  transport_availabilities: number[]
  transfers: number[]
  comforts: number[]
  
  best: {
    min_cost: number
    min_time: number
    min_distance: number
    min_cost_bdt: number
    min_traffic: number
    best_road_condition: number
    min_weather_impact: number
    min_safety_risk: number
    max_transport_avail: number
    min_transfers: number
    max_comfort: number
  }
}

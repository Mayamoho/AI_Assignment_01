import type { WeightParams, WeightSlidersResponse } from '../types'
import { useState, useEffect } from 'react'

interface Props {
  params: WeightParams
  onChange: (p: WeightParams) => void
  loading: boolean
}

export default function WeightControls({ params, onChange, loading }: Props) {
  const [sliderConfig, setSliderConfig] = useState<WeightSlidersResponse | null>(null)

  useEffect(() => {
    fetch('http://localhost:8000/api/weight-sliders')
      .then(res => res.json())
      .then(config => setSliderConfig(config))
      .catch(console.error)
  }, [])

  if (!sliderConfig) {
    return <div style={{ padding: '12px 16px', color: '#666' }}>Loading weight configurations...</div>
  }

  const renderSliderGroup = (title: string, sliders: any[]) => (
    <div style={{ marginBottom: 24 }}>
      <div style={{ 
        color: '#aaa', 
        fontSize: 11, 
        marginBottom: 8, 
        textTransform: 'uppercase', 
        letterSpacing: 1,
        fontWeight: 600
      }}>
        {title}
      </div>
      {sliders.map(([key, config]: [string, any]) => (
        <div key={key} style={{ marginBottom: 16 }}>
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center',
            marginBottom: 6 
          }}>
            <div>
              <div style={{ color: '#ccc', fontSize: 12, marginBottom: 2 }}>
                {config.name}
              </div>
              <div style={{ color: '#888', fontSize: 9, fontStyle: 'italic' }}>
                {config.description}
              </div>
            </div>
            <span style={{ 
              color: getSliderColor(key), 
              fontSize: 12, 
              fontWeight: 700,
              backgroundColor: 'rgba(255,255,255,0.1)',
              padding: '2px 6px',
              borderRadius: 4
            }}>
              {params[key as keyof WeightParams]?.toFixed(1)}×
            </span>
          </div>
          <input
            type="range" 
            min={config.min} 
            max={config.max} 
            step={config.step}
            value={params[key as keyof WeightParams] || config.default}
            disabled={loading}
            onChange={e => onChange({ ...params, [key]: parseFloat(e.target.value) })}
            style={{ 
              width: '100%', 
              accentColor: getSliderColor(key),
              height: '6px'
            }}
          />
        </div>
      ))}
    </div>
  )

  const getSliderColor = (key: string): string => {
    const colors: Record<string, string> = {
      travel_time_weight: '#e74c3c',
      distance_weight: '#3498db',
      travel_cost_weight: '#f39c12',
      traffic_density_weight: '#e67e22',
      road_condition_weight: '#9b59b6',
      weather_impact_weight: '#1abc9c',
      safety_risk_weight: '#e74c3c',
      transport_availability_weight: '#27ae60',
      transfers_weight: '#f39c12',
      comfort_weight: '#16a085',
      traffic_weight: '#95a5a6',
      safety_weight: '#27ae60',
      road_age_weight: '#9b59b6',
      turn_weight: '#1abc9c'
    }
    return colors[key] || '#666'
  }

  return (
    <div style={{ padding: '12px 16px', background: '#1e2a38', borderRadius: 8 }}>
      <div style={{ 
        color: '#aaa', 
        fontSize: 11, 
        marginBottom: 4, 
        textTransform: 'uppercase', 
        letterSpacing: 1,
        fontWeight: 600
      }}>
        🇧🇩 Bangladesh Pathfinding Metrics
      </div>
      
      <div style={{ 
        color: '#555', 
        fontSize: 10, 
        marginBottom: 16,
        padding: '8px',
        background: 'rgba(255,255,255,0.05)',
        borderRadius: 4
      }}>
        <strong>Cost Formula:</strong> Travel Time^w1 × Distance^w2 × Cost^w3 × Traffic^w4 × Road^w5 × Weather^w6 × Safety^w7 × Transport^w8 × Transfers^w9 × Comfort^w10
      </div>

      {renderSliderGroup('🎯 Primary Metrics', [
        ['travel_time_weight', sliderConfig.primary_metrics.travel_time],
        ['distance_weight', sliderConfig.primary_metrics.distance],
        ['travel_cost_weight', sliderConfig.primary_metrics.travel_cost]
      ])}

      {renderSliderGroup('🌧 Bangladesh-Specific Factors', [
        ['traffic_density_weight', sliderConfig.bangladesh_factors.traffic_density],
        ['road_condition_weight', sliderConfig.bangladesh_factors.road_condition],
        ['weather_impact_weight', sliderConfig.bangladesh_factors.weather_impact],
        ['safety_risk_weight', sliderConfig.bangladesh_factors.safety_risk]
      ])}

      {renderSliderGroup('🚗 Context-Specific Metrics', [
        ['transport_availability_weight', sliderConfig.context_metrics.transport_availability],
        ['transfers_weight', sliderConfig.context_metrics.transfers],
        ['comfort_weight', sliderConfig.context_metrics.comfort]
      ])}

      <div style={{ marginTop: 20, padding: '8px', background: 'rgba(52,152,219,0.1)', borderRadius: 4 }}>
        <div style={{ color: '#888', fontSize: 9, marginBottom: 4 }}>
          <strong>Legacy Weights (for compatibility)</strong>
        </div>
        {['traffic_weight', 'safety_weight', 'road_age_weight', 'turn_weight'].map(key => (
          <div key={key} style={{ marginBottom: 8 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
              <span style={{ color: '#999', fontSize: 11 }}>{key.replace('_weight', '')}</span>
              <span style={{ color: '#666', fontSize: 11, fontWeight: 700 }}>
                {params[key as keyof WeightParams]?.toFixed(1)}×
              </span>
            </div>
            <input
              type="range" min={0.1} max={3} step={0.1}
              value={params[key as keyof WeightParams]}
              disabled={loading}
              onChange={e => onChange({ ...params, [key]: parseFloat(e.target.value) })}
              style={{ width: '100%', accentColor: '#666', height: '4px' }}
            />
          </div>
        ))}
      </div>

      {loading && (
        <div style={{ 
          color: '#3498db', 
          fontSize: 11, 
          textAlign: 'center', 
          marginTop: 16,
          padding: '8px',
          background: 'rgba(52,152,219,0.1)',
          borderRadius: 4
        }}>
          🔄 Running algorithms with new weights...
        </div>
      )}
    </div>
  )
}

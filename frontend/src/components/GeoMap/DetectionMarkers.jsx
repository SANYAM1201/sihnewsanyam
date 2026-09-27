import React from 'react';
import { CircleMarker, Popup } from 'react-leaflet';

export default function DetectionMarkers({ detections = [], onSelect }) {
  const getRiskColor = (risk) => {
    const r = (risk || '').toLowerCase();
    if (r === 'critical' || r === 'high') return '#ef4444';
    if (r === 'medium') return '#f59e0b';
    return '#10b981';
  };

  return (
    <>
      {detections.map((det) => {
        const lat = det.lat ?? det.latitude;
        const lng = det.lng ?? det.longitude;
        if (lat == null || lng == null) return null;

        const color = getRiskColor(det.risk_level || det.riskLevel);

        return (
          <CircleMarker
            key={det.id || det.detection_id || `${lat}-${lng}`}
            center={[lat, lng]}
            radius={8}
            pathOptions={{
              color: '#ffffff',
              fillColor: color,
              fillOpacity: 0.95,
              weight: 2,
            }}
            eventHandlers={{
              click: () => onSelect && onSelect(det),
            }}
          >
            <Popup>
              <div style={{ padding: '4px', fontSize: '12px', minWidth: '160px' }}>
                <div style={{ fontWeight: 700, fontSize: '13px', marginBottom: '4px' }}>
                  {det.class_label || det.class || 'Anomaly'}
                </div>
                <div>Confidence: {Math.round((det.confidence || 0) * 100)}%</div>
                <div>Risk: <span style={{ color, fontWeight: 700 }}>{det.risk_level || 'NORMAL'}</span></div>
                {det.sadh_height_m && (
                  <div>SADH Height: <strong>{Number(det.sadh_height_m).toFixed(2)}m</strong></div>
                )}
                <div style={{ fontSize: '10px', color: '#666', marginTop: '6px' }}>
                  {Number(lat).toFixed(5)}°N, {Number(lng).toFixed(5)}°E
                </div>
                {onSelect && (
                  <button
                    onClick={() => onSelect(det)}
                    style={{
                      marginTop: '8px',
                      width: '100%',
                      padding: '4px 8px',
                      background: '#2e3700',
                      color: '#fff',
                      borderRadius: '4px',
                      fontSize: '11px',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    Inspect Physics (SADH)
                  </button>
                )}
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </>
  );
}

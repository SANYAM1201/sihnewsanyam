import React from 'react';
import RiskBadge from '../common/RiskBadge';

export default function DetectionCard({ detection, onInspect }) {
  if (!detection) return null;

  const label = (detection.class_label || detection.label || 'Debris').replace('_', ' ');
  const confidence = Math.round((detection.confidence || 0) * 100);
  const lat = detection.latitude ?? detection.lat;
  const lng = detection.longitude ?? detection.lng;
  const risk = detection.risk_level || detection.riskLevel || 'medium';
  const heightM = detection.sadh_height_m || detection.height_m;

  return (
    <div
      style={{
        backgroundColor: 'var(--gesso-surface, #e7e5e7)',
        borderRadius: '10px',
        padding: '14px',
        border: '1px solid var(--gesso-divider, rgba(0,0,0,0.06))',
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
        transition: 'transform 0.15s ease',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h4 style={{ margin: 0, textTransform: 'capitalize', fontSize: '15px', fontWeight: 700 }}>
          {label}
        </h4>
        <RiskBadge risk={risk} size="small" />
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--gesso-fg-muted)' }}>
        <span>Confidence: <strong style={{ color: 'var(--gesso-fg)' }}>{confidence}%</strong></span>
        {heightM && (
          <span>Height: <strong style={{ color: 'var(--gesso-fg)' }}>{Number(heightM).toFixed(2)}m</strong></span>
        )}
      </div>

      {lat != null && lng != null && (
        <div style={{ fontSize: '11px', fontFamily: 'monospace', color: 'var(--gesso-fg-muted)' }}>
          📍 {Number(lat).toFixed(5)}°N, {Number(lng).toFixed(5)}°E
        </div>
      )}

      {onInspect && (
        <button
          onClick={() => onInspect(detection)}
          style={{
            marginTop: '4px',
            padding: '6px 12px',
            backgroundColor: 'var(--gesso-primary, #2e3700)',
            color: '#ffffff',
            borderRadius: '6px',
            fontSize: '12px',
            fontWeight: 600,
            cursor: 'pointer',
            textAlign: 'center',
          }}
        >
          Inspect Physics (SADH)
        </button>
      )}
    </div>
  );
}

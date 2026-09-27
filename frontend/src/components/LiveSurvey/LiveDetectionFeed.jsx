import React from 'react';
import RiskBadge from '../common/RiskBadge';

export default function LiveDetectionFeed({ detections = [], onInspect }) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        maxHeight: '400px',
        overflowY: 'auto',
        paddingRight: '4px',
      }}
    >
      {detections.length === 0 ? (
        <div
          style={{
            padding: '24px',
            textAlign: 'center',
            color: 'var(--gesso-fg-muted)',
            fontSize: '13px',
            background: 'var(--gesso-surface, #e7e5e7)',
            borderRadius: '8px',
          }}
        >
          No real-time targets detected in current swath segment. Awaiting acoustic echoes...
        </div>
      ) : (
        detections.map((d, idx) => {
          const lat = d.latitude ?? d.lat;
          const lng = d.longitude ?? d.lng;
          const height = d.sadh_height_m || d.height_m;
          return (
            <div
              key={d.id || idx}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 14px',
                background: 'var(--gesso-surface, #e7e5e7)',
                borderRadius: '8px',
                border: '1px solid var(--gesso-divider, rgba(0,0,0,0.06))',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '16px' }}>🎯</span>
                <div>
                  <div style={{ fontWeight: 700, fontSize: '13px', textTransform: 'capitalize' }}>
                    {d.class_label || d.label || 'Debris Target'}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--gesso-fg-muted)' }}>
                    Confidence: <strong>{Math.round((d.confidence || 0) * 100)}%</strong>
                    {height && ` · SADH: ${Number(height).toFixed(2)}m`}
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <RiskBadge risk={d.risk_level || d.riskLevel || 'medium'} size="small" />
                {onInspect && (
                  <button
                    onClick={() => onInspect(d)}
                    style={{
                      padding: '4px 8px',
                      background: 'var(--gesso-primary, #2e3700)',
                      color: '#ffffff',
                      borderRadius: '4px',
                      fontSize: '11px',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    View
                  </button>
                )}
              </div>
            </div>
          );
        })
      )}
    </div>
  );
}

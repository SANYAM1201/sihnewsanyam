import React from 'react';

export default function SystemStatusBar({
  fps = 62.4,
  latencyMs = 12.8,
  modelName = 'WERB-YOLOv8s + D-GRM',
  status = 'ONLINE',
}) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '8px 16px',
        backgroundColor: 'var(--gesso-surface, #e7e5e7)',
        borderBottom: '1px solid var(--gesso-divider, rgba(0,0,0,0.06))',
        fontSize: '12px',
        fontFamily: 'var(--gesso-font-mono, monospace)',
        color: 'var(--gesso-fg-muted, #5b595f)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: '#16a34a',
              display: 'inline-block',
            }}
          />
          <span style={{ fontWeight: 600, color: 'var(--gesso-fg)' }}>SYSTEM {status}</span>
        </div>
        <div>
          EDGE ENGINE: <strong style={{ color: 'var(--gesso-fg)' }}>{modelName}</strong>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        <div>
          INFERENCE: <span style={{ color: '#166534', fontWeight: 700 }}>{fps} FPS</span>
        </div>
        <div>
          DSP LATENCY: <span style={{ color: 'var(--gesso-fg)', fontWeight: 700 }}>{latencyMs} ms</span>
        </div>
        <div>
          GEODESY: <span style={{ color: 'var(--gesso-fg)', fontWeight: 700 }}>WGS84 ELLIPSOID</span>
        </div>
      </div>
    </div>
  );
}

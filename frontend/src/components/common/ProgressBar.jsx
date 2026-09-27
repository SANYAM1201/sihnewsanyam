import React from 'react';

export default function ProgressBar({ progress = 0, label = '', status = '' }) {
  const clamped = Math.min(100, Math.max(0, Math.round(progress)));

  return (
    <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '6px' }}>
      {(label || status) && (
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--gesso-fg-muted)' }}>
          <span>{label}</span>
          <span style={{ fontWeight: 600, color: 'var(--gesso-fg)' }}>{status || `${clamped}%`}</span>
        </div>
      )}
      <div
        style={{
          width: '100%',
          height: '8px',
          background: 'var(--gesso-surface-elevated, #dedcde)',
          borderRadius: '4px',
          overflow: 'hidden',
          position: 'relative',
        }}
      >
        <div
          style={{
            height: '100%',
            width: `${clamped}%`,
            background: 'var(--gesso-primary, #2e3700)',
            borderRadius: '4px',
            transition: 'width 0.3s ease-in-out',
          }}
        />
      </div>
    </div>
  );
}

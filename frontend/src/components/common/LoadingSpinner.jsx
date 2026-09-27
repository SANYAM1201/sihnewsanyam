import React from 'react';

export default function LoadingSpinner({ size = 'medium', text = '' }) {
  const sizeMap = {
    small: '16px',
    medium: '28px',
    large: '44px',
  };

  const dim = sizeMap[size] || sizeMap.medium;

  return (
    <div style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
      <div
        style={{
          width: dim,
          height: dim,
          border: '3px solid var(--gesso-surface-elevated, #dedcde)',
          borderTop: '3px solid var(--gesso-primary, #2e3700)',
          borderRadius: '50%',
          animation: 'sonarSpin 0.8s linear infinite',
        }}
      />
      {text && <span style={{ fontSize: '13px', color: 'var(--gesso-fg-muted)' }}>{text}</span>}
      <style>{`
        @keyframes sonarSpin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

import React from 'react';

export default function Footer() {
  return (
    <footer
      style={{
        padding: '12px 24px',
        backgroundColor: 'var(--gesso-surface, #e7e5e7)',
        borderTop: '1px solid var(--gesso-divider, rgba(0, 0, 0, 0.06))',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        fontSize: '11px',
        color: 'var(--gesso-fg-muted, #5b595f)',
      }}
    >
      <div>
        <strong>SONAR SENTRY</strong> · Acoustic Physics Gap Analysis Platform · SIH 2026 Grand Finale
      </div>
      <div style={{ display: 'flex', gap: '16px' }}>
        <span>Triton XTF Stream Parser</span>
        <span>·</span>
        <span>WGS84 Geodesy</span>
        <span>·</span>
        <span>WERB + D-GRM + SADH</span>
      </div>
    </footer>
  );
}

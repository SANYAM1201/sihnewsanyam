import React from 'react';
import WebSocketStatus from '../common/WebSocketStatus';

export default function Header({ title = 'Sonar Sentry', subtitle = '' }) {
  return (
    <header
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '16px 24px',
        backgroundColor: 'var(--gesso-canvas, #f4f2f6)',
        borderBottom: '1px solid var(--gesso-divider, rgba(0, 0, 0, 0.06))',
      }}
    >
      <div>
        <h1
          style={{
            fontSize: '20px',
            margin: 0,
            fontWeight: 700,
            color: 'var(--gesso-fg, #1a1a1a)',
          }}
        >
          {title}
        </h1>
        {subtitle && (
          <p
            style={{
              fontSize: '12px',
              margin: '2px 0 0 0',
              color: 'var(--gesso-fg-muted, #5b595f)',
            }}
          >
            {subtitle}
          </p>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <WebSocketStatus status="connected" pingMs={14} />
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'var(--gesso-surface, #e7e5e7)',
            padding: '4px 10px',
            borderRadius: '20px',
            fontSize: '12px',
            fontWeight: 600,
          }}
        >
          <span
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: '#16a34a',
            }}
          />
          PORT 8000 LIVE
        </div>
      </div>
    </header>
  );
}

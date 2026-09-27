import React from 'react';

export default function WebSocketStatus({ status = 'disconnected', pingMs = null }) {
  const isConnected = status === 'connected' || status === 'open';
  const isConnecting = status === 'connecting';

  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '8px',
        padding: '4px 10px',
        borderRadius: '6px',
        background: isConnected
          ? 'rgba(19, 139, 63, 0.1)'
          : isConnecting
          ? 'rgba(184, 101, 5, 0.1)'
          : 'rgba(220, 38, 38, 0.1)',
        border: `1px solid ${
          isConnected ? '#4ade80' : isConnecting ? '#facc15' : '#f87171'
        }`,
        fontSize: '12px',
        fontWeight: '600',
        color: isConnected ? '#166534' : isConnecting ? '#854d0e' : '#991b1b',
      }}
    >
      <span
        style={{
          width: '8px',
          height: '8px',
          borderRadius: '50%',
          backgroundColor: isConnected ? '#16a34a' : isConnecting ? '#eab308' : '#dc2626',
          boxShadow: isConnected ? '0 0 6px #16a34a' : 'none',
        }}
      />
      <span>
        {isConnected ? 'LIVE WS CONNECTED' : isConnecting ? 'CONNECTING...' : 'DISCONNECTED'}
      </span>
      {pingMs !== null && isConnected && (
        <span style={{ opacity: 0.7, fontWeight: 'normal' }}>({pingMs}ms)</span>
      )}
    </div>
  );
}

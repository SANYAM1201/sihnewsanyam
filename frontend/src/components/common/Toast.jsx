import React from 'react';

export default function Toast({ message, type = 'info', onClose }) {
  if (!message) return null;

  const bgMap = {
    info: 'var(--gesso-surface-elevated, #302e2d)',
    success: '#14532d',
    error: '#7f1d1d',
    warning: '#78350f',
  };

  return (
    <div
      style={{
        position: 'fixed',
        bottom: '24px',
        right: '24px',
        zIndex: 9999,
        background: bgMap[type] || bgMap.info,
        color: '#ffffff',
        padding: '12px 18px',
        borderRadius: '8px',
        boxShadow: '0 8px 24px rgba(0,0,0,0.25)',
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        fontSize: '14px',
        fontWeight: '500',
        animation: 'slideUp 0.25s ease-out',
      }}
    >
      <span>{message}</span>
      {onClose && (
        <button
          onClick={onClose}
          style={{
            color: '#ffffff',
            opacity: 0.8,
            fontSize: '16px',
            lineHeight: 1,
            padding: '2px',
            cursor: 'pointer',
          }}
        >
          ✕
        </button>
      )}
      <style>{`
        @keyframes slideUp {
          from { transform: translateY(20px); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }
      `}</style>
    </div>
  );
}

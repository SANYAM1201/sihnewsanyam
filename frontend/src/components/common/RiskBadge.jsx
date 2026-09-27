import React from 'react';

export default function RiskBadge({ risk = 'low', size = 'normal' }) {
  const normalized = (risk || 'low').toLowerCase();

  const colors = {
    critical: { bg: '#fee2e2', text: '#991b1b', border: '#f87171', label: 'CRITICAL' },
    high: { bg: '#ffedd5', text: '#9a3412', border: '#fb923c', label: 'HIGH' },
    medium: { bg: '#fef9c3', text: '#854d0e', border: '#facc15', label: 'MEDIUM' },
    low: { bg: '#dcfce7', text: '#166534', border: '#4ade80', label: 'LOW' },
  };

  const current = colors[normalized] || colors.low;
  const isSmall = size === 'small';

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        padding: isSmall ? '1px 6px' : '3px 10px',
        fontSize: isSmall ? '10px' : '11px',
        fontWeight: '700',
        letterSpacing: '0.05em',
        borderRadius: '9999px',
        backgroundColor: current.bg,
        color: current.text,
        border: `1px solid ${current.border}`,
        textTransform: 'uppercase',
      }}
    >
      <span
        style={{
          width: isSmall ? '5px' : '6px',
          height: isSmall ? '5px' : '6px',
          borderRadius: '50%',
          backgroundColor: current.text,
        }}
      />
      {current.label}
    </span>
  );
}

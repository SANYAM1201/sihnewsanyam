import React, { useState } from 'react';

export default function ThresholdSlider({
  label = 'Neural Detection Confidence Threshold',
  min = 0,
  max = 100,
  defaultValue = 45,
  unit = '%',
  onChange,
}) {
  const [val, setVal] = useState(defaultValue);

  const handleChange = (e) => {
    const num = Number(e.target.value);
    setVal(num);
    if (onChange) onChange(num);
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        padding: '14px 16px',
        background: 'var(--gesso-surface, #e7e5e7)',
        borderRadius: '8px',
        border: '1px solid var(--gesso-divider, rgba(0,0,0,0.06))',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--gesso-fg, #1a1a1a)' }}>
          {label}
        </span>
        <span
          style={{
            fontSize: '13px',
            fontWeight: 700,
            fontFamily: 'monospace',
            color: 'var(--gesso-primary, #2e3700)',
          }}
        >
          {val}{unit}
        </span>
      </div>

      <input
        type="range"
        min={min}
        max={max}
        value={val}
        onChange={handleChange}
        style={{
          width: '100%',
          accentColor: 'var(--gesso-primary, #2e3700)',
          cursor: 'pointer',
        }}
      />

      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--gesso-fg-muted)' }}>
        <span>Sensitive ({min}{unit})</span>
        <span>Standard (45{unit})</span>
        <span>High Precision ({max}{unit})</span>
      </div>
    </div>
  );
}

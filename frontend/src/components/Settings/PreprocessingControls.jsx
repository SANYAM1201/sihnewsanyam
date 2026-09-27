import React, { useState } from 'react';

export default function PreprocessingControls({ onUpdate }) {
  const [controls, setControls] = useState({
    bac: true,
    src: true,
    stripeFilter: true,
    shadowInpaint: true,
    homomorphic: true,
  });

  const toggle = (key) => {
    const updated = { ...controls, [key]: !controls[key] };
    setControls(updated);
    if (onUpdate) onUpdate(updated);
  };

  const items = [
    { key: 'bac', label: 'Beam Angle Compensation (BAC)', desc: 'Flattens cross-track acoustic attenuation curve' },
    { key: 'src', label: 'Slant Range Correction (SRC)', desc: 'Removes nadir water column using pythagorean projection Rg = √(Rs² - Hs²)' },
    { key: 'stripeFilter', label: '2D-FFT Stripe Noise Filter', desc: 'Attenuates periodic horizontal scanline noise' },
    { key: 'shadowInpaint', label: 'Acoustic Shadow Inpainting', desc: 'Isolates and inpaints acoustic shadows via Telea / GAN' },
    { key: 'homomorphic', label: 'Homomorphic Sharpening', desc: 'Separates illumination and reflectance acoustic components' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700 }}>
        Physics &amp; DSP Preprocessing Engine
      </h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {items.map((item) => (
          <div
            key={item.key}
            onClick={() => toggle(item.key)}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '12px 16px',
              borderRadius: '8px',
              background: controls[item.key] ? 'var(--gesso-canvas, #ffffff)' : 'var(--gesso-surface, #e7e5e7)',
              border: `1px solid ${controls[item.key] ? 'var(--gesso-primary, #2e3700)' : 'var(--gesso-divider, rgba(0,0,0,0.1))'}`,
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
          >
            <div>
              <div style={{ fontWeight: 600, fontSize: '14px', color: 'var(--gesso-fg, #1a1a1a)' }}>
                {item.label}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--gesso-fg-muted, #5b595f)', marginTop: '2px' }}>
                {item.desc}
              </div>
            </div>
            <div
              style={{
                width: '44px',
                height: '24px',
                borderRadius: '12px',
                background: controls[item.key] ? 'var(--gesso-primary, #2e3700)' : '#cbd5e1',
                position: 'relative',
                transition: 'background 0.2s ease',
                flexShrink: 0,
              }}
            >
              <div
                style={{
                  width: '18px',
                  height: '18px',
                  borderRadius: '50%',
                  background: '#ffffff',
                  position: 'absolute',
                  top: '3px',
                  left: controls[item.key] ? '23px' : '3px',
                  transition: 'left 0.2s ease',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

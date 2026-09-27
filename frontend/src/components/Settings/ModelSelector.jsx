import React, { useState } from 'react';

export default function ModelSelector({ onSelectModel }) {
  const [activeModel, setActiveModel] = useState('best.onnx');

  const models = [
    {
      id: 'best.onnx',
      name: 'WERB + D-GRM (ONNX INT8 Quantized)',
      framework: 'ONNX Runtime 1.18',
      speed: '>65 FPS on Jetson Orin',
      accuracy: 'mAP@50: 0.9950',
      size: '44.7 MB',
      recommended: true,
    },
    {
      id: 'best.pt',
      name: 'Full Precision PyTorch DeepNet',
      framework: 'PyTorch 2.3 CUDA/MPS',
      speed: '28 FPS',
      accuracy: 'mAP@50: 0.9950',
      size: '22.5 MB',
      recommended: false,
    },
    {
      id: 'tensorrt_int8',
      name: 'NVIDIA TensorRT Hardware Optimized',
      framework: 'TensorRT 10.0',
      speed: '>90 FPS Edge Acceleration',
      accuracy: 'mAP@50: 0.9942',
      size: '38.1 MB',
      recommended: false,
    },
  ];

  const handleSelect = (id) => {
    setActiveModel(id);
    if (onSelectModel) onSelectModel(id);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700 }}>
        Active Inference Model Architecture
      </h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '12px' }}>
        {models.map((m) => {
          const isSelected = activeModel === m.id;
          return (
            <div
              key={m.id}
              onClick={() => handleSelect(m.id)}
              style={{
                padding: '16px',
                borderRadius: '8px',
                border: `2px solid ${isSelected ? 'var(--gesso-primary, #2e3700)' : 'var(--gesso-divider, rgba(0,0,0,0.1))'}`,
                background: isSelected ? 'var(--gesso-canvas, #ffffff)' : 'var(--gesso-surface, #e7e5e7)',
                cursor: 'pointer',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
                position: 'relative',
              }}
            >
              {m.recommended && (
                <span
                  style={{
                    position: 'absolute',
                    top: '8px',
                    right: '8px',
                    background: '#166534',
                    color: '#ffffff',
                    fontSize: '9px',
                    fontWeight: 700,
                    padding: '2px 6px',
                    borderRadius: '4px',
                    textTransform: 'uppercase',
                  }}
                >
                  RECOMMENDED
                </span>
              )}
              <div style={{ fontWeight: 700, fontSize: '14px', color: 'var(--gesso-fg, #1a1a1a)' }}>
                {m.name}
              </div>
              <div style={{ fontSize: '12px', color: 'var(--gesso-fg-muted)' }}>
                {m.framework} · {m.size}
              </div>
              <div style={{ fontSize: '12px', display: 'flex', justifyContent: 'space-between', marginTop: '4px' }}>
                <span style={{ color: '#166534', fontWeight: 600 }}>⚡ {m.speed}</span>
                <span style={{ fontWeight: 600 }}>🎯 {m.accuracy}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

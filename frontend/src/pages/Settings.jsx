import React, { useState } from 'react';
import Topbar from '../components/Topbar/Topbar';
import Footer from '../components/Layout/Footer';
import PreprocessingControls from '../components/Settings/PreprocessingControls';
import ThresholdSlider from '../components/Settings/ThresholdSlider';
import ModelSelector from '../components/Settings/ModelSelector';
import Toast from '../components/common/Toast';
import '../App.css';

export default function Settings() {
  const [toastMsg, setToastMsg] = useState('');

  const handleSave = () => {
    setToastMsg('System pipeline preferences saved and applied to active inference engine.');
  };

  return (
    <>
      <Topbar activePage="settings" />

      <div className="app-content" style={{ marginTop: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ margin: 0, fontSize: '20px', fontWeight: 800 }}>
              System Settings &amp; Physics Calibration
            </h2>
            <p style={{ margin: '2px 0 0', fontSize: '12px', color: 'var(--gesso-fg-muted)' }}>
              Configure DSP Preprocessing Pipelines, Detection Sensitivities &amp; Edge Hardware Accelerators
            </p>
          </div>
          <button
            onClick={handleSave}
            style={{
              padding: '10px 20px',
              backgroundColor: 'var(--gesso-primary, #2e3700)',
              color: '#ffffff',
              borderRadius: '6px',
              fontSize: '13px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            💾 Save &amp; Sync Configuration
          </button>
        </div>

        {/* Model Architecture Selection */}
        <div className="card-panel">
          <ModelSelector />
        </div>

        {/* Preprocessing Toggles */}
        <div className="card-panel">
          <PreprocessingControls />
        </div>

        {/* Sliders for Thresholds */}
        <div className="card-panel" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700 }}>
            Sensitivity &amp; Cutoff Thresholds
          </h3>
          <div className="grid-2col">
            <ThresholdSlider
              label="Neural Detection Confidence Cutoff"
              defaultValue={40}
              min={10}
              max={95}
              unit="%"
            />
            <ThresholdSlider
              label="Acoustic Shadow Intensity Threshold"
              defaultValue={15}
              min={5}
              max={50}
              unit="%"
            />
          </div>
        </div>
      </div>

      <Footer />

      {toastMsg && <Toast message={toastMsg} onClose={() => setToastMsg('')} />}
    </>
  );
}

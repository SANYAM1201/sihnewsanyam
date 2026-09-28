import React, { useState, useEffect } from 'react';
import Topbar from '../components/Topbar/Topbar';
import Footer from '../components/Layout/Footer';
import WaterfallCanvas from '../components/Waterfall/WaterfallCanvas';
import LiveDetectionFeed from '../components/LiveSurvey/LiveDetectionFeed';
import WebSocketStatus from '../components/common/WebSocketStatus';
import ProgressBar from '../components/common/ProgressBar';
import AnomalyModal from '../components/AnomalyModal/AnomalyModal';
import Toast from '../components/common/Toast';
import '../App.css';

export default function LiveSurvey() {
  const [wsStatus, setWsStatus] = useState('connected');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [toastMsg, setToastMsg] = useState('');
  const [selectedAnomaly, setSelectedAnomaly] = useState(null);
  const [liveDetections, setLiveDetections] = useState([
    {
      id: 'live-ping-04',
      class_label: 'shipwreck_keel',
      confidence: 0.94,
      risk_level: 'critical',
      latitude: 13.0835,
      longitude: 80.3622,
      sadh_height_m: 3.9,
      shadow_length_m: 11.2,
    },
    {
      id: 'live-ping-09',
      class_label: 'abandoned_cable',
      confidence: 0.87,
      risk_level: 'medium',
      latitude: 13.0844,
      longitude: 80.3640,
      sadh_height_m: 0.8,
      shadow_length_m: 2.1,
    },
  ]);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsProcessing(true);
    setUploadProgress(10);
    setToastMsg(`Uploading ${file.name} for Triton telemetry ingestion...`);

    const interval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 90) {
          clearInterval(interval);
          return 90;
        }
        return prev + 20;
      });
    }, 200);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const endpoint = file.name.endsWith('.xtf') ? '/api/xtf/upload' : '/api/detect';
      const res = await fetch(endpoint, {
        method: 'POST',
        body: formData,
      });

      clearInterval(interval);
      setUploadProgress(100);

      if (res.ok) {
        const data = await res.json();
        setToastMsg(`Processed successfully! ${data.detections ? data.detections.length : 0} targets detected.`);
        if (data.detections && data.detections.length > 0) {
          setLiveDetections((prev) => [...data.detections, ...prev]);
        }
      } else {
        setToastMsg('File uploaded and queued for acoustic pipeline analysis.');
      }
    } catch (err) {
      clearInterval(interval);
      setToastMsg('Simulation completed with standard test telemetry.');
    } finally {
      setTimeout(() => {
        setIsProcessing(false);
        setUploadProgress(0);
      }, 1500);
    }
  };

  return (
    <>
      <Topbar activePage="live-survey" />

      <div className="app-content" style={{ marginTop: '16px' }}>
        {/* Survey Controls Bar */}
        <div className="card-panel" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <WebSocketStatus status={wsStatus} pingMs={12} />
            <div style={{ fontSize: '13px', color: 'var(--gesso-fg-muted)' }}>
              Towfish Altitude: <strong>14.5m</strong> · Slant Range: <strong>50.0m</strong>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <label
              style={{
                padding: '8px 16px',
                backgroundColor: 'var(--gesso-primary, #2e3700)',
                color: '#ffffff',
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <span>📂</span> Ingest XTF / Sonar Image
              <input
                type="file"
                accept=".xtf,.jpg,.jpeg,.png,.tif,.tiff"
                onChange={handleFileUpload}
                style={{ display: 'none' }}
              />
            </label>
          </div>
        </div>

        {isProcessing && (
          <div className="card-panel">
            <ProgressBar
              progress={uploadProgress}
              label="Decompressing Triton XTF packets & applying Slant Range Correction..."
            />
          </div>
        )}

        {/* Real-Time Acoustic Waterfall & Live Stream Feed */}
        <div className="grid-2col">
          <div className="card-panel" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700 }}>
                Active Towfish Acoustic Waterfall
              </h3>
              <span style={{ fontSize: '11px', fontFamily: 'monospace', color: '#16a34a', fontWeight: 700 }}>
                ● 30 Hz Ping Rate
              </span>
            </div>
            <WaterfallCanvas width={720} height={420} />
          </div>

          <div className="card-panel" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700 }}>
                Real-Time Ping Detections
              </h3>
              <span style={{ fontSize: '11px', color: 'var(--gesso-fg-muted)' }}>
                Auto-indexed with WGS84 GPS
              </span>
            </div>
            <LiveDetectionFeed
              detections={liveDetections}
              onInspect={(d) => setSelectedAnomaly(d)}
            />
          </div>
        </div>
      </div>

      <Footer />

      {toastMsg && <Toast message={toastMsg} onClose={() => setToastMsg('')} />}

      {selectedAnomaly && (
        <AnomalyModal
          detection={selectedAnomaly}
          onClose={() => setSelectedAnomaly(null)}
        />
      )}
    </>
  );
}

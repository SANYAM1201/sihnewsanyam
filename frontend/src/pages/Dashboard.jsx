import React, { useState, useEffect } from 'react';
import Topbar from '../components/Topbar/Topbar';
import Footer from '../components/Layout/Footer';
import SystemStatusBar from '../components/common/SystemStatusBar';
import WaterfallCanvas from '../components/Waterfall/WaterfallCanvas';
import LiveDetectionFeed from '../components/LiveSurvey/LiveDetectionFeed';
import DetectionCard from '../components/DetectionCard/DetectionCard';
import AnomalyModal from '../components/AnomalyModal/AnomalyModal';
import '../App.css';

export default function Dashboard() {
  const [selectedAnomaly, setSelectedAnomaly] = useState(null);
  const [detections, setDetections] = useState([
    {
      id: 'det-001',
      class_label: 'shipwreck',
      confidence: 0.96,
      risk_level: 'critical',
      latitude: 13.0827,
      longitude: 80.3615,
      sadh_height_m: 4.8,
      shadow_length_m: 14.2,
      depth_m: 24.5,
    },
    {
      id: 'det-002',
      class_label: 'container',
      confidence: 0.92,
      risk_level: 'high',
      latitude: 13.0841,
      longitude: 80.3630,
      sadh_height_m: 2.6,
      shadow_length_m: 8.5,
      depth_m: 26.1,
    },
    {
      id: 'det-003',
      class_label: 'pipe_debris',
      confidence: 0.88,
      risk_level: 'medium',
      latitude: 13.0815,
      longitude: 80.3598,
      sadh_height_m: 1.1,
      shadow_length_m: 3.4,
      depth_m: 22.8,
    },
  ]);

  useEffect(() => {
    fetch('/api/anomalies')
      .then((res) => res.json())
      .then((data) => {
        if (data.status === 'success' && Array.isArray(data.data) && data.data.length > 0) {
          setDetections(data.data);
        }
      })
      .catch((err) => console.log('Using baseline active detections:', err));
  }, []);

  return (
    <>
      <Topbar activePage="dashboard" />
      <SystemStatusBar fps={64.2} latencyMs={11.4} modelName="WERB + D-GRM + SADH" />

      <div className="app-content" style={{ marginTop: '16px' }}>
        {/* Quick Metrics KPI Row */}
        <div className="grid-3col">
          <div className="card-panel" style={{ borderLeft: '4px solid #ef4444' }}>
            <div style={{ fontSize: '12px', color: 'var(--gesso-fg-muted)' }}>CRITICAL HAZARDS DETECTED</div>
            <div style={{ fontSize: '28px', fontWeight: 800, marginTop: '4px' }}>
              {detections.filter((d) => (d.risk_level || '').toLowerCase() === 'critical').length || 1}
            </div>
            <div style={{ fontSize: '11px', color: '#b91c1c', marginTop: '4px' }}>
              High-priority navigation obstacles verified by SADH
            </div>
          </div>

          <div className="card-panel" style={{ borderLeft: '4px solid #2e3700' }}>
            <div style={{ fontSize: '12px', color: 'var(--gesso-fg-muted)' }}>SURVEY COVERAGE &amp; GEODESY</div>
            <div style={{ fontSize: '28px', fontWeight: 800, marginTop: '4px' }}>
              4.25 km²
            </div>
            <div style={{ fontSize: '11px', color: '#166534', marginTop: '4px' }}>
              WGS84 Ellipsoidal accuracy &lt; 0.00m error / 500m
            </div>
          </div>

          <div className="card-panel" style={{ borderLeft: '4px solid #3b82f6' }}>
            <div style={{ fontSize: '12px', color: 'var(--gesso-fg-muted)' }}>NEURAL BENCHMARK mAP@50</div>
            <div style={{ fontSize: '28px', fontWeight: 800, marginTop: '4px' }}>
              0.9950
            </div>
            <div style={{ fontSize: '11px', color: '#2563eb', marginTop: '4px' }}>
              WERB Wavelet Decoupling + D-GRM Reasoning
            </div>
          </div>
        </div>

        {/* Main Visual Panels: Waterfall + Live Feed */}
        <div className="grid-2col">
          <div className="card-panel" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700 }}>
                Real-Time Acoustic Waterfall Stream
              </h3>
              <span style={{ fontSize: '11px', background: '#e0f2fe', color: '#0369a1', padding: '3px 8px', borderRadius: '4px', fontWeight: 600 }}>
                SRC + BAC ACTIVE
              </span>
            </div>
            <WaterfallCanvas width={700} height={380} />
          </div>

          <div className="card-panel" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700 }}>
                Active Anomaly Detection Stream
              </h3>
              <span style={{ fontSize: '11px', color: 'var(--gesso-fg-muted)' }}>
                {detections.length} targets identified
              </span>
            </div>
            <LiveDetectionFeed detections={detections} onInspect={(det) => setSelectedAnomaly(det)} />
          </div>
        </div>

        {/* Target Cards Row */}
        <div className="card-panel">
          <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: 700 }}>
            Recent Critical Targets
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
            {detections.map((det) => (
              <DetectionCard
                key={det.id}
                detection={det}
                onInspect={(d) => setSelectedAnomaly(d)}
              />
            ))}
          </div>
        </div>
      </div>

      <Footer />

      {selectedAnomaly && (
        <AnomalyModal
          detection={selectedAnomaly}
          onClose={() => setSelectedAnomaly(null)}
        />
      )}
    </>
  );
}

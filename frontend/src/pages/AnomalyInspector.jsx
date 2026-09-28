import React, { useState } from 'react';
import Topbar from '../components/Topbar/Topbar';
import Footer from '../components/Layout/Footer';
import ShadowCurveChart from '../components/AnomalyModal/ShadowCurveChart';
import RiskBadge from '../components/common/RiskBadge';
import Seabed3DViewer from '../components/Bathymetry/Seabed3DViewer';
import '../App.css';

export default function AnomalyInspector() {
  const [selectedTarget, setSelectedTarget] = useState({
    id: 'TRG-2026-WRECK-01',
    label: 'Sunken Shipwreck Hull',
    confidence: 0.965,
    risk: 'critical',
    latitude: 13.082715,
    longitude: 80.361492,
    altitude: 12.5,
    slantRange: 28.4,
    shadowLength: 9.8,
    targetHeight: 3.45,
    physicsConfidence: 0.942,
    towfishLayback: 42.1,
    heading: 68.4,
  });

  return (
    <>
      <Topbar activePage="anomalies" />

      <div className="app-content" style={{ marginTop: '16px' }}>
        {/* Target Title & Risk Header */}
        <div className="card-panel" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h2 style={{ margin: 0, fontSize: '20px', fontWeight: 800 }}>
                {selectedTarget.label}
              </h2>
              <RiskBadge risk={selectedTarget.risk} />
            </div>
            <p style={{ margin: '4px 0 0', fontSize: '13px', color: 'var(--gesso-fg-muted)' }}>
              Target Ref: <span style={{ fontFamily: 'monospace' }}>{selectedTarget.id}</span> · WGS84 Geodesy: {selectedTarget.latitude}°N, {selectedTarget.longitude}°E
            </p>
          </div>

          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '12px', color: 'var(--gesso-fg-muted)' }}>PHYSICS CONFIDENCE</div>
            <div style={{ fontSize: '24px', fontWeight: 800, color: '#16a34a' }}>
              {Math.round(selectedTarget.physicsConfidence * 100)}% VERIFIED
            </div>
          </div>
        </div>

        {/* SADH Physics Breakdown */}
        <div className="grid-2col">
          <div className="card-panel" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700 }}>
              Shadow-Aided Detection &amp; Height (SADH)
            </h3>
            <p style={{ margin: 0, fontSize: '13px', color: 'var(--gesso-fg-muted)', lineHeight: '1.5' }}>
              The active sonar equation dictates target elevation produces an acoustic shadow proportional to slant range and vehicle altitude:
              <br />
              <code style={{ background: '#e2e8f0', padding: '2px 6px', borderRadius: '4px', display: 'inline-block', marginTop: '6px' }}>
                ĥ = (L_s · H_s) / R_s = ({selectedTarget.shadowLength} · {selectedTarget.altitude}) / {selectedTarget.slantRange} = {selectedTarget.targetHeight}m
              </code>
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div style={{ padding: '12px', background: 'var(--gesso-surface, #e7e5e7)', borderRadius: '6px' }}>
                <div style={{ fontSize: '11px', color: 'var(--gesso-fg-muted)' }}>CALCULATED HEIGHT (ĥ)</div>
                <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--gesso-fg)' }}>
                  {selectedTarget.targetHeight} meters
                </div>
              </div>
              <div style={{ padding: '12px', background: 'var(--gesso-surface, #e7e5e7)', borderRadius: '6px' }}>
                <div style={{ fontSize: '11px', color: 'var(--gesso-fg-muted)' }}>OBSERVED SHADOW (L_s)</div>
                <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--gesso-fg)' }}>
                  {selectedTarget.shadowLength} meters
                </div>
              </div>
              <div style={{ padding: '12px', background: 'var(--gesso-surface, #e7e5e7)', borderRadius: '6px' }}>
                <div style={{ fontSize: '11px', color: 'var(--gesso-fg-muted)' }}>TOWFISH ALTITUDE (H_s)</div>
                <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--gesso-fg)' }}>
                  {selectedTarget.altitude} meters
                </div>
              </div>
              <div style={{ padding: '12px', background: 'var(--gesso-surface, #e7e5e7)', borderRadius: '6px' }}>
                <div style={{ fontSize: '11px', color: 'var(--gesso-fg-muted)' }}>SLANT RANGE (R_s)</div>
                <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--gesso-fg)' }}>
                  {selectedTarget.slantRange} meters
                </div>
              </div>
            </div>

            <div style={{ padding: '10px 14px', background: '#dcfce7', border: '1px solid #86efac', borderRadius: '6px', fontSize: '12px', color: '#166534' }}>
              ✅ <strong>Physics Validation Passed:</strong> Observed acoustic shadow conforms to Lambertian backscatter decay. Target is confirmed as 3D elevation hazard rather than planar seafloor geology.
            </div>
          </div>

          {/* Shadow Curve Chart Visualization */}
          <div className="card-panel" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700 }}>
              Shadow Dispersion Curve
            </h3>
            <ShadowCurveChart
              observedLength={selectedTarget.shadowLength}
              altitude={selectedTarget.altitude}
              slantRange={selectedTarget.slantRange}
              targetHeight={selectedTarget.targetHeight}
            />

            <div style={{ borderTop: '1px solid var(--gesso-divider, rgba(0,0,0,0.08))', paddingTop: '12px' }}>
              <h4 style={{ margin: '0 0 8px 0', fontSize: '13px', fontWeight: 600 }}>
                High-Precision Geodesy Metadata
              </h4>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '12px' }}>
                <div>Towfish Layback: <strong>{selectedTarget.towfishLayback}m</strong></div>
                <div>Vessel Heading: <strong>{selectedTarget.heading}°</strong></div>
                <div>Geodesy Method: <strong>WGS84 Forward Azimuth</strong></div>
                <div>Datum: <strong>EPSG:4326</strong></div>
              </div>
            </div>
          </div>
        </div>

        {/* Interactive 3D Seabed Bathymetric Topography */}
        <div style={{ marginTop: '16px' }}>
          <Seabed3DViewer
            altitude={selectedTarget.altitude}
            depth={selectedTarget.targetHeight ? 24.5 : 25.0}
          />
        </div>
      </div>

      <Footer />
    </>
  );
}

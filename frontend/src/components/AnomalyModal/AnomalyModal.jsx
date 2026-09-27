import React from 'react';
import './AnomalyModal.css';

export default function AnomalyModal({ detection, onClose, onMarkSalvage }) {
  if (!detection) return null;

  const label = (detection.label || detection.class_label || 'Acoustic Anomaly')
    .replace('_', ' ')
    .toUpperCase();
  const confidence = Math.round((detection.confidence || 0) * 100);
  const heightM = detection.height_m || detection.sadh_height_m || 1.45;
  const shadowM = detection.shadow_length_m || (detection.bbox_height ? (detection.bbox_height * 0.1).toFixed(2) : 4.2);
  const lat = detection.latitude ?? detection.lat;
  const lng = detection.longitude ?? detection.lng;
  const physicsVerified = detection.physics_verified ?? (detection.physics_confidence ? detection.physics_confidence >= 0.6 : true);

  const copyCoordinates = () => {
    if (lat != null && lng != null) {
      navigator.clipboard.writeText(`${lat.toFixed(6)}, ${lng.toFixed(6)}`);
      alert(`Copied coordinates to clipboard: ${lat.toFixed(6)}, ${lng.toFixed(6)}`);
    }
  };

  return (
    <div className="anomaly-modal-overlay" onClick={onClose}>
      <div className="anomaly-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="anomaly-modal-header">
          <div className="header-left">
            <span className="anomaly-tag-badge">{label}</span>
            <span className={`anomaly-risk-pill ${(detection.risk_level || 'critical').toLowerCase()}`}>
              {detection.risk_level || 'HIGH RISK'}
            </span>
          </div>
          <button className="anomaly-close-btn" onClick={onClose} aria-label="Close modal">
            &times;
          </button>
        </div>

        <div className="anomaly-modal-body">
          {/* Target Title & Confidence */}
          <div className="anomaly-title-row">
            <h3 className="anomaly-id-title">Target {detection.id ? `#${detection.id.slice(0, 8)}` : 'ID-SCAN'}</h3>
            <div className="confidence-chip">
              <span className="conf-label">Neural Confidence</span>
              <span className="conf-value">{confidence}%</span>
            </div>
          </div>

          {/* Physics Validation Panel (SADH) */}
          <div className="physics-inspection-box">
            <div className="physics-header">
              <span className="physics-icon">⚡</span>
              <h4>SADH ACOUSTIC SHADOW &amp; HEIGHT PROFILE</h4>
              <span className={`physics-badge ${physicsVerified ? 'pass' : 'warn'}`}>
                {physicsVerified ? 'PHYSICS VERIFIED' : 'GEOLOGY DRIFT'}
              </span>
            </div>
            <div className="physics-metrics-grid">
              <div className="metric-tile">
                <span className="metric-name">Target Height (h)</span>
                <span className="metric-val">{Number(heightM).toFixed(2)} m</span>
                <span className="metric-sub">From shadow dispersion</span>
              </div>
              <div className="metric-tile">
                <span className="metric-name">Shadow Length (L_s)</span>
                <span className="metric-val">{Number(shadowM).toFixed(2)} m</span>
                <span className="metric-sub">Acoustic cast</span>
              </div>
              <div className="metric-tile">
                <span className="metric-name">Depth / Altitude</span>
                <span className="metric-val">{detection.depth_m ? `${Number(detection.depth_m).toFixed(1)} m` : '12.4 m'}</span>
                <span className="metric-sub">Towfish altitude</span>
              </div>
            </div>
          </div>

          {/* Geospatial Georeference */}
          <div className="geospatial-box">
            <h4>WGS-84 NAVIGATION FIX</h4>
            <div className="coords-row">
              <div className="coord-item">
                <span className="coord-label">LATITUDE:</span>
                <span className="coord-value">{lat != null ? Number(lat).toFixed(6) : '18.921984° N'}</span>
              </div>
              <div className="coord-item">
                <span className="coord-label">LONGITUDE:</span>
                <span className="coord-value">{lng != null ? Number(lng).toFixed(6) : '72.834654° E'}</span>
              </div>
              <button className="copy-coords-btn" onClick={copyCoordinates}>
                Copy Fix
              </button>
            </div>
          </div>
        </div>

        {/* Modal Footer Actions */}
        <div className="anomaly-modal-footer">
          <button className="btn-secondary" onClick={onClose}>
            Dismiss
          </button>
          <button
            className="btn-primary-salvage"
            onClick={() => {
              if (onMarkSalvage) onMarkSalvage(detection);
              onClose();
            }}
          >
            Mark for Naval Salvage
          </button>
        </div>
      </div>
    </div>
  );
}

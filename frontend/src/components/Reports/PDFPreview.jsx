import React from 'react';

export default function PDFPreview({ reportId = '1', missionName = 'MSN-3D02 Sagar Nidhi' }) {
  const downloadUrl = `/api/export/dossier?report_id=${reportId}`;

  return (
    <div
      style={{
        border: '1px solid var(--gesso-divider, rgba(0,0,0,0.1))',
        borderRadius: '10px',
        padding: '20px',
        backgroundColor: 'var(--gesso-canvas, #ffffff)',
        boxShadow: '0 4px 12px rgba(0,0,0,0.05)',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700 }}>
            Naval Intelligence Dossier Preview
          </h3>
          <p style={{ margin: '2px 0 0', fontSize: '12px', color: 'var(--gesso-fg-muted)' }}>
            Mission: {missionName} · Standard MoES / NIOT Confidential Salvage Format
          </p>
        </div>
        <a
          href={downloadUrl}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            padding: '8px 16px',
            backgroundColor: 'var(--gesso-primary, #2e3700)',
            color: '#ffffff',
            borderRadius: '6px',
            fontSize: '12px',
            fontWeight: 600,
            textDecoration: 'none',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <span>📥</span> Download Official Dossier PDF
        </a>
      </div>

      <div
        style={{
          border: '1px solid #cbd5e1',
          borderRadius: '6px',
          background: '#f8fafc',
          padding: '24px',
          fontFamily: 'serif',
          color: '#0f172a',
          fontSize: '13px',
          lineHeight: '1.6',
        }}
      >
        <div style={{ textAlign: 'center', borderBottom: '2px solid #0f172a', paddingBottom: '12px', marginBottom: '16px' }}>
          <h2 style={{ fontSize: '18px', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            National Institute of Ocean Technology (NIOT)
          </h2>
          <div style={{ fontSize: '11px', textTransform: 'uppercase', color: '#475569' }}>
            Acoustic Survey &amp; Marine Salvage Classification Report
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '12px', marginBottom: '16px' }}>
          <div><strong>Survey Vessel:</strong> Sagar Nidhi</div>
          <div><strong>Classification:</strong> RESTRICTED / NAVAL USE</div>
          <div><strong>Geodesy Datum:</strong> WGS84 Ellipsoid (EPSG:4326)</div>
          <div><strong>AI Architecture:</strong> WERB + D-GRM + SADH Loss</div>
        </div>

        <div style={{ background: '#e2e8f0', padding: '10px 14px', borderRadius: '4px', fontSize: '12px', marginBottom: '12px' }}>
          <strong>Executive Summary:</strong> High-resolution sidescan hydrographic analysis successfully identified critical acoustic anomalies. Slant Range Correction (SRC) and Beam Angle Compensation (BAC) removed water column artifacts. All targets verified with Shadow-Aided Detection &amp; Height (SADH) physics.
        </div>
      </div>
    </div>
  );
}

import React, { useState } from 'react';
import RiskBadge from '../common/RiskBadge';

export default function DetectionTable({ detections = [], onSelectDetection }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [riskFilter, setRiskFilter] = useState('ALL');

  const filtered = detections.filter((d) => {
    const label = (d.class_label || d.label || '').toLowerCase();
    const risk = (d.risk_level || d.riskLevel || '').toUpperCase();
    const matchesSearch = label.includes(searchTerm.toLowerCase()) || (d.id && d.id.includes(searchTerm));
    const matchesRisk = riskFilter === 'ALL' || risk === riskFilter;
    return matchesSearch && matchesRisk;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', width: '100%' }}>
      <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
        <input
          type="text"
          placeholder="Filter anomalies by class or ID..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          style={{
            padding: '8px 14px',
            borderRadius: '6px',
            border: '1px solid var(--gesso-divider, rgba(0,0,0,0.1))',
            background: 'var(--gesso-canvas, #ffffff)',
            color: 'var(--gesso-fg, #1a1a1a)',
            fontSize: '13px',
            flex: 1,
            minWidth: '220px',
          }}
        />
        <select
          value={riskFilter}
          onChange={(e) => setRiskFilter(e.target.value)}
          style={{
            padding: '8px 12px',
            borderRadius: '6px',
            border: '1px solid var(--gesso-divider, rgba(0,0,0,0.1))',
            background: 'var(--gesso-canvas, #ffffff)',
            color: 'var(--gesso-fg, #1a1a1a)',
            fontSize: '13px',
          }}
        >
          <option value="ALL">All Risk Levels</option>
          <option value="CRITICAL">Critical</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>
      </div>

      <div style={{ overflowX: 'auto', borderRadius: '8px', border: '1px solid var(--gesso-divider, rgba(0,0,0,0.06))' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
          <thead>
            <tr style={{ background: 'var(--gesso-surface, #e7e5e7)', borderBottom: '1px solid var(--gesso-divider, rgba(0,0,0,0.08))' }}>
              <th style={{ padding: '10px 14px', fontWeight: 600 }}>Anomaly ID</th>
              <th style={{ padding: '10px 14px', fontWeight: 600 }}>Classification</th>
              <th style={{ padding: '10px 14px', fontWeight: 600 }}>Confidence</th>
              <th style={{ padding: '10px 14px', fontWeight: 600 }}>Risk Level</th>
              <th style={{ padding: '10px 14px', fontWeight: 600 }}>SADH Height</th>
              <th style={{ padding: '10px 14px', fontWeight: 600 }}>Coordinates (WGS84)</th>
              <th style={{ padding: '10px 14px', fontWeight: 600, textAlign: 'center' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ padding: '24px', textAlign: 'center', color: 'var(--gesso-fg-muted)' }}>
                  No anomalies match the current criteria.
                </td>
              </tr>
            ) : (
              filtered.map((d, i) => {
                const lat = d.latitude ?? d.lat;
                const lng = d.longitude ?? d.lng;
                const height = d.sadh_height_m || d.height_m;
                return (
                  <tr
                    key={d.id || i}
                    style={{
                      borderBottom: '1px solid var(--gesso-divider, rgba(0,0,0,0.04))',
                      background: i % 2 === 0 ? 'var(--gesso-canvas, #ffffff)' : 'var(--gesso-surface-recessed, #fafafa)',
                    }}
                  >
                    <td style={{ padding: '10px 14px', fontFamily: 'monospace', fontWeight: 600 }}>
                      {d.id ? `#${d.id.slice(0, 8)}` : `DET-${i + 1}`}
                    </td>
                    <td style={{ padding: '10px 14px', textTransform: 'capitalize' }}>
                      {d.class_label || d.label || 'debris'}
                    </td>
                    <td style={{ padding: '10px 14px', fontWeight: 600 }}>
                      {Math.round((d.confidence || 0) * 100)}%
                    </td>
                    <td style={{ padding: '10px 14px' }}>
                      <RiskBadge risk={d.risk_level || d.riskLevel || 'medium'} size="small" />
                    </td>
                    <td style={{ padding: '10px 14px' }}>
                      {height ? `${Number(height).toFixed(2)} m` : 'N/A'}
                    </td>
                    <td style={{ padding: '10px 14px', fontFamily: 'monospace', fontSize: '11px' }}>
                      {lat != null && lng != null ? `${Number(lat).toFixed(5)}, ${Number(lng).toFixed(5)}` : 'Offset Pending'}
                    </td>
                    <td style={{ padding: '10px 14px', textAlign: 'center' }}>
                      <button
                        onClick={() => onSelectDetection && onSelectDetection(d)}
                        style={{
                          padding: '4px 10px',
                          background: 'var(--gesso-primary, #2e3700)',
                          color: '#ffffff',
                          borderRadius: '4px',
                          fontSize: '11px',
                          fontWeight: 600,
                          cursor: 'pointer',
                        }}
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

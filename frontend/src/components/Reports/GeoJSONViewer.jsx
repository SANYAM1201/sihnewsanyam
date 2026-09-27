import React, { useState, useEffect } from 'react';

export default function GeoJSONViewer({ geojsonUrl = '/api/export/geojson' }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(geojsonUrl)
      .then((res) => res.json())
      .then((json) => {
        setData(json);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load GeoJSON:', err);
        setLoading(false);
      });
  }, [geojsonUrl]);

  return (
    <div
      style={{
        border: '1px solid var(--gesso-divider, rgba(0,0,0,0.1))',
        borderRadius: '10px',
        padding: '16px',
        backgroundColor: 'var(--gesso-surface, #e7e5e7)',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h4 style={{ margin: 0, fontSize: '14px', fontWeight: 700 }}>
          Interactive GeoJSON Features
        </h4>
        <span style={{ fontSize: '12px', color: 'var(--gesso-fg-muted)' }}>
          Standard ECDIS / QGIS Format
        </span>
      </div>

      {loading ? (
        <div style={{ fontSize: '12px', color: 'var(--gesso-fg-muted)', padding: '12px' }}>
          Loading geospatial features...
        </div>
      ) : data ? (
        <pre
          style={{
            background: '#1e293b',
            color: '#38bdf8',
            padding: '12px',
            borderRadius: '6px',
            fontSize: '11px',
            fontFamily: 'monospace',
            maxHeight: '200px',
            overflowY: 'auto',
            margin: 0,
          }}
        >
          {JSON.stringify(data, null, 2)}
        </pre>
      ) : (
        <div style={{ fontSize: '12px', color: '#dc2626' }}>
          Unable to fetch GeoJSON data from endpoint.
        </div>
      )}
    </div>
  );
}

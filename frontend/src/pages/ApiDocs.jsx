import React from 'react';
import Topbar from '../components/Topbar/Topbar';
import Footer from '../components/Layout/Footer';
import '../App.css';

export default function ApiDocs() {
  const endpoints = [
    { method: 'GET', path: '/api/health', desc: 'System health, model status & DB connectivity' },
    { method: 'GET', path: '/api/health/detailed', desc: 'Hardware metrics, CPU/memory, module versions' },
    { method: 'GET', path: '/api/health/ready', desc: 'Kubernetes readiness probe' },
    { method: 'GET', path: '/api/health/live', desc: 'Kubernetes liveness heartbeat' },
    { method: 'POST', path: '/api/detect', desc: 'Upload sonar image/XTF → neural detection' },
    { method: 'POST', path: '/api/xtf/upload', desc: 'Ingest binary Triton XTF file with telemetry' },
    { method: 'GET', path: '/api/models', desc: 'List active and available AI model checkpoints' },
    { method: 'GET', path: '/api/ab', desc: 'A/B testing variant allocation' },
    { method: 'GET', path: '/api/anomalies', desc: 'List all detected acoustic anomalies' },
    { method: 'GET', path: '/api/anomalies/{id}', desc: 'Get single anomaly metadata with SADH metrics' },
    { method: 'GET', path: '/api/reports', desc: 'Paginated list of mission hydrographic reports' },
    { method: 'GET', path: '/api/reports/{id}', desc: 'Single mission report detail' },
    { method: 'GET', path: '/api/runs', desc: 'Inference and pipeline run history' },
    { method: 'GET', path: '/api/runs/{id}', desc: 'Single run detail with georeferenced coordinates' },
    { method: 'GET', path: '/api/export/dossier', desc: 'Generate multi-page Naval PDF Dossier' },
    { method: 'GET', path: '/api/export/geojson', desc: 'Export detections as standard GeoJSON feature collection' },
    { method: 'GET', path: '/api/export/swath', desc: 'Generate high-resolution GeoTIFF seafloor swath' },
    { method: 'GET', path: '/api/export/csv', desc: 'Export detection list in tabular CSV format' },
    { method: 'GET', path: '/api/export/detection/{id}', desc: 'Single target JSON / GeoJSON export' },
    { method: 'WS', path: '/api/waterfall', desc: 'WebSocket live acoustic ping streaming' },
  ];

  return (
    <>
      <Topbar activePage="api-docs" />

      <div className="app-content" style={{ marginTop: '16px' }}>
        <div className="card-panel" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ margin: 0, fontSize: '20px', fontWeight: 800 }}>
              Live Swagger UI &amp; OpenAPI Spec
            </h2>
            <p style={{ margin: '4px 0 0', fontSize: '12px', color: 'var(--gesso-fg-muted)' }}>
              Auto-generated documentation generated directly by FastAPI backend
            </p>
          </div>
          <div style={{ display: 'flex', gap: '10px' }}>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              style={{
                padding: '8px 14px',
                background: 'var(--gesso-primary, #2e3700)',
                color: '#ffffff',
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: 600,
                textDecoration: 'none',
              }}
            >
              Open Swagger UI ↗
            </a>
            <a
              href="http://localhost:8000/redoc"
              target="_blank"
              rel="noreferrer"
              style={{
                padding: '8px 14px',
                background: 'var(--gesso-surface, #e7e5e7)',
                color: 'var(--gesso-fg, #1a1a1a)',
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: 600,
                textDecoration: 'none',
                border: '1px solid var(--gesso-divider, rgba(0,0,0,0.1))',
              }}
            >
              Open ReDoc ↗
            </a>
          </div>
        </div>

        {/* Quick API Reference Table */}
        <div className="card-panel">
          <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: 700 }}>
            Production Endpoints Reference
          </h3>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
              <thead>
                <tr style={{ background: 'var(--gesso-surface, #e7e5e7)', borderBottom: '1px solid var(--gesso-divider, rgba(0,0,0,0.1))' }}>
                  <th style={{ padding: '10px 14px', width: '90px' }}>Method</th>
                  <th style={{ padding: '10px 14px', width: '240px' }}>Endpoint</th>
                  <th style={{ padding: '10px 14px' }}>Description &amp; Specifications</th>
                </tr>
              </thead>
              <tbody>
                {endpoints.map((ep, i) => (
                  <tr
                    key={i}
                    style={{
                      borderBottom: '1px solid var(--gesso-divider, rgba(0,0,0,0.04))',
                      background: i % 2 === 0 ? 'var(--gesso-canvas, #ffffff)' : 'var(--gesso-surface-recessed, #fafafa)',
                    }}
                  >
                    <td style={{ padding: '10px 14px' }}>
                      <span
                        style={{
                          fontWeight: 700,
                          fontSize: '11px',
                          padding: '2px 6px',
                          borderRadius: '4px',
                          backgroundColor:
                            ep.method === 'POST'
                              ? '#dbeafe'
                              : ep.method === 'GET'
                              ? '#dcfce7'
                              : '#fef3c7',
                          color:
                            ep.method === 'POST'
                              ? '#1d4ed8'
                              : ep.method === 'GET'
                              ? '#15803d'
                              : '#b45309',
                        }}
                      >
                        {ep.method}
                      </span>
                    </td>
                    <td style={{ padding: '10px 14px', fontFamily: 'monospace', fontWeight: 600 }}>
                      {ep.path}
                    </td>
                    <td style={{ padding: '10px 14px', color: 'var(--gesso-fg-muted)' }}>
                      {ep.desc}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Interactive Embedded Docs */}
        <div className="card-panel" style={{ padding: 0, overflow: 'hidden' }}>
          <iframe
            src="http://localhost:8000/docs"
            title="FastAPI Swagger Documentation"
            style={{ width: '100%', height: '600px', border: 'none' }}
          />
        </div>
      </div>

      <Footer />
    </>
  );
}

import React, { useState } from 'react';
import './ReportExporter.css';

export default function ReportExporter({ runId, missionId = 'MSN-CURRENT', onExportComplete }) {
  const [downloading, setDownloading] = useState(null);
  const [statusMsg, setStatusMsg] = useState('');

  const handleDownload = async (type, endpoint, filename) => {
    try {
      setDownloading(type);
      setStatusMsg(`Generating ${type.toUpperCase()}...`);

      const queryParam = runId ? `?run_id=${encodeURIComponent(runId)}` : '';
      const url = `${endpoint}${queryParam}`;

      const res = await fetch(url);
      if (!res.ok) {
        throw new Error(`Export failed: ${res.statusText}`);
      }

      if (type === 'geojson') {
        const data = await res.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        triggerDownload(blob, filename);
      } else if (type === 'swath') {
        const data = await res.json();
        setStatusMsg(`GeoTIFF ready: ${data.file_name || 'swath.tif'}`);
        if (onExportComplete) onExportComplete(data);
      } else {
        const blob = await res.blob();
        triggerDownload(blob, filename);
      }

      setStatusMsg(`Successfully exported ${filename}`);
      setTimeout(() => setStatusMsg(''), 4000);
    } catch (err) {
      console.error(err);
      setStatusMsg(`Error: ${err.message}`);
    } finally {
      setDownloading(null);
    }
  };

  const triggerDownload = (blob, filename) => {
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="report-exporter-card">
      <div className="exporter-header">
        <div className="exporter-title-group">
          <span className="exporter-icon">📋</span>
          <div>
            <h3>TACTICAL MISSION EXPORT &amp; CLEARANCE</h3>
            <p className="exporter-subtitle">Mission: {missionId} | SIH-26057 Defense &amp; Salvage Standards</p>
          </div>
        </div>
      </div>

      <div className="exporter-actions-grid">
        {/* Naval PDF Dossier */}
        <div className="export-action-item">
          <div className="action-info">
            <span className="format-badge pdf">PDF</span>
            <div>
              <h4>Naval Salvage Dossier</h4>
              <p>Official clearance brief for Indian Navy &amp; Coast Guard</p>
            </div>
          </div>
          <button
            className="export-btn btn-pdf"
            disabled={downloading !== null}
            onClick={() => handleDownload('pdf', '/api/export/dossier', `NAV_SALVAGE_${missionId}.pdf`)}
          >
            {downloading === 'pdf' ? 'Generating...' : 'Export Dossier'}
          </button>
        </div>

        {/* GeoJSON Feature Collection */}
        <div className="export-action-item">
          <div className="action-info">
            <span className="format-badge geojson">GEOJSON</span>
            <div>
              <h4>GIS Vector Points</h4>
              <p>WGS84 points for QGIS, ArcGIS, and ECDIS systems</p>
            </div>
          </div>
          <button
            className="export-btn btn-geojson"
            disabled={downloading !== null}
            onClick={() => handleDownload('geojson', '/api/export/geojson', `targets_${missionId}.geojson`)}
          >
            {downloading === 'geojson' ? 'Extracting...' : 'Export GeoJSON'}
          </button>
        </div>

        {/* GeoTIFF Swath Mosaic */}
        <div className="export-action-item">
          <div className="action-info">
            <span className="format-badge geotiff">TIFF</span>
            <div>
              <h4>GeoTIFF Swath Mosaic</h4>
              <p>Georeferenced acoustic swath raster (EPSG:4326)</p>
            </div>
          </div>
          <button
            className="export-btn btn-geotiff"
            disabled={downloading !== null}
            onClick={() => handleDownload('swath', '/api/export/swath', `swath_${missionId}.tif`)}
          >
            {downloading === 'swath' ? 'Mosaicing...' : 'Generate Raster'}
          </button>
        </div>

        {/* CSV Target Log */}
        <div className="export-action-item">
          <div className="action-info">
            <span className="format-badge csv">CSV</span>
            <div>
              <h4>Acoustic Target Ledger</h4>
              <p>Tabular dataset with physics metrics and WGS84 fixes</p>
            </div>
          </div>
          <button
            className="export-btn btn-csv"
            disabled={downloading !== null}
            onClick={() => handleDownload('csv', '/api/export/detections/csv', `targets_${missionId}.csv`)}
          >
            {downloading === 'csv' ? 'Exporting...' : 'Export CSV'}
          </button>
        </div>

        {/* OGC KML 2.2 for Google Earth / ECDIS */}
        <div className="export-action-item">
          <div className="action-info">
            <span className="format-badge kml" style={{ background: '#0284c7', color: '#fff' }}>KML</span>
            <div>
              <h4>Google Earth / ECDIS (KML)</h4>
              <p>3D placemarks with threat balloons for navigation consoles</p>
            </div>
          </div>
          <button
            className="export-btn btn-kml"
            style={{ background: '#0284c7', color: '#fff' }}
            disabled={downloading !== null}
            onClick={() => handleDownload('kml', '/api/export/kml', `targets_${missionId}.kml`)}
          >
            {downloading === 'kml' ? 'Exporting...' : 'Export KML'}
          </button>
        </div>

        {/* Naval Salvage Mission Plan */}
        <div className="export-action-item">
          <div className="action-info">
            <span className="format-badge plan" style={{ background: '#7c3aed', color: '#fff' }}>PLAN</span>
            <div>
              <h4>Salvage Route &amp; Trajectory</h4>
              <p>Risk-ranked recovery sequence with nautical clearance corridor</p>
            </div>
          </div>
          <button
            className="export-btn btn-plan"
            style={{ background: '#7c3aed', color: '#fff' }}
            disabled={downloading !== null}
            onClick={() => handleDownload('geojson', '/api/salvage/route', `salvage_plan_${missionId}.json`)}
          >
            {downloading === 'geojson' ? 'Optimizing...' : 'Generate Plan'}
          </button>
        </div>
      </div>

      {statusMsg && <div className="export-status-banner">{statusMsg}</div>}
    </div>
  );
}

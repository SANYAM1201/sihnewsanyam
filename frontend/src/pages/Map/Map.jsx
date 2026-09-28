import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import Topbar from '../../components/Topbar/Topbar'
import GeoMap from '../../components/GeoMap/GeoMap'
import { listMapPoints, listReports, listRuns } from '../../api/client'
import styles from './Map.module.css'

function formatCoord(value) {
  const n = Number(value)
  return Number.isFinite(n) ? n.toFixed(5) : '—'
}

function getRiskClass(risk, s) {
  const r = (risk || '').toLowerCase()
  if (r === 'high' || r === 'critical') return s.riskHigh
  if (r === 'medium') return s.riskMedium
  return s.riskLow
}

export default function Map() {
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const runFromUrl = params.get('run') || ''

  const [runs, setRuns] = useState([])
  const [reports, setReports] = useState([])         // only original (non-instance) reports
  const [anomalies, setAnomalies] = useState([])     // all map points from /api/map/points

  const [selectedRunId, setSelectedRunId] = useState(runFromUrl)
  const [selectedPointId, setSelectedPointId] = useState('')
  const [basemap, setBasemap] = useState('satellite')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  // ── Load data ─────────────────────────────────────────────────────────────
  useEffect(() => {
    let cancelled = false
    setLoading(true)
    Promise.all([
      listRuns({ pageSize: 100 }),
      listReports({ page: 1, pageSize: 100 }),
      listMapPoints({ pageSize: 100 }),
    ])
      .then(([runData, reportData, mapData]) => {
        if (cancelled) return
        const runItems = runData.items || []
        const reportItems = (reportData.items || []).filter(r => r.kind !== 'instance')
        const mapItems = mapData.items || []

        setRuns(runItems)
        setReports(reportItems)
        setAnomalies(mapItems)

        // Auto-select: prefer URL param, then last used, then first
        const preferred = runFromUrl || localStorage.getItem('lastRunId') || runItems[0]?.run_id || ''
        const valid = runItems.some(r => r.run_id === preferred)
          ? preferred
          : (runItems[0]?.run_id || '')
        setSelectedRunId(valid)
        setLoading(false)
      })
      .catch(err => {
        if (!cancelled) {
          setError(err.message || 'Unable to load map data.')
          setLoading(false)
        }
      })
    return () => { cancelled = true }
  }, [runFromUrl])

  // ── Derived data ──────────────────────────────────────────────────────────
  const selectedRun  = runs.find(r => r.run_id === selectedRunId)
  const selectedReport = reports.find(r => r.run_id === selectedRunId)

  // All anomaly points that belong to the active run
  const activePoints = useMemo(() => {
    if (!selectedRunId) return []
    return anomalies
      .filter(a => a.run_id === selectedRunId)
      .map((a, idx) => ({
        id: a.id,
        serial: idx + 1,
        lat: a.latitude,
        lng: a.longitude,
        title: a.class_label,
        riskLevel: a.risk_level,
        confidence: a.confidence,
        depth: a.depth_m,
        runId: a.run_id,
        missionId: a.mission_id,
        detail: a.filename,
        isMission: false,
        geotiff_available: true,
      }))
  }, [anomalies, selectedRunId])

  // ── Handlers ──────────────────────────────────────────────────────────────
  function selectReport(run) {
    setSelectedRunId(run.run_id)
    setSelectedPointId('')
    setParams({ run: run.run_id }, { replace: true })
    localStorage.setItem('lastRunId', run.run_id)
  }

  function handleSelectPoint(pointId) {
    setSelectedPointId(prev => prev === pointId ? '' : pointId)
  }

  function openResults(runId, threshold) {
    const id = runId || selectedRunId
    if (!id) return
    const qs = threshold != null ? `?threshold=${threshold}` : ''
    navigate(`/results/${id}${qs}`)
  }

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <>
      <Topbar activePage="map" />
      <main className={styles.page}>

        {/* ── LEFT PANEL ─────────────────────────────────────────────────── */}
        <aside className={styles.sidebar}>
          {/* Header */}
          <div className={styles.sidebarHeader}>
            <h1 className={styles.sidebarTitle}>Detection Map</h1>
            <p className={styles.sidebarSub}>
              Select a report to view its detected objects on the map.
            </p>
          </div>

          {/* Basemap toggle */}
          <div className={styles.basemap}>
            <button
              type="button"
              className={basemap === 'satellite' ? styles.layerOn : styles.layer}
              onClick={() => setBasemap('satellite')}
            >
              Satellite
            </button>
            <button
              type="button"
              className={basemap === 'streets' ? styles.layerOn : styles.layer}
              onClick={() => setBasemap('streets')}
            >
              Streets
            </button>
          </div>

          {error && <div className={styles.error}>{error}</div>}

          {/* Reports numbered list */}
          <div className={styles.reportListWrap}>
            <div className={styles.listLabel}>
              Reports&nbsp;
              <span className={styles.listCount}>({reports.length})</span>
            </div>

            {loading ? (
              <p className={styles.empty}>Loading reports…</p>
            ) : reports.length === 0 ? (
              <p className={styles.empty}>No reports found.</p>
            ) : (
              <ul className={styles.reportList}>
                {reports.map((rep, idx) => {
                  const run = runs.find(r => r.run_id === rep.run_id)
                  const isActive = rep.run_id === selectedRunId
                  const count = anomalies.filter(a => a.run_id === rep.run_id).length

                  return (
                    <li key={rep.report_id}>
                      <button
                        type="button"
                        className={`${styles.reportCard} ${isActive ? styles.reportCardActive : ''}`}
                        onClick={() => selectReport(run || { run_id: rep.run_id })}
                      >
                        {/* Serial badge */}
                        <span className={`${styles.serial} ${isActive ? styles.serialActive : ''}`}>
                          {String(idx + 1).padStart(2, '0')}
                        </span>

                        {/* Main content */}
                        <div className={styles.reportCardBody}>
                          <div className={styles.reportCardTop}>
                            <span className={styles.reportName}>
                              {rep.mission_name || rep.mission_id}
                            </span>
                            <span className={styles.detectionBadge}>
                              {count} object{count !== 1 ? 's' : ''}
                            </span>
                          </div>
                          <span className={styles.reportMeta}>
                            {rep.mission_id}
                            {rep.scan_date ? ` · ${rep.scan_date}` : ''}
                          </span>
                          <span className={styles.reportCoords}>
                            {formatCoord(run?.latitude)}, {formatCoord(run?.longitude)}
                          </span>
                        </div>
                      </button>
                    </li>
                  )
                })}
              </ul>
            )}
          </div>

          {/* Active report: detected instances panel */}
          {selectedRunId && activePoints.length > 0 && (
            <div className={styles.instancePanel}>
              <div className={styles.instancePanelHeader}>
                <span className={styles.listLabel}>
                  Detected Objects&nbsp;
                  <span className={styles.listCount}>({activePoints.length})</span>
                </span>
                {selectedReport && (
                  <button
                    type="button"
                    className={styles.viewResultsBtn}
                    onClick={() => openResults(selectedRunId)}
                  >
                    View Scan →
                  </button>
                )}
              </div>

              <ul className={styles.instanceList}>
                {activePoints.map(pt => (
                  <li key={pt.id}>
                    <button
                      type="button"
                      className={`${styles.instanceItem} ${pt.id === selectedPointId ? styles.instanceItemActive : ''}`}
                      onClick={() => handleSelectPoint(pt.id)}
                    >
                      <span className={styles.instanceSerial}>{pt.serial}</span>
                      <div className={styles.instanceBody}>
                        <div className={styles.instanceTop}>
                          <span className={styles.instanceName}>{pt.title}</span>
                          <span className={`${styles.riskPill} ${getRiskClass(pt.riskLevel, styles)}`}>
                            {pt.riskLevel || 'N/A'}
                          </span>
                        </div>
                        <span className={styles.instanceCoords}>
                          {formatCoord(pt.lat)}, {formatCoord(pt.lng)}
                          {pt.confidence != null ? ` · ${Math.round(pt.confidence * 100)}% conf` : ''}
                          {pt.depth != null ? ` · ${pt.depth}m` : ''}
                        </span>
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {selectedRunId && activePoints.length === 0 && !loading && (
            <p className={styles.empty} style={{ marginTop: 8 }}>
              No georeferenced objects found for this report.
            </p>
          )}
        </aside>

        {/* ── MAP ──────────────────────────────────────────────────────────── */}
        <section className={styles.mapCol} aria-label="Geographic map of sonar detections">
          <GeoMap
            points={activePoints}
            selectedId={selectedPointId}
            onSelect={handleSelectPoint}
            onOpenResults={openResults}
            basemap={basemap}
            detections={activePoints}
          />
        </section>
      </main>
    </>
  )
}

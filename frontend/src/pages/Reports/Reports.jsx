import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Topbar from '../../components/Topbar/Topbar'
import { deleteReport, getRun, listReports } from '../../api/client'
import { exportReportsCsv, exportRunCsv } from '../../utils/exportReport'
import ReportExporter from '../../components/Reports/ReportExporter'
import PDFPreview from '../../components/Reports/PDFPreview'
import GeoJSONViewer from '../../components/Reports/GeoJSONViewer'
import styles from './Reports.module.css'

const STATUS_TABS = ['All', 'Reviewed', 'Pending', 'Flagged']
const ROWS_PER_PAGE = 8

const STATUS_CLASS = {
  Reviewed: 'statusReviewed',
  Pending: 'statusPending',
  Flagged: 'statusFlagged',
  Processing: 'statusProcessing',
  Instance: 'statusReviewed',
}

function uiStatus(row) {
  if ((row.kind || '') === 'instance' || (row.status || '').toLowerCase() === 'instance') {
    return 'Instance'
  }
  const raw = (row.status || '').toLowerCase()
  if (raw === 'processing') return 'Processing'
  if (raw === 'pending') return 'Pending'
  if (raw === 'flagged' || (row.high_risk_count || 0) > 0) return 'Flagged'
  return 'Reviewed'
}

function barsFor(row) {
  const high = Math.min(20, 4 + (row.high_risk_count || 0) * 3)
  const med = Math.min(20, 3 + (row.medium_risk_count || 0) * 2)
  const low = Math.min(20, 2 + (row.low_risk_count || 0) * 2)
  return [
    { h: high, fill: 'var(--gesso-data-1)' },
    { h: med, fill: 'var(--gesso-data-2)' },
    { h: low, fill: 'var(--gesso-data-3)' },
    { h: Math.max(2, Math.round((row.anomaly_count || 0) / 2)), fill: 'var(--gesso-data-4)' },
    { h: 4, fill: 'var(--gesso-data-5)' },
    { h: 6, fill: 'var(--gesso-data-2)' },
    { h: 3, fill: 'var(--gesso-data-6)' },
  ]
}

function WavesIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 6c.6.5 1.2 1 2.5 1C7 7 7 5 9.5 5c2.6 0 2.4 2 5 2c2.5 0 2.5-2 5-2c1.3 0 1.9.5 2.5 1M2 12c.6.5 1.2 1 2.5 1c2.5 0 2.5-2 5-2c2.6 0 2.4 2 5 2c2.5 0 2.5-2 5-2c1.3 0 1.9.5 2.5 1M2 18c.6.5 1.2 1 2.5 1c2.5 0 2.5-2 5-2c2.6 0 2.4 2 5 2c2.5 0 2.5-2 5-2c1.3 0 1.9.5 2.5 1" />
    </svg>
  )
}

function SearchIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <g><path d="m21 21l-4.34-4.34" /><circle cx="11" cy="11" r="8" /></g>
    </svg>
  )
}

function CalendarIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <g><path d="M8 2v4m8-4v4" /><rect width="18" height="18" x="3" y="4" rx="2" /><path d="M3 10h18" /></g>
    </svg>
  )
}

function MapPinIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <g><path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0" /><circle cx="12" cy="10" r="3" /></g>
    </svg>
  )
}

function ChevronDownIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="m6 9l6 6l6-6" />
    </svg>
  )
}

function ChevronLeftIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="m15 18l-6-6l6-6" />
    </svg>
  )
}

function ChevronRightIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="m9 18l6-6l-6-6" />
    </svg>
  )
}

function EyeIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <g><path d="M2.062 12.348a1 1 0 0 1 0-.696a10.75 10.75 0 0 1 19.876 0a1 1 0 0 1 0 .696a10.75 10.75 0 0 1-19.876 0" /><circle cx="12" cy="12" r="3" /></g>
    </svg>
  )
}

function DownloadIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <g><path d="M12 15V3m9 12v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><path d="m7 10l5 5l5-5" /></g>
    </svg>
  )
}

function TrashIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 6h18M8 6V4h8v2m-1 0v14a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2V6h10" />
    </svg>
  )
}

function ExportSelectedIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <g><path d="M12 15V3m9 12v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><path d="m7 10l5 5l5-5" /></g>
    </svg>
  )
}

function CapsuleBars({ bars }) {
  const totalHeight = 20
  const barWidth = 4
  const gap = 2
  return (
    <svg className={styles.capsuleBars} width="40" height={totalHeight} viewBox={`0 0 40 ${totalHeight}`} aria-hidden="true">
      {bars.map((bar, i) => (
        <rect
          key={i}
          x={i * (barWidth + gap)}
          y={totalHeight - bar.h}
          width={barWidth}
          height={bar.h}
          rx={2}
          fill={bar.fill}
        />
      ))}
    </svg>
  )
}

export default function Reports() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('All')
  const [currentPage, setCurrentPage] = useState(1)
  const [reports, setReports] = useState([])
  const [loadError, setLoadError] = useState('')
  const [selectedIds, setSelectedIds] = useState(new Set())

  useEffect(() => {
    listReports({ page: 1, pageSize: 100, search: search.trim() || undefined })
      .then((data) => {
        setReports(data.items || [])
        setLoadError('')
        setSelectedIds(prev => {
          const next = new Set(prev)
          const validIds = new Set((data.items || []).map(r => r.report_id))
          for (const id of next) if (!validIds.has(id)) next.delete(id)
          return next
        })
      })
      .catch((err) => setLoadError(err.message || 'Unable to load reports.'))
  }, [search])

  const mapped = useMemo(
    () => reports.map((row) => ({
      ...row,
      id: row.mission_id,
      name: row.mission_name,
      date: row.scan_date,
      anomalies: row.anomaly_count,
      status: uiStatus(row),
      confidence: row.confidence == null ? null : Math.round(row.confidence),
      bars: barsFor(row),
    })),
    [reports],
  )

  const filtered = useMemo(() => {
    if (statusFilter === 'All') return mapped
    return mapped.filter((r) => r.status === statusFilter)
  }, [mapped, statusFilter])

  const totalPages = Math.max(1, Math.ceil(filtered.length / ROWS_PER_PAGE))
  const safePage = Math.min(currentPage, totalPages)
  const startIdx = (safePage - 1) * ROWS_PER_PAGE
  const pageRows = filtered.slice(startIdx, startIdx + ROWS_PER_PAGE)
  const from = startIdx + 1
  const to = Math.min(startIdx + ROWS_PER_PAGE, filtered.length)
  const flagged = mapped.filter((r) => r.status === 'Flagged').length
  const pending = mapped.filter((r) => r.status === 'Pending' || r.status === 'Processing').length

  async function downloadRow(row) {
    const run = await getRun(row.run_id)
    exportRunCsv(run)
  }

  function downloadFiltered() {
    if (selectedIds.size > 0) {
      exportReportsCsv(mapped.filter(r => selectedIds.has(r.report_id)))
      return
    }
    if (!mapped.length) return
    exportReportsCsv(statusFilter === 'All' ? mapped : filtered)
  }

  async function handleDelete(row) {
    const label = row.kind === 'instance' ? row.name : row.name
    if (!window.confirm(`Delete ${label}?`)) return
    await deleteReport(row.report_id)
    listReports({ page: 1, pageSize: 100, search: search.trim() || undefined })
      .then((data) => setReports(data.items || []))
  }

  async function handleBulkDelete() {
    if (selectedIds.size === 0) return
    if (!window.confirm(`Delete ${selectedIds.size} selected report(s)?`)) return
    await Promise.all(Array.from(selectedIds).map(id => deleteReport(id)))
    setSelectedIds(new Set())
    listReports({ page: 1, pageSize: 100, search: search.trim() || undefined })
      .then((data) => setReports(data.items || []))
  }

  const allSelected = filtered.length > 0 && selectedIds.size === filtered.length
  function toggleAll() {
    if (allSelected) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(filtered.map(r => r.report_id)))
    }
  }

  function toggleOne(event, reportId) {
    event.stopPropagation()
    const next = new Set(selectedIds)
    if (next.has(reportId)) next.delete(reportId)
    else next.add(reportId)
    setSelectedIds(next)
  }

  return (
    <>
      <Topbar activePage="reports" />
      <div className={styles.wrap}>
        <div className={styles.headerBand}>
          <div className={styles.headerTop}>
            <div>
              <h1 className={styles.pageTitle}>Reports</h1>
              <p className={styles.pageSub}>Generated mission reports across all detection runs</p>
            </div>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              {selectedIds.size > 0 && (
                <button className={`${styles.btnPrimary} ${styles.btnDanger || ''}`} type="button" onClick={handleBulkDelete}>
                  <TrashIcon />
                  Delete selected
                </button>
              )}
              <button className={styles.btnPrimary} type="button" onClick={downloadFiltered} disabled={!filtered.length && selectedIds.size === 0}>
                <ExportSelectedIcon />
                Export selected
              </button>
            </div>
          </div>

          <div className={styles.statusRow}>
            <div className={styles.statusItem}>
              <span className={styles.statusVal}>{mapped.length}</span>
              <span className={styles.statusLbl}>Total reports</span>
            </div>
            <div className={styles.statusItem}>
              <span className={styles.statusVal}>{flagged}</span>
              <span className={styles.statusLbl}>Flagged for review</span>
            </div>
            <div className={styles.statusItem}>
              <span className={styles.statusVal}>{pending}</span>
              <span className={styles.statusLbl}>Pending analysis</span>
            </div>
            <div className={styles.statusItem}>
              <span className={styles.statusVal}>{mapped.length}</span>
              <span className={styles.statusLbl}>Stored locally</span>
            </div>
          </div>

          <div className={styles.toolbar}>
            <div className={styles.searchField}>
              <SearchIcon />
              <input
                type="text"
                placeholder="Search mission name or scan ID…"
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value)
                  setCurrentPage(1)
                }}
              />
            </div>
            <div className={styles.seg} role="tablist" aria-label="Status filter">
              {STATUS_TABS.map((tab) => (
                <button
                  key={tab}
                  role="tab"
                  aria-selected={statusFilter === tab}
                  className={styles.segBtn}
                  onClick={() => {
                    setStatusFilter(tab)
                    setCurrentPage(1)
                  }}
                >
                  {tab}
                </button>
              ))}
            </div>
            <div className={styles.selectChip}>
              <CalendarIcon />
              All dates
              <ChevronDownIcon />
            </div>
            <div className={styles.selectChip}>
              <MapPinIcon />
              All regions
              <ChevronDownIcon />
            </div>
            <div className={styles.toolbarSpacer} />
            <span className={styles.resultCount}>{filtered.length} reports</span>
          </div>
        </div>

        {loadError ? <p>{loadError}</p> : null}

        <div className={styles.tableWrap}>
          <table>
            <thead>
              <tr>
                <th style={{ width: '40px', textAlign: 'center' }}>
                  <input 
                    type="checkbox" 
                    checked={allSelected} 
                    onChange={toggleAll}
                    aria-label="Select all"
                  />
                </th>
                <th className={styles.sortable}>
                  <span className={styles.thInner}>Mission <ChevronDownIcon /></span>
                </th>
                <th className={styles.sortable}>
                  <span className={styles.thInner}>Scan date <ChevronDownIcon /></span>
                </th>
                <th className={styles.sortable}>
                  <span className={styles.thInner}>Anomalies <ChevronDownIcon /></span>
                </th>
                <th>Status</th>
                <th className={styles.sortable}>
                  <span className={styles.thInner}>Confidence <ChevronDownIcon /></span>
                </th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {pageRows.map((row) => (
                <tr key={row.report_id}>
                  <td style={{ textAlign: 'center' }} onClick={e => e.stopPropagation()}>
                    <input 
                      type="checkbox" 
                      checked={selectedIds.has(row.report_id)} 
                      onChange={(e) => toggleOne(e, row.report_id)}
                      aria-label={`Select ${row.id}`}
                    />
                  </td>
                  <td>
                    <div className={styles.missionCell}>
                      <div className={styles.missionIcon}><WavesIcon /></div>
                      <div className={styles.missionTxt}>
                        <span className={styles.missionName}>{row.name}</span>
                        <span className={styles.missionCode}>{row.id}</span>
                      </div>
                    </div>
                  </td>
                  <td className={styles.cellDate}>{row.date}</td>
                  <td>
                    <div className={styles.anomalyCell}>
                      <span className={styles.anomalyCount}>{row.anomalies}</span>
                      <CapsuleBars bars={row.bars} />
                    </div>
                  </td>
                  <td>
                    <span className={`${styles.statusBadge} ${styles[STATUS_CLASS[row.status]]}`}>
                      <span className={styles.dot} />
                      {row.status}
                    </span>
                  </td>
                  <td>
                    <div className={styles.confidenceCell}>
                      <div className={styles.confidenceTrack}>
                        <div className={styles.confidenceFill} style={{ width: row.confidence !== null ? `${row.confidence}%` : '0%' }} />
                      </div>
                      <span className={styles.confidenceVal}>{row.confidence !== null ? `${row.confidence}%` : '—'}</span>
                    </div>
                  </td>
                  <td>
                    <div className={styles.rowActions}>
                      <button
                        className={styles.actionBtn}
                        aria-label="Open report"
                        disabled={row.status === 'Processing'}
                        onClick={() => {
                          const threshold = row.confidence_threshold
                          const qs = threshold != null ? `?threshold=${threshold}` : ''
                          navigate(`/results/${row.run_id}${qs}`)
                        }}
                      >
                        <EyeIcon />
                      </button>
                      <button
                        className={`${styles.actionBtn} ${styles.actionBtnExport}`}
                        aria-label="Export report"
                        disabled={row.status === 'Processing'}
                        onClick={() => downloadRow(row)}
                      >
                        <DownloadIcon />
                      </button>
                      <button
                        className={styles.actionBtn}
                        aria-label="Delete report"
                        onClick={() => handleDelete(row)}
                      >
                        <TrashIcon />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className={styles.pagination}>
          <span className={styles.paginationCount}>
            Showing {filtered.length > 0 ? from : 0}–{to} of {filtered.length} reports
          </span>
          <div className={styles.pagerControls}>
            <button
              className={styles.pagerBtn}
              aria-label="Previous page"
              disabled={safePage <= 1}
              onClick={() => setCurrentPage(Math.max(1, safePage - 1))}
            >
              <ChevronLeftIcon />
            </button>
            <button
              className={styles.pagerBtn}
              aria-label="Next page"
              disabled={safePage >= totalPages}
              onClick={() => setCurrentPage(Math.min(totalPages, safePage + 1))}
            >
              <ChevronRightIcon />
            </button>
          </div>
        </div>

        {/* Advanced Multi-Format Dissemination Suite */}
        <div style={{ marginTop: '36px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ background: 'var(--gesso-surface, #e7e5e7)', padding: '20px', borderRadius: '10px', border: '1px solid var(--gesso-divider)' }}>
            <h3 style={{ margin: '0 0 12px 0', fontSize: '16px', fontWeight: 700 }}>
              Official Hydrographic Dissemination Suite
            </h3>
            <ReportExporter runId="active" />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
            <PDFPreview reportId="1" missionName="MSN-3D02 Sagar Nidhi Hydrographic Survey" />
            <GeoJSONViewer geojsonUrl="/api/export/geojson" />
          </div>
        </div>
      </div>
    </>
  )
}

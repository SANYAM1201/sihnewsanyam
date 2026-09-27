export function downloadTextFile(filename, contents, mime = 'text/plain;charset=utf-8') {
  const blob = new Blob([contents], { type: mime })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

function csvEscape(value) {
  const text = value == null ? '' : String(value)
  if (/[",\n\r]/.test(text)) return `"${text.replaceAll('"', '""')}"`
  return text
}

export function toCsv(headers, rows) {
  const lines = [headers.map(csvEscape).join(',')]
  for (const row of rows) {
    lines.push(headers.map((key) => csvEscape(row[key])).join(','))
  }
  return `${lines.join('\n')}\n`
}

export function exportRunCsv(run) {
  const meta = run.scan_metadata || {}
  const detections = run.detections || []
  const headers = [
    'mission_id',
    'run_id',
    'filename',
    'latitude',
    'longitude',
    'sonar_type',
    'detection_id',
    'class_label',
    'confidence_pct',
    'risk_level',
    'depth_m',
    'area_m2',
    'sadh_height_m',
    'physics_confidence_pct',
    'bbox_x',
    'bbox_y',
    'bbox_width',
    'bbox_height',
  ]
  const rows = (detections.length ? detections : [{}]).map((d) => ({
    mission_id: run.mission_id,
    run_id: run.run_id,
    filename: meta.filename || run.filename,
    latitude: meta.latitude,
    longitude: meta.longitude,
    sonar_type: meta.sonar_type,
    detection_id: d.detection_id || '',
    class_label: d.class_label || '',
    confidence_pct: d.confidence == null ? '' : Math.round(d.confidence * 100),
    risk_level: d.risk_level || '',
    depth_m: d.depth_m ?? '',
    area_m2: d.area_m2 ?? '',
    sadh_height_m: d.sadh_height_m != null ? d.sadh_height_m.toFixed(2) : '',
    physics_confidence_pct: d.physics_confidence != null ? Math.round(d.physics_confidence * 100) : '',
    bbox_x: d.bbox?.x ?? '',
    bbox_y: d.bbox?.y ?? '',
    bbox_width: d.bbox?.width ?? '',
    bbox_height: d.bbox?.height ?? '',
  }))
  const id = run.mission_id || run.run_id || 'report'
  downloadTextFile(`${id}-detections.csv`, toCsv(headers, rows), 'text/csv;charset=utf-8')
}

export function exportReportsCsv(reports) {
  const headers = [
    'mission_id',
    'mission_name',
    'scan_date',
    'run_id',
    'report_id',
    'anomalies',
    'high_risk_count',
    'status',
    'confidence',
  ]
  const rows = reports.map((row) => ({
    mission_id: row.mission_id || row.id,
    mission_name: row.mission_name || row.name,
    scan_date: row.scan_date || row.date,
    run_id: row.run_id,
    report_id: row.report_id,
    anomalies: row.anomaly_count ?? row.anomalies,
    high_risk_count: row.high_risk_count ?? '',
    status: row.status,
    confidence: row.confidence ?? '',
  }))
  downloadTextFile('sonaris-reports.csv', toCsv(headers, rows), 'text/csv;charset=utf-8')
}

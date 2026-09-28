const API_BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options)
  let body = null
  try {
    body = await response.json()
  } catch {
    body = null
  }
  if (!response.ok) {
    const message = body?.error?.message || `Request failed (${response.status})`
    throw new Error(message)
  }
  return body
}

export function getHealth() {
  return request('/api/health')
}

export function listRuns({ page = 1, pageSize = 20, status } = {}) {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  })
  if (status) params.set('status', status)
  return request(`/api/runs?${params}`)
}

export function getRun(runId) {
  return request(`/api/runs/${runId}`)
}

export function runFileUrl(runId) {
  return `${API_BASE}/api/runs/${runId}/file`
}

export function detectScan(formData) {
  return request('/api/detect', { method: 'POST', body: formData })
}

export function listReports({
  page = 1,
  pageSize = 8,
  search,
  status,
} = {}) {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  })
  if (search) params.set('search', search)
  if (status) params.set('status', status)
  return request(`/api/reports?${params}`)
}

export function getReport(reportId) {
  return request(`/api/reports/${reportId}`)
}

export function getAnomalies() {
  return request('/api/anomalies')
}

export function listMapPoints() {
  return request('/api/map/points')
}

export function createReportInstance(runId, confidenceThreshold) {
  return request(`/api/runs/${runId}/instances`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ confidence_threshold: confidenceThreshold }),
  })
}

export function forgetLastScanIfRun(runId) {
  try {
    const last = JSON.parse(localStorage.getItem('sonarLastScan') || 'null')
    if (last?.runId === runId) localStorage.removeItem('sonarLastScan')
  } catch {
    /* ignore */
  }
}

export function deleteRun(runId) {
  return request(`/api/runs/${runId}`, { method: 'DELETE' })
}

export function deleteReport(reportId) {
  return request(`/api/reports/${reportId}`, { method: 'DELETE' })
}

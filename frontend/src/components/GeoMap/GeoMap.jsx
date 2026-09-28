import { useEffect, useState } from 'react'
import { CircleMarker, ImageOverlay, MapContainer, Polygon, Polyline, Popup, TileLayer, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import styles from './GeoMap.module.css'

const SATELLITE = {
  url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
  attribution: 'Tiles © Esri — Source: Esri, Maxar, Earthstar Geographics',
}

const STREETS = {
  url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
  attribution: '&copy; OpenStreetMap contributors',
}

const FALLBACK_CENTER = [13.0800, 80.3600]

// ⭐ NEW: Development mode mock overlay for testing
const DEV_MODE = import.meta.env.MODE === 'development'
const MOCK_OVERLAY = DEV_MODE ? {
  id: 'mock_swath',
  imageUrl: 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Indian_Ocean_location_map.svg/1024px-Indian_Ocean_location_map.svg.png',
  bounds: [[10.5, 80.0], [11.0, 80.5]], // Bay of Bengal test coordinates
  opacity: 0.7
} : null

function FlyTo({ lat, lng, zoom }) {
  const map = useMap()
  useEffect(() => {
    if (lat == null || lng == null) return
    map.flyTo([lat, lng], zoom ?? 16, { duration: 0.7 })
  }, [map, lat, lng, zoom])
  return null
}

function FitOrFocus({ points, selectedPoint }) {
  const map = useMap()
  const key = points.map((p) => `${p.lat},${p.lng}`).join('|')

  useEffect(() => {
    map.invalidateSize()
    if (selectedPoint) {
      return
    }
    if (points.length === 0) {
      map.setView(FALLBACK_CENTER, 11)
      return
    }
    if (points.length === 1) {
      map.setView([points[0].lat, points[0].lng], 15)
      return
    }
    const validPoints = points.filter((p) => Number.isFinite(p.lat) && Number.isFinite(p.lng))
    if (validPoints.length > 0) {
      const bounds = L.latLngBounds(validPoints.map((p) => [p.lat, p.lng]))
      map.fitBounds(bounds.pad(0.2))
    }
  }, [map, key, selectedPoint, points])

  return null
}

function getMarkerColor(point) {
  if (point.color) return point.color
  if (point.isMission) return '#3b82f6'
  const risk = (point.riskLevel || '').toLowerCase()
  if (risk === 'critical' || risk === 'high') return '#ef4444'
  if (risk === 'medium') return '#f59e0b'
  if (risk === 'low') return '#10b981'
  return '#c45c26'
}

function getBadgeClass(point) {
  if (point.isMission) return styles.badgeMission
  const risk = (point.riskLevel || '').toLowerCase()
  if (risk === 'critical' || risk === 'high') return styles.badgeHigh
  if (risk === 'medium') return styles.badgeMedium
  if (risk === 'low') return styles.badgeLow
  return styles.badgeLow
}

// ⭐ NEW: Swath Overlay Control Component
function SwathOverlayControl({ swathOverlays, setSwathOverlays, showSwath, setShowSwath, opacity, setOpacity }) {
  return (
    <div className={styles.swathControl}>
      <div className={styles.controlGroup}>
        <label className={styles.controlLabel}>
          <input
            type="checkbox"
            checked={showSwath}
            onChange={(e) => setShowSwath(e.target.checked)}
            className={styles.controlCheckbox}
          />
          Show Sonar Swath
        </label>
      </div>
      <div className={styles.controlGroup}>
        <label className={styles.controlLabel}>
          Opacity: {Math.round(opacity * 100)}%
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={opacity}
            onChange={(e) => setOpacity(parseFloat(e.target.value))}
            className={styles.opacitySlider}
          />
        </label>
      </div>
    </div>
  )
}

export default function GeoMap({
  points = [],
  selectedId,
  onSelect,
  onOpenResults,
  basemap = 'satellite',
  swathPolygon = null,
  vesselTrack = null,
  detections = [], // ⭐ NEW: Add detections prop for GeoTIFF overlays
}) {
  const tile = basemap === 'streets' ? STREETS : SATELLITE
  const selected = points.find((p) => p.id === selectedId)

  // ⭐ NEW: State for swath overlays
  const [swathOverlays, setSwathOverlays] = useState([])
  const [showSwath, setShowSwath] = useState(true)
  const [opacity, setOpacity] = useState(0.7)

  // ⭐ NEW: Fetch GeoTIFF bounds for detections with geotiff_available flag
  useEffect(() => {
    const fetchSwathOverlays = async () => {
      const overlays = []

      // Add mock overlay in development mode
      if (DEV_MODE && MOCK_OVERLAY) {
        overlays.push(MOCK_OVERLAY)
      }

      // Fetch real overlays for detections with GeoTIFF
      for (const detection of detections) {
        if (detection.geotiff_available) {
          try {
            const response = await fetch(`/api/export/geotiff/${detection.id}/bounds`)
            if (response.ok) {
              const boundsData = await response.json()
              overlays.push({
                id: detection.id,
                imageUrl: boundsData.image_url || `/api/export/geotiff/${detection.id}/render`,
                bounds: [[boundsData.south, boundsData.west], [boundsData.north, boundsData.east]],
                opacity: opacity
              })
            }
          } catch (error) {
            console.debug(`Failed to fetch GeoTIFF bounds for detection ${detection.id}:`, error)
          }
        }
      }

      setSwathOverlays(overlays)
    }

    fetchSwathOverlays()
  }, [detections, opacity])

  // ⭐ NEW: Update opacity for all overlays when slider changes
  useEffect(() => {
    if (swathOverlays.length > 0) {
      setSwathOverlays(prev =>
        prev.map(overlay => ({ ...overlay, opacity }))
      )
    }
  }, [opacity])

  return (
    <div className={styles.mapShell}>
      <MapContainer
        className={styles.map}
        style={{ height: '100%', width: '100%' }}
        center={selected ? [selected.lat, selected.lng] : FALLBACK_CENTER}
        zoom={selected ? 15 : 12}
        scrollWheelZoom
      >
        <TileLayer key={basemap} attribution={tile.attribution} url={tile.url} />
        <FitOrFocus points={points} selectedPoint={selected} />
        {selected ? <FlyTo lat={selected.lat} lng={selected.lng} zoom={16} /> : null}

        {swathPolygon && swathPolygon.length > 0 && (
          <Polygon
            positions={swathPolygon}
            pathOptions={{
              color: '#0284c7',
              weight: 2,
              fillColor: '#0284c7',
              fillOpacity: 0.18,
              dashArray: '5, 5',
            }}
          />
        )}
        {vesselTrack && vesselTrack.length > 1 && (
          <Polyline
            positions={vesselTrack}
            pathOptions={{
              color: '#38bdf8',
              weight: 3,
              opacity: 0.85,
            }}
          />
        )}

        {/* ⭐ NEW: ImageOverlay for Sonar Swath - Rendered after Polygon/Marker layers */}
        {showSwath && swathOverlays.map(overlay => (
          <ImageOverlay
            key={overlay.imageUrl}
            url={overlay.imageUrl}
            bounds={overlay.bounds}
            opacity={overlay.opacity}
            zIndex={10}
          />
        ))}

        {points.map((point) => {
          const active = point.id === selectedId
          const color = getMarkerColor(point)
          const radius = point.isMission ? (active ? 13 : 9) : (active ? 11 : 7)

          return (
            <CircleMarker
              key={point.id}
              center={[point.lat, point.lng]}
              radius={radius}
              pathOptions={{
                color: active ? '#ffffff' : 'rgba(255, 255, 255, 0.8)',
                weight: active ? 3 : 1.5,
                fillColor: color,
                fillOpacity: active ? 1 : 0.85,
              }}
              eventHandlers={{
                click: () => onSelect?.(point.id),
              }}
            >
              <Popup>
                <div className={styles.popup}>
                  <div className={styles.popupHeader}>
                    <span className={styles.popupTitle}>{point.title}</span>
                    <span className={`${styles.badge} ${getBadgeClass(point)}`}>
                      {point.isMission ? 'Survey Track' : `${point.riskLevel || 'Object'}`}
                    </span>
                  </div>

                  <div className={styles.popupDetails}>
                    {point.missionId ? (
                      <div className={styles.popupRow}>
                        <span>Mission:</span>
                        <strong>{point.missionId}</strong>
                      </div>
                    ) : null}
                    {point.confidence != null ? (
                      <div className={styles.popupRow}>
                        <span>Confidence:</span>
                        <strong>{Math.round(point.confidence * 100)}%</strong>
                      </div>
                    ) : null}
                    {point.depth != null ? (
                      <div className={styles.popupRow}>
                        <span>Depth:</span>
                        <strong>{point.depth} m</strong>
                      </div>
                    ) : null}
                    {point.detail ? (
                      <div className={styles.popupRow}>
                        <span>File:</span>
                        <span>{point.detail}</span>
                      </div>
                    ) : null}
                  </div>

                  <div className={styles.popupCoords}>
                    {point.lat.toFixed(6)}, {point.lng.toFixed(6)}
                  </div>

                  {point.runId && onOpenResults ? (
                    <button
                      type="button"
                      className={styles.popupBtn}
                      onClick={() => onOpenResults(point.runId, point.threshold)}
                    >
                      View Detection Scan →
                    </button>
                  ) : null}
                </div>
              </Popup>
            </CircleMarker>
          )
        })}

        {/* ⭐ NEW: Swath Overlay Control - Positioned in top-right */}
        <SwathOverlayControl
          swathOverlays={swathOverlays}
          setSwathOverlays={setSwathOverlays}
          showSwath={showSwath}
          setShowSwath={setShowSwath}
          opacity={opacity}
          setOpacity={setOpacity}
        />
      </MapContainer>

      <div className={styles.legendBox}>
        <div className={styles.legendTitle}>Map Legend</div>
        <div className={styles.legendItem}>
          <span className={styles.legendDot} style={{ background: '#ef4444' }} />
          <span>Critical / High Risk</span>
        </div>
        <div className={styles.legendItem}>
          <span className={styles.legendDot} style={{ background: '#f59e0b' }} />
          <span>Medium Risk</span>
        </div>
        <div className={styles.legendItem}>
          <span className={styles.legendDot} style={{ background: '#10b981' }} />
          <span>Low Risk</span>
        </div>
        <div className={styles.legendItem}>
          <span className={styles.legendDot} style={{ background: '#3b82f6' }} />
          <span>Survey Vessel Track</span>
        </div>
      </div>
    </div>
  )
}

import { useEffect } from 'react'
import { CircleMarker, MapContainer, Polygon, Polyline, Popup, TileLayer, useMap } from 'react-leaflet'
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

export default function GeoMap({
  points = [],
  selectedId,
  onSelect,
  onOpenResults,
  basemap = 'satellite',
  swathPolygon = null,
  vesselTrack = null,
}) {
  const tile = basemap === 'streets' ? STREETS : SATELLITE
  const selected = points.find((p) => p.id === selectedId)

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

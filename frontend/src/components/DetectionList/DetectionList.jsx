import styles from './DetectionList.module.css'

const riskStyles = {
  critical: styles.riskPillCritical,
  high: styles.riskPillHigh,
  medium: styles.riskPillMedium,
  low: styles.riskPillLow,
}

function getPhysicsStyle(confidence) {
  if (confidence == null) return styles.physicsPillLow
  if (confidence >= 0.75) return styles.physicsPillHigh
  if (confidence >= 0.5) return styles.physicsPillMedium
  return styles.physicsPillLow
}

function metaLine(d) {
  const parts = []
  if (d.depth_m != null) parts.push(`Depth ${d.depth_m} m`)
  if (d.area_m2 != null) parts.push(`${d.area_m2} m²`)
  if (d.sadh_height_m != null) parts.push(`Height ${d.sadh_height_m.toFixed(2)} m`)
  if (d.physics_confidence != null) parts.push(`Physics ${(d.physics_confidence * 100).toFixed(1)}%`)
  if (d.bbox) parts.push(`box ${Math.round(d.bbox.x)},${Math.round(d.bbox.y)}`)
  return parts.join(' · ') || 'No extra metadata'
}

export default function DetectionList({
  detections = [],
  selectedId,
  onSelect,
  threshold = 0,
  onThresholdChange,
  instanceNote = '',
}) {
  const pct = (threshold / 95) * 100

  return (
    <section className={styles.panel}>
      <div className={styles.listHeader}>
        <span className={styles.listHeader__label}>Detected objects</span>
        <span className={`${styles.listHeader__count} tabular`}>{detections.length} total</span>
      </div>

      <div className={styles.thresholdBlock}>
        <div className={styles.thresholdTop}>
          <span>Hide below threshold</span>
          <strong className="tabular">{threshold}%</strong>
        </div>
        <div className={styles.thresholdTrack}>
          <input
            type="range"
            min={0}
            max={95}
            value={threshold}
            aria-label="Confidence threshold"
            onChange={(e) => onThresholdChange?.(Number(e.target.value))}
          />
          <div className={styles.thresholdFill} style={{ width: `${pct}%` }} />
        </div>
        {instanceNote ? <p className={styles.instanceNote}>{instanceNote}</p> : null}
      </div>

      <div className={styles.detectList}>
        {detections.length === 0 ? (
          <div className={styles.detectRow}>
            <div className={styles.detectRow__text}>
              <span className={styles.detectRow__title}>No objects above the current threshold</span>
              <span className={styles.detectRow__meta}>Lower the threshold to show more findings.</span>
            </div>
          </div>
        ) : detections.map((d) => (
          <button
            type="button"
            key={d.detection_id}
            className={`${styles.detectRow} ${selectedId === d.detection_id ? styles.detectRowSelected : ''}`}
            onClick={() => onSelect?.(d.detection_id)}
          >
            <div className={styles.detectRow__left}>
              <span className={styles.detectRow__icon}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect width="18" height="18" x="3" y="3" rx="2" />
                </svg>
              </span>
              <div className={styles.detectRow__text}>
                <span className={styles.detectRow__title}>{d.class_label} — {d.detection_id.slice(0, 8)}</span>
                <span className={styles.detectRow__meta}>{metaLine(d)}</span>
                <div className={styles.detectRow__badges}>
                  {d.sadh_height_m != null && (
                    <span
                      className={styles.sadhBadge}
                      title="Shadow Acoustic Height (SADH): Estimated target height from acoustic shadow geometry"
                    >
                      📐 Height: {d.sadh_height_m.toFixed(2)} m
                    </span>
                  )}
                  {d.physics_confidence != null && (
                    <span
                      className={`${styles.physicsPill} ${getPhysicsStyle(d.physics_confidence)}`}
                      title="Physics Confidence: Multi-modal fusion of acoustic shadow length and sonar backscatter"
                    >
                      ⚡ Physics {(d.physics_confidence * 100).toFixed(1)}%
                    </span>
                  )}
                </div>
              </div>
            </div>
            <div className={styles.detectRow__right}>
              <span className={`${styles.riskPill} ${riskStyles[d.risk_level] || styles.riskPillLow}`}>
                {(d.risk_level || 'low').charAt(0).toUpperCase() + (d.risk_level || 'low').slice(1)}
              </span>
              <span className={`${styles.detectRow__conf} tabular`}>{Math.round((d.confidence || 0) * 100)}%</span>
            </div>
          </button>
        ))}
      </div>
    </section>
  )
}


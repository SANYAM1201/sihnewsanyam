import React from 'react'
import styles from './WaterfallPreview.module.css'

export default function WaterfallPreview({ waterfallData, metadata }) {
  if (!waterfallData) return null

  // Support base64 image or direct URL
  const src = waterfallData.startsWith('data:') || waterfallData.startsWith('http') || waterfallData.startsWith('/')
    ? waterfallData
    : `data:image/png;base64,${waterfallData}`

  const pingCount = metadata?.ping_count || metadata?.num_pings || 'Live'
  const frequency = metadata?.frequency ? `${metadata.frequency} kHz` : 'Side-Scan Sonar'
  const slantRange = metadata?.avg_slant_range_m ? `${metadata.avg_slant_range_m} m range` : 'Dual Channel'

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.title}>
          <span>Sonar Waterfall Sonogram</span>
          <span className={styles.badge}>XTF Hydrographic</span>
        </div>
        <span className={styles.meta}>
          {frequency} · {slantRange}
        </span>
      </div>

      <div className={styles.waterfallWrap}>
        <img src={src} alt="Reconstructed Sonar Waterfall" className={styles.waterfallImg} />
        <div className={styles.nadirLine} title="Nadir (Direct Nadir Track Line)" />
      </div>

      <div className={styles.footer}>
        <span>◄ PORT SWATH</span>
        <span>NADIR CENTER</span>
        <span>STARBOARD SWATH ►</span>
      </div>
      <div className={styles.footer}>
        <span>Pings: {pingCount}</span>
        <span>Resolution: calibrated acoustic sweep</span>
      </div>
    </div>
  )
}

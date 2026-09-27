import React, { useEffect, useRef } from 'react'
import useWaterfallStream from '../../hooks/useWaterfallStream'
import styles from './RealTimeWaterfall.module.css'

export default function RealTimeWaterfall({ wsUrl }) {
  const { waterfallData, detections, isConnected, latestPing, clearStream } = useWaterfallStream(wsUrl)
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    if (!waterfallData.length) {
      ctx.fillStyle = '#0a0d12'
      ctx.fillRect(0, 0, canvas.width, canvas.height)
      return
    }

    const nPings = waterfallData.length
    const nSamples = waterfallData[0]?.length || 512

    // Adapt internal canvas resolution to match sonar geometry
    if (canvas.width !== nSamples || canvas.height !== Math.max(nPings, 256)) {
      canvas.width = nSamples
      canvas.height = Math.max(nPings, 256)
    }

    const imgData = ctx.createImageData(canvas.width, canvas.height)
    const data = imgData.data

    // Clear buffer to black
    data.fill(0)

    for (let row = 0; row < nPings; row++) {
      const ping = waterfallData[row]
      const rowOffset = (canvas.height - nPings + row) * canvas.width * 4
      for (let col = 0; col < Math.min(ping.length, canvas.width); col++) {
        const val = ping[col] || 0
        const idx = rowOffset + col * 4

        // Apply sonar thermal colormap: bronze/copper palette
        data[idx] = Math.min(255, val * 1.1)      // R
        data[idx + 1] = Math.min(255, val * 0.85) // G
        data[idx + 2] = Math.min(255, val * 0.45) // B
        data[idx + 3] = 255                       // Alpha
      }
    }

    ctx.putImageData(imgData, 0, 0)

    // Draw Nadir track center line
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.25)'
    ctx.lineWidth = 1
    ctx.beginPath()
    ctx.moveTo(canvas.width / 2, 0)
    ctx.lineTo(canvas.width / 2, canvas.height)
    ctx.stroke()

    // Draw active bounding box overlays from streaming detections
    detections.slice(-20).forEach((det) => {
      if (!det.bbox) return
      const bx = det.bbox.x * canvas.width
      const by = det.bbox.y * canvas.height
      const bw = det.bbox.width * canvas.width
      const bh = det.bbox.height * canvas.height

      ctx.strokeStyle = det.risk_level === 'critical' ? '#ef4444' : '#eab308'
      ctx.lineWidth = 2
      ctx.strokeRect(bx, by, bw, bh)
    })
  }, [waterfallData, detections])

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.titleArea}>
          <h3 className={styles.title}>Real-Time Sonar Waterfall</h3>
          <span
            className={`${styles.liveBadge} ${
              isConnected ? styles.liveOnline : styles.liveOffline
            }`}
          >
            <span className={styles.liveDot} />
            {isConnected ? 'LIVE STREAM' : 'DISCONNECTED'}
          </span>
        </div>
        <div className={styles.controls}>
          <button type="button" className={styles.btnAction} onClick={clearStream}>
            Reset View
          </button>
        </div>
      </div>

      <div className={styles.canvasWrap}>
        <canvas ref={canvasRef} className={styles.canvas} width={1024} height={512} />
        {!waterfallData.length && (
          <div className={styles.emptyOverlay}>
            {isConnected
              ? 'Waiting for vessel acoustic pings via WebSocket /ws/waterfall...'
              : 'Connecting to WebSocket stream at ws://localhost:8000/ws/waterfall...'}
          </div>
        )}
      </div>

      <div className={styles.telemetryBar}>
        <span>
          Pings Received: <strong>{waterfallData.length}</strong>
        </span>
        {latestPing?.timestamp && <span>Latest: {latestPing.timestamp}</span>}
        <span>◄ PORT | NADIR | STBD ►</span>
      </div>
    </div>
  )
}

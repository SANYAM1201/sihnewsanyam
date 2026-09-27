import { useEffect, useState, useRef, useCallback } from 'react'

export default function useWaterfallStream(customUrl) {
  const [waterfallData, setWaterfallData] = useState([])
  const [detections, setDetections] = useState([])
  const [isConnected, setIsConnected] = useState(false)
  const [latestPing, setLatestPing] = useState(null)
  const ws = useRef(null)

  const defaultUrl = (() => {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    const wsProto = apiUrl.startsWith('https') ? 'wss:' : 'ws:'
    const host = apiUrl.replace(/^https?:\/\//, '')
    return `${wsProto}//${host}/ws/waterfall`
  })()

  const url = customUrl || import.meta.env.VITE_WS_URL || defaultUrl

  useEffect(() => {
    let reconnectTimer = null

    function connect() {
      try {
        ws.current = new WebSocket(url)

        ws.current.onopen = () => {
          setIsConnected(true)
        }

        ws.current.onclose = () => {
          setIsConnected(false)
          // Attempt automatic reconnect after 3 seconds
          reconnectTimer = setTimeout(connect, 3000)
        }

        ws.current.onerror = () => {
          setIsConnected(false)
        }

        ws.current.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            if (data.type === 'ping') {
              if (data.waterfall_chunk) {
                setWaterfallData((prev) => {
                  const updated = [...prev, data.waterfall_chunk]
                  // Keep last 500 pings in memory to prevent canvas memory overflow
                  return updated.slice(-500)
                })
              }
              if (data.detections && data.detections.length > 0) {
                setDetections((prev) => [...prev, ...data.detections])
              }
              setLatestPing(data)
            }
          } catch {
            // Ignore non-json or telemetry heartbeats
          }
        }
      } catch {
        setIsConnected(false)
      }
    }

    connect()

    return () => {
      clearTimeout(reconnectTimer)
      if (ws.current) {
        ws.current.onclose = null
        ws.current.close()
      }
    }
  }, [url])

  const clearStream = useCallback(() => {
    setWaterfallData([])
    setDetections([])
    setLatestPing(null)
  }, [])

  return { waterfallData, detections, isConnected, latestPing, clearStream }
}

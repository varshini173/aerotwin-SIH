import { useEffect, useRef, useState, useCallback } from 'react'
import { WS_URL } from '../services/api'

// Keeps a live-updating engine state object plus a bounded rolling history
// buffer (for charts) fed purely from WebSocket pushes. Reconnects
// automatically with backoff if the backend restarts.
export function useEngineSocket(historyLimit = 120) {
  const [state, setState] = useState(null)
  const [connected, setConnected] = useState(false)
  const [history, setHistory] = useState([])
  const wsRef = useRef(null)
  const retryRef = useRef(1000)

  const connect = useCallback(() => {
    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      retryRef.current = 1000
    }
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        setState(data)
        setHistory((prev) => {
          const next = [...prev, data]
          if (next.length > historyLimit) next.shift()
          return next
        })
      } catch (e) {
        // ignore malformed frame
      }
    }
    ws.onclose = () => {
      setConnected(false)
      setTimeout(connect, retryRef.current)
      retryRef.current = Math.min(retryRef.current * 1.5, 8000)
    }
    ws.onerror = () => {
      ws.close()
    }
  }, [historyLimit])

  useEffect(() => {
    connect()
    return () => {
      wsRef.current?.close()
    }
  }, [connect])

  return { state, connected, history }
}

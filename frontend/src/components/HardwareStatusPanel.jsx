import { useEffect, useState } from 'react'
import { api } from '../services/api'

// This project's hardware mode is set at backend startup (USE_HARDWARE=1
// env var), not switchable from the UI — so this panel is a read-only
// status display, polling GET /api/engine/hardware-status every couple
// seconds, rather than a connect/disconnect control.
export default function HardwareStatusPanel() {
  const [status, setStatus] = useState(null)

  useEffect(() => {
    const poll = () => api.getHardwareStatus().then(setStatus).catch(() => {})
    poll()
    const id = setInterval(poll, 2000)
    return () => clearInterval(id)
  }, [])

  if (!status) return null

  const isHardwareMode = status.mode === 'hardware'
  const connected = status.connected
  const ageSeconds = status.lastSampleTime ? (Date.now() / 1000 - status.lastSampleTime).toFixed(1) : null

  return (
    <div className="glass-card p-4">
      <div className="font-label-caps text-label-caps text-on-surface-variant mb-2 flex items-center gap-2">
        <span className="material-symbols-outlined text-[16px]">memory</span>
        HARDWARE STATUS
      </div>

      {!isHardwareMode && (
        <div className="font-body-md text-body-md text-on-surface-variant">
          Running on the <span className="text-primary">software simulator</span>. To read from your
          Arduino Uno + potentiometer, stop the backend and restart it with{' '}
          <code className="text-primary">USE_HARDWARE=1</code> set (see{' '}
          <code className="text-primary">hardware/README.md</code>), then run{' '}
          <code className="text-primary">serial_bridge/bridge.py</code>.
        </div>
      )}

      {isHardwareMode && (
        <div className="flex items-center justify-between">
          <span
            className={`px-2 py-1 rounded font-label-caps text-label-caps border flex items-center gap-2 ${
              connected ? 'text-secondary border-secondary bg-secondary/10' : 'text-error border-error bg-error/10'
            }`}
          >
            <span className={`w-2 h-2 rounded-full ${connected ? 'bg-secondary animate-pulse' : 'bg-error'}`}></span>
            {connected ? 'RECEIVING LIVE DATA' : 'NO DATA — start bridge.py'}
          </span>
          {ageSeconds !== null && (
            <span className="font-label-sm text-label-sm text-on-surface-variant">last sample {ageSeconds}s ago</span>
          )}
        </div>
      )}
    </div>
  )
}

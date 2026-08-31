import { useEffect, useState } from 'react'
import { api } from '../services/api'
import TimeSeriesChart from '../charts/TimeSeriesChart'

export default function History() {
  const [runs, setRuns] = useState([])
  const [selectedRun, setSelectedRun] = useState(null)
  const [samples, setSamples] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    api.getRuns().then((res) => {
      setRuns(res.runs || [])
      if (res.runs?.length) setSelectedRun(res.runs[0].run_id)
    })
  }, [])

  useEffect(() => {
    if (!selectedRun) return
    setLoading(true)
    api
      .getRunDetail(selectedRun)
      .then((res) => setSamples(res.samples || []))
      .finally(() => setLoading(false))
  }, [selectedRun])

  const chartData = samples.map((s, i) => ({ ...s, tick: i }))
  const final = samples[samples.length - 1]
  const majorAlerts = samples
    .flatMap((s) => s.alerts || [])
    .filter((a) => a.severity === 'CRITICAL' || a.severity === 'HIGH')
    .slice(-15)
    .reverse()

  return (
    <div className="flex flex-col gap-stack-md h-full">
      <div className="grid grid-cols-12 gap-gutter">
        <div className="col-span-3 glass-card p-4 flex flex-col gap-2 max-h-[600px] overflow-y-auto">
          <div className="font-label-caps text-label-caps text-on-surface-variant mb-2">RUN HISTORY</div>
          {runs.length === 0 && <div className="text-on-surface-variant text-body-md opacity-60">No runs yet.</div>}
          {runs.map((r) => (
            <button
              key={r.run_id}
              onClick={() => setSelectedRun(r.run_id)}
              className={`text-left p-2 rounded border font-label-sm text-label-sm transition-colors ${
                selectedRun === r.run_id
                  ? 'border-primary-container text-primary bg-primary-container/10'
                  : 'border-outline-variant text-on-surface-variant hover:bg-surface-container-highest'
              }`}
            >
              <div className="font-data-lg text-body-md">{r.run_id}</div>
              <div>{r.started_at}</div>
              <div>{r.final_status ? `Final: ${r.final_status}` : 'In progress'}</div>
            </button>
          ))}
        </div>

        <div className="col-span-9 flex flex-col gap-gutter">
          {loading && <div className="glass-card p-4 text-center text-on-surface-variant">Loading run…</div>}
          {!loading && final && (
            <>
              <div className="grid grid-cols-4 gap-gutter">
                <Stat label="FINAL HEALTH" value={`${final.health}%`} />
                <Stat label="FINAL STATUS" value={final.status} />
                <Stat label="FINAL FAULT" value={final.fault_type || 'NONE'} />
                <Stat label="SAMPLES" value={samples.length} />
              </div>

              <div className="grid grid-cols-2 gap-gutter">
                <TimeSeriesChart data={chartData} dataKey="temperature" label="TEMPERATURE (REPLAY)" color="#ffb95f" unit="°C" />
                <TimeSeriesChart data={chartData} dataKey="vibration" label="VIBRATION (REPLAY)" color="#ff8a80" unit=" mm/s" />
                <TimeSeriesChart data={chartData} dataKey="health" label="HEALTH (REPLAY)" color="#4edea3" unit="%" />
                <TimeSeriesChart data={chartData} dataKey="degradation" label="DEGRADATION (REPLAY)" color="#ffb4ab" unit="%" />
              </div>

              <div className="glass-card p-4">
                <div className="font-label-caps text-label-caps text-on-surface-variant mb-2">MAJOR ALERTS DURING RUN</div>
                <div className="space-y-1 max-h-48 overflow-y-auto">
                  {majorAlerts.length === 0 && (
                    <div className="text-on-surface-variant opacity-60 text-body-md">No major alerts recorded.</div>
                  )}
                  {majorAlerts.map((a, i) => (
                    <div key={i} className="flex gap-4 text-body-md text-error border-b border-surface-variant py-1">
                      <span className="opacity-70 w-20 shrink-0">[{a.timestamp}]</span>
                      <span>
                        {a.severity}: {a.message}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
          {!loading && !final && (
            <div className="glass-card p-8 text-center text-on-surface-variant">Select a run to view its replay.</div>
          )}
        </div>
      </div>
    </div>
  )
}

function Stat({ label, value }) {
  return (
    <div className="glass-card p-3 text-center">
      <div className="font-label-caps text-label-caps text-on-surface-variant">{label}</div>
      <div className="font-data-lg text-headline-md text-primary">{value}</div>
    </div>
  )
}

import { useEngineSocket } from '../hooks/useEngineSocket'
import DigitalTwinSVG from '../components/DigitalTwinSVG'
import MetricCard from '../components/MetricCard'

const STATUS_STYLES = {
  HEALTHY: 'text-secondary border-secondary bg-secondary/10',
  NORMAL: 'text-secondary border-secondary bg-secondary/10',
  DEGRADING: 'text-tertiary-fixed-dim border-tertiary-fixed-dim bg-tertiary-fixed-dim/10',
  WARNING: 'text-tertiary-fixed-dim border-tertiary-fixed-dim bg-tertiary-fixed-dim/10',
  CRITICAL: 'text-error border-error bg-error/10 glow-critical',
}

export default function DigitalTwin() {
  const { state } = useEngineSocket(60)
  const s = state || {}
  const badgeClass = STATUS_STYLES[s.status] || 'text-on-surface-variant border-outline-variant'

  return (
    <div className="flex flex-col gap-stack-md h-full">
      <div className="grid grid-cols-12 gap-gutter flex-1 min-h-[500px]">
        <div className="col-span-7 glass-card p-6 flex flex-col relative border-t-2 border-t-primary-container">
          <div className="font-label-caps text-label-caps text-on-surface-variant mb-4 flex justify-between items-center">
            <span>DIGITAL TWIN — AERO PISTON ENGINE</span>
            <span className={`px-3 py-1 rounded border font-label-caps text-label-caps ${badgeClass}`}>
              {s.status || 'UNKNOWN'}
            </span>
          </div>
          <div className="flex-1 flex items-center justify-center relative">
            <DigitalTwinSVG sensors={s} />
          </div>
          <div className="grid grid-cols-5 gap-3 mt-4">
            {[
              ['RPM', s.rpm, ''],
              ['TEMP', s.temperature, '°C'],
              ['VIB', s.vibration, 'mm/s'],
              ['PRESS', s.pressure, 'bar'],
              ['LOAD', s.load, '%'],
            ].map(([label, val, unit]) => (
              <div key={label} className="glass-card p-2 text-center">
                <div className="font-label-caps text-label-caps text-on-surface-variant">{label}</div>
                <div className="font-data-lg text-data-lg text-primary">
                  {val ?? '--'} {unit}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="col-span-5 flex flex-col gap-gutter">
          <div className="grid grid-cols-2 gap-gutter">
            <MetricCard label="ENGINE HEALTH" value={`${s.health ?? 0}%`} thresholds={[75, 50]} invert />
            <MetricCard label="FAULT RISK" value={`${s.faultRisk ?? 0}%`} thresholds={[30, 70]} />
            <MetricCard label="DEGRADATION" value={`${s.degradation ?? 0}%`} thresholds={[20, 50]} />
            <MetricCard label="EST. RUL" value={`${s.rulHours ?? 0} hrs`} thresholds={[2, 0.5]} invert />
          </div>

          <div className="glass-card p-4 flex-1">
            <div className="font-label-caps text-label-caps text-on-surface-variant mb-3">TWIN STATE DETAIL</div>
            <div className="space-y-2 font-body-md text-body-md">
              <Row label="Fault Type" value={s.faultType || 'NONE'} />
              <Row label="Anomaly Score" value={`${s.anomalyScore ?? 0} / 100`} />
              <Row label="Time to Critical" value={`${s.timeToCriticalMinutes ?? '--'} min`} />
              <Row label="Mission Risk" value={s.missionRisk || '--'} />
              <Row label="Mission Readiness" value={s.missionReadiness || '--'} />
              <Row label="Scenario" value={s.scenario || 'NORMAL'} />
              <Row label="Last Update" value={s.timestamp || '--'} />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function Row({ label, value }) {
  return (
    <div className="flex justify-between border-b border-surface-variant pb-1">
      <span className="text-on-surface-variant font-label-caps text-label-caps">{label}</span>
      <span className="text-on-surface font-data-lg text-body-md">{value}</span>
    </div>
  )
}

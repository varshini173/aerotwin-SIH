import { useState } from 'react'
import { useEngineSocket } from '../hooks/useEngineSocket'
import MetricCard from '../components/MetricCard'
import TelemetryCard from '../components/TelemetryCard'
import DigitalTwinSVG from '../components/DigitalTwinSVG'
import AlertFeed from '../components/AlertFeed'
import SimulationControls from '../components/SimulationControls'
import HardwareStatusPanel from '../components/HardwareStatusPanel'
import TimeSeriesChart from '../charts/TimeSeriesChart'
import { api } from '../services/api'

export default function Overview() {
  const { state, history } = useEngineSocket(150)
  const [missionDuration, setMissionDuration] = useState('2')

  const s = state || {}
  const missionDurationNum = parseFloat(missionDuration) || 0
  const isMissionReady = s.missionReadiness === 'READY'
  const chartData = history.map((h, i) => ({ ...h, tick: i }))

  const handleMissionSubmit = async (e) => {
    e.preventDefault()
    await api.setMission(missionDurationNum, 60)
  }

  return (
    <div className="flex flex-col gap-stack-md h-full">
      {/* Top Row: Exec Summary */}
      <div className="grid grid-cols-4 gap-gutter">
        <MetricCard label="ENGINE HEALTH" value={`${(s.health ?? 0).toFixed?.(1) ?? s.health}%`} thresholds={[75, 50]} invert />
        <MetricCard label="FAULT RISK" value={`${s.faultRisk ?? 0}%`} thresholds={[30, 70]} />
        <MetricCard label="DEGRADATION" value={`${s.degradation ?? 0}%`} thresholds={[20, 50]} />
        <MetricCard label="EST. RUL" value={`${s.rulHours ?? 0} hrs`} thresholds={[2, 0.5]} invert />
      </div>

      {/* Middle Row: Twin, Telemetry, Controls */}
      <div className="grid grid-cols-12 gap-gutter flex-1 min-h-[400px]">
        <div className="col-span-5 glass-card p-4 flex flex-col relative border-t-2 border-t-primary-container">
          <div className="font-label-caps text-label-caps text-on-surface-variant mb-4 flex justify-between">
            <span>DIGITAL TWIN VISUALIZER</span>
            <span className="text-primary animate-pulse flex items-center gap-1">
              <span className="material-symbols-outlined text-[14px]">sync</span> LIVE
            </span>
          </div>
          <div className="flex-1 flex items-center justify-center relative">
            <DigitalTwinSVG sensors={s} />
            <div className="absolute top-4 left-4 bg-surface-container-lowest/80 p-2 rounded border border-outline-variant font-data-lg text-body-md text-on-surface">
              T: <span>{s.temperature ?? '--'}°C</span>
            </div>
            <div className="absolute bottom-4 left-4 bg-surface-container-lowest/80 p-2 rounded border border-outline-variant font-data-lg text-body-md text-on-surface">
              V: <span>{s.vibration ?? '--'} mm/s</span>
            </div>
          </div>
        </div>

        <div className="col-span-4 flex flex-col gap-2">
          <div className="font-label-caps text-label-caps text-on-surface-variant mb-2">LIVE SENSOR TELEMETRY</div>
          <TelemetryCard name="RPM" val={s.rpm ?? '--'} unit="RPM" thresholds={[5200, 6000]} gaugePercent={((s.rpm ?? 4200) / 7500) * 100} />
          <TelemetryCard name="TEMPERATURE" val={s.temperature ?? '--'} unit="°C" thresholds={[95, 110]} gaugePercent={((s.temperature ?? 72) / 160) * 100} />
          <TelemetryCard name="VIBRATION" val={s.vibration ?? '--'} unit="mm/s" thresholds={[4, 7]} gaugePercent={((s.vibration ?? 1.2) / 12) * 100} />
          <TelemetryCard name="PRESSURE" val={s.pressure ?? '--'} unit="bar" thresholds={[2.5, 1.8]} gaugePercent={((s.pressure ?? 4.2) / 8) * 100} />
          <TelemetryCard name="LOAD" val={s.load ?? '--'} unit="%" thresholds={[80, 92]} gaugePercent={s.load ?? 55} />
        </div>

        <div className="col-span-3 flex flex-col gap-stack-md">
          <form
            onSubmit={handleMissionSubmit}
            className={`glass-card p-4 border-l-4 ${isMissionReady ? 'border-l-secondary bg-secondary/5' : 'border-l-error bg-error/5'}`}
          >
            <div className="font-label-caps text-label-caps text-on-surface-variant mb-4 flex items-center gap-2">
              <span className="material-symbols-outlined text-[16px]">flight_takeoff</span>
              MISSION READINESS
            </div>
            <div className="mb-4">
              <label className="block font-label-sm text-label-sm text-on-surface-variant mb-1">PLANNED DURATION (HRS)</label>
              <input
                type="number"
                step="0.1"
                value={missionDuration}
                onChange={(e) => setMissionDuration(e.target.value)}
                className="w-full bg-surface-container border-b border-outline-variant focus:border-primary-container text-on-surface font-data-lg p-2 focus:ring-0 outline-none transition-colors"
              />
            </div>
            <button
              type="submit"
              className={`w-full p-2 text-center font-headline-md text-body-md font-bold rounded ${
                isMissionReady ? 'text-secondary border border-secondary/30' : 'text-error border border-error/30 animate-pulse'
              }`}
            >
              {s.missionReadiness || 'MISSION READY'}
            </button>
            <div className="text-center font-label-sm text-label-sm mt-2 text-outline">
              {s.recommendation || 'Set duration and submit to evaluate.'}
            </div>
          </form>

          <HardwareStatusPanel />
          <SimulationControls activeScenario={s.scenario} />
        </div>
      </div>

      {/* Trend Charts */}
      <div className="grid grid-cols-4 gap-gutter">
        <TimeSeriesChart data={chartData} dataKey="temperature" label="TEMPERATURE" color="#ffb95f" unit="°C" height={120} />
        <TimeSeriesChart data={chartData} dataKey="vibration" label="VIBRATION" color="#ff8a80" unit=" mm/s" height={120} />
        <TimeSeriesChart data={chartData} dataKey="health" label="ENGINE HEALTH" color="#4edea3" unit="%" height={120} />
        <TimeSeriesChart data={chartData} dataKey="degradation" label="DEGRADATION" color="#ffb4ab" unit="%" height={120} />
      </div>

      <AlertFeed alerts={s.alerts} />
    </div>
  )
}

import { useState } from 'react'
import { useEngineSocket } from '../hooks/useEngineSocket'
import { api } from '../services/api'

const RISK_STYLES = {
  LOW: 'text-secondary border-secondary bg-secondary/10',
  MODERATE: 'text-tertiary-fixed-dim border-tertiary-fixed-dim bg-tertiary-fixed-dim/10',
  HIGH: 'text-error border-error bg-error/10 glow-critical',
}

export default function MissionReadiness() {
  const { state } = useEngineSocket(30)
  const s = state || {}
  const [duration, setDuration] = useState('2')
  const [load, setLoad] = useState('60')
  const [result, setResult] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      const res = await api.setMission(parseFloat(duration) || 0, parseFloat(load) || 60)
      setResult(res)
    } finally {
      setSubmitting(false)
    }
  }

  const risk = result?.missionRisk || s.missionRisk || 'LOW'
  const badgeClass = RISK_STYLES[risk] || 'text-on-surface-variant border-outline-variant'

  return (
    <div className="flex flex-col gap-stack-md h-full">
      <div className="grid grid-cols-12 gap-gutter">
        <form onSubmit={handleSubmit} className="col-span-4 glass-card p-6 flex flex-col gap-4">
          <div className="font-label-caps text-label-caps text-on-surface-variant flex items-center gap-2">
            <span className="material-symbols-outlined text-[16px]">flight_takeoff</span>
            PLAN A MISSION
          </div>
          <div>
            <label className="block font-label-sm text-label-sm text-on-surface-variant mb-1">
              PLANNED MISSION DURATION (HRS)
            </label>
            <input
              type="number"
              step="0.1"
              min="0"
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
              className="w-full bg-surface-container border-b border-outline-variant focus:border-primary-container text-on-surface font-data-lg p-2 focus:ring-0 outline-none transition-colors"
            />
          </div>
          <div>
            <label className="block font-label-sm text-label-sm text-on-surface-variant mb-1">
              EXPECTED MISSION LOAD (%)
            </label>
            <input
              type="number"
              step="1"
              min="0"
              max="100"
              value={load}
              onChange={(e) => setLoad(e.target.value)}
              className="w-full bg-surface-container border-b border-outline-variant focus:border-primary-container text-on-surface font-data-lg p-2 focus:ring-0 outline-none transition-colors"
            />
          </div>
          <button
            type="submit"
            disabled={submitting}
            className="mt-2 py-2 border border-primary-container text-primary hover:bg-primary-container/10 transition-colors rounded font-label-caps text-label-caps disabled:opacity-60"
          >
            {submitting ? 'EVALUATING…' : 'EVALUATE MISSION'}
          </button>
        </form>

        <div className="col-span-8 glass-card p-6 flex flex-col gap-4">
          <div className="font-label-caps text-label-caps text-on-surface-variant">MISSION ASSESSMENT</div>
          <div className={`p-6 text-center rounded border ${badgeClass}`}>
            <div className="font-display-lg text-display-lg font-bold">{risk} RISK</div>
            <div className="font-label-caps text-label-caps mt-2">
              {result?.missionReadiness || s.missionReadiness || 'READY'}
            </div>
          </div>
          <div className="glass-card p-4">
            <div className="font-label-caps text-label-caps text-on-surface-variant mb-2">RECOMMENDATION</div>
            <div className="font-body-md text-body-md text-on-surface">
              {result?.recommendation || s.recommendation || 'Set mission parameters and evaluate.'}
            </div>
          </div>
          <div className="grid grid-cols-3 gap-gutter">
            <Stat label="CURRENT HEALTH" value={`${s.health ?? 0}%`} />
            <Stat label="ESTIMATED RUL" value={`${s.rulHours ?? 0} hrs`} />
            <Stat label="FAULT RISK" value={`${s.faultRisk ?? 0}%`} />
          </div>
          {result && (
            <div className="grid grid-cols-2 gap-gutter">
              <Stat label="REQUIRED RUL (LOW-RISK MARGIN)" value={`${result.requiredRulHoursLowRisk} hrs`} />
              <Stat label="EFFECTIVE MISSION DEMAND" value={`${result.effectiveMissionHours} hrs`} />
            </div>
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

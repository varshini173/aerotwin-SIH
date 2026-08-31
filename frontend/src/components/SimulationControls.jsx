import { useState } from 'react'
import { api } from '../services/api'

const SCENARIOS = [
  { id: 'NORMAL', label: 'NORMAL OP', activeColor: 'bg-secondary/20 text-secondary border-secondary glow-active' },
  { id: 'OVERHEAT', label: 'INJECT OVERHEAT', activeColor: 'bg-error/20 text-error border-error glow-critical' },
  {
    id: 'VIBRATION',
    label: 'INJECT VIBRATION',
    activeColor: 'bg-tertiary-fixed-dim/20 text-tertiary-fixed-dim border-tertiary-fixed-dim glow-warning',
  },
  {
    id: 'RPM_INSTABILITY',
    label: 'RPM FLUCTUATION',
    activeColor: 'bg-tertiary-fixed-dim/20 text-tertiary-fixed-dim border-tertiary-fixed-dim',
  },
  {
    id: 'PRESSURE_ABNORMALITY',
    label: 'PRESSURE ABNORMALITY',
    activeColor: 'bg-tertiary-fixed-dim/20 text-tertiary-fixed-dim border-tertiary-fixed-dim',
  },
  {
    id: 'COMBINED_DEGRADATION',
    label: 'ACCEL. DEGRADATION',
    activeColor: 'bg-error/20 text-error border-error',
  },
  {
    id: 'PROGRESSIVE_DEGRADATION',
    label: 'PROGRESSIVE WEAR',
    activeColor: 'bg-error/20 text-error border-error',
  },
]

export default function SimulationControls({ activeScenario }) {
  const [pending, setPending] = useState(null)

  const handleClick = async (id) => {
    setPending(id)
    try {
      await api.setScenario(id)
    } finally {
      setPending(null)
    }
  }

  const handleReset = async () => {
    setPending('RESET')
    try {
      await api.resetEngine()
    } finally {
      setPending(null)
    }
  }

  return (
    <div className="glass-card p-4 flex-1 flex flex-col">
      <div className="font-label-caps text-label-caps text-on-surface-variant mb-4 flex items-center gap-2">
        <span className="material-symbols-outlined text-[16px]">tune</span>
        SIMULATION CONTROLS
      </div>

      <div className="flex flex-col gap-2 flex-1 justify-center">
        {SCENARIOS.map((btn) => (
          <button
            key={btn.id}
            onClick={() => handleClick(btn.id)}
            disabled={pending !== null}
            className={`font-label-caps text-label-caps py-2 px-3 rounded border text-left transition-all disabled:opacity-60 ${
              activeScenario === btn.id
                ? btn.activeColor
                : 'border-outline-variant text-on-surface-variant hover:bg-surface-container-highest hover:text-primary'
            }`}
          >
            {activeScenario === btn.id ? '> ' : ''}
            {btn.label}
            {pending === btn.id ? ' …' : ''}
          </button>
        ))}
      </div>

      <button
        onClick={handleReset}
        disabled={pending !== null}
        className="mt-4 py-2 border border-outline-variant text-on-surface hover:bg-surface-container-highest hover:text-primary transition-colors rounded font-label-caps text-label-caps disabled:opacity-60"
      >
        RESET SIMULATION{pending === 'RESET' ? ' …' : ''}
      </button>
    </div>
  )
}

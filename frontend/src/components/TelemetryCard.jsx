function statusColor(val, thresholds) {
  if (val >= thresholds[1]) return 'text-error'
  if (val >= thresholds[0]) return 'text-tertiary-fixed-dim'
  return 'text-secondary'
}

export default function TelemetryCard({ name, val, unit, thresholds, gaugePercent }) {
  const colorClass = statusColor(val, thresholds)
  return (
    <div className="glass-card p-3 flex items-center justify-between">
      <div className="font-label-caps text-label-caps text-on-surface w-24">{name}</div>
      <div className="flex-1 mx-4 h-1.5 bg-surface-container-highest rounded-full overflow-hidden">
        <div
          className={`h-full ${colorClass.replace('text-', 'bg-')}`}
          style={{ width: `${Math.max(4, Math.min(100, gaugePercent))}%`, transition: 'width 0.5s ease' }}
        ></div>
      </div>
      <div className="text-right w-24 flex items-baseline justify-end gap-1">
        <span className={`font-data-lg text-data-lg ${colorClass}`}>{val}</span>
        <span className="font-label-sm text-label-sm text-on-surface-variant">{unit}</span>
      </div>
    </div>
  )
}

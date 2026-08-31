function statusColor(val, thresholds, invert = false) {
  // thresholds = [warning, critical]
  if (invert) {
    if (val <= thresholds[1]) return 'text-error'
    if (val <= thresholds[0]) return 'text-tertiary-fixed-dim'
    return 'text-secondary'
  }
  if (val >= thresholds[1]) return 'text-error'
  if (val >= thresholds[0]) return 'text-tertiary-fixed-dim'
  return 'text-secondary'
}

export default function MetricCard({ label, value, thresholds, invert = false }) {
  const colorClass = statusColor(value, thresholds, invert)
  const glowClass = colorClass.includes('error')
    ? 'bg-error'
    : colorClass.includes('tertiary')
    ? 'bg-tertiary-fixed-dim'
    : 'bg-secondary'
  return (
    <div className="glass-card p-4 flex flex-col justify-between h-24 relative overflow-hidden">
      <div className="font-label-caps text-label-caps text-on-surface-variant z-10">{label}</div>
      <div className={`font-data-lg text-display-lg mt-auto z-10 ${colorClass}`}>{value}</div>
      <div className={`absolute -right-4 -bottom-4 w-16 h-16 rounded-full blur-xl opacity-20 ${glowClass}`}></div>
    </div>
  )
}

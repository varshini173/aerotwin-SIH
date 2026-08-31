const STATUS_COLOR = {
  HEALTHY: 'text-secondary',
  NORMAL: 'text-secondary',
  DEGRADING: 'text-tertiary-fixed-dim',
  WARNING: 'text-tertiary-fixed-dim',
  CRITICAL: 'text-error',
}

export default function Header({ connected, status }) {
  const colorClass = STATUS_COLOR[status] || 'text-on-surface-variant'
  return (
    <header className="fixed top-0 right-0 left-64 h-16 backdrop-blur-xl bg-surface-container/80 border-b border-outline-variant shadow-sm flex items-center justify-between px-gutter w-full z-40">
      <div className="flex items-center gap-4">
        <h1 className="font-display-lg text-display-lg font-bold tracking-tight text-primary truncate">
          SIH 2026 UAV Mission Control
        </h1>
        <span
          className={`px-2 py-1 rounded font-label-caps text-label-caps flex items-center gap-2 border ${
            connected ? 'bg-secondary/10 border-secondary text-secondary' : 'bg-error/10 border-error text-error'
          }`}
        >
          <span className={`w-2 h-2 rounded-full ${connected ? 'bg-secondary animate-pulse' : 'bg-error'}`}></span>
          {connected ? 'LIVE CONNECTION: ACTIVE' : 'LIVE CONNECTION: LOST'}
        </span>
      </div>
      <div className="flex items-center gap-6">
        <div className="font-label-caps text-label-caps text-on-surface flex flex-col items-end">
          <span>ENGINE_ID: UAV-77X</span>
          <span className={`${colorClass} glow-active`}>STATUS: {status || '—'}</span>
        </div>
      </div>
    </header>
  )
}

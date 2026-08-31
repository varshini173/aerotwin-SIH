export default function AlertFeed({ alerts = [] }) {
  return (
    <div className="glass-card p-0 flex flex-col h-48 border-t-2 border-t-outline-variant">
      <div className="p-3 border-b border-outline-variant font-label-caps text-label-caps text-on-surface-variant flex items-center gap-2 bg-surface-container/50">
        <span className="material-symbols-outlined text-[16px]">list_alt</span>
        SYSTEM LOGS &amp; ALERTS
      </div>
      <div className="flex-1 overflow-y-auto p-2 font-data-lg text-body-md">
        {alerts.length === 0 && (
          <div className="text-on-surface-variant opacity-60 py-2 px-2">No alerts yet.</div>
        )}
        {alerts.map((alert, i) => {
          const isError = alert.severity === 'CRITICAL' || alert.severity === 'HIGH'
          const isWarning = alert.severity === 'WARNING'
          return (
            <div
              key={i}
              className={`flex gap-4 py-1.5 border-b border-surface-variant last:border-0 ${
                isError ? 'text-error' : isWarning ? 'text-tertiary-fixed-dim' : 'text-on-surface-variant'
              }`}
            >
              <span className="opacity-70 w-24 shrink-0">[{alert.timestamp}]</span>
              <span className={isError ? 'font-bold' : ''}>
                {alert.severity}: {alert.message}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

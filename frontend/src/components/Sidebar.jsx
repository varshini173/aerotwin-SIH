import { NavLink } from 'react-router-dom'

const NAV_ITEMS = [
  { to: '/', label: 'Overview', icon: 'dashboard' },
  { to: '/digital-twin', label: 'Digital Twin', icon: 'model_training' },
  { to: '/live-monitoring', label: 'Live Monitoring', icon: 'monitoring' },
  { to: '/mission-readiness', label: 'Mission Readiness', icon: 'verified' },
  { to: '/history', label: 'History', icon: 'history' },
]

export default function Sidebar({ connected }) {
  return (
    <nav className="h-screen w-64 fixed left-0 top-0 bg-surface-container-low border-r border-outline-variant flex flex-col py-margin-page z-50">
      <div className="px-6 mb-8 flex flex-col gap-2">
        <div className="w-12 h-12 rounded-lg bg-surface-container-highest border border-outline-variant flex items-center justify-center overflow-hidden mb-2">
          <span className="material-symbols-outlined text-primary text-[28px]">flight</span>
        </div>
        <div className="font-headline-md text-headline-md font-bold text-primary">MALE UAV Engine</div>
        <div className="font-label-caps text-label-caps text-on-surface-variant">Telemetry &amp; Digital Twin</div>
      </div>
      <div className="flex-1 px-4 space-y-2">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-4 px-4 py-3 rounded-lg font-medium transition-all duration-200 ${
                isActive
                  ? 'text-primary font-bold border-r-2 border-primary bg-surface-container-highest opacity-90'
                  : 'text-on-surface-variant hover:bg-surface-container-highest hover:text-primary'
              }`
            }
          >
            <span className="material-symbols-outlined">{item.icon}</span>
            <span className="font-label-caps text-label-caps">{item.label}</span>
          </NavLink>
        ))}
      </div>
      <div className="px-6 mt-auto">
        <div
          className={`p-3 border rounded glass-card text-center font-label-caps text-label-caps flex items-center justify-center gap-2 ${
            connected ? 'border-secondary text-secondary glow-active' : 'border-error text-error'
          }`}
        >
          <span className="material-symbols-outlined text-[16px]">
            {connected ? 'check_circle' : 'cloud_off'}
          </span>
          {connected ? 'System Status: OK' : 'Backend Disconnected'}
        </div>
      </div>
    </nav>
  )
}

import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Header from './components/Header'
import Overview from './pages/Overview'
import DigitalTwin from './pages/DigitalTwin'
import LiveMonitoring from './pages/LiveMonitoring'
import MissionReadiness from './pages/MissionReadiness'
import History from './pages/History'
import { useEngineSocket } from './hooks/useEngineSocket'

export default function App() {
  // A single top-level socket subscription drives the header's connection
  // badge and status text; each page also opens its own subscription for
  // its own history buffer sizing needs.
  const { state, connected } = useEngineSocket(5)

  return (
    <div className="engineering-grid min-h-screen">
      <Sidebar connected={connected} />
      <Header connected={connected} status={state?.status} />
      <main className="ml-64 mt-16 p-margin-page min-h-[calc(100vh-4rem)]">
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/digital-twin" element={<DigitalTwin />} />
          <Route path="/live-monitoring" element={<LiveMonitoring />} />
          <Route path="/mission-readiness" element={<MissionReadiness />} />
          <Route path="/history" element={<History />} />
        </Routes>
      </main>
    </div>
  )
}

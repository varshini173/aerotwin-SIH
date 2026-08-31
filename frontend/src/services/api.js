const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })

  if (!res.ok) {
    throw new Error(`API ${path} failed: ${res.status}`)
  }

  return res.json()
}

export const api = {
  getStatus: () => request('/api/engine/status'),

  getPrediction: () =>
    request('/api/engine/prediction'),

  getMissionRisk: () =>
    request('/api/engine/mission-risk'),

  getHistory: (runId, limit = 300) =>
    request(
      `/api/engine/history?${runId ? `run_id=${runId}&` : ''}limit=${limit}`
    ),

  getRuns: () =>
    request('/api/engine/runs'),

  getRunDetail: (runId) =>
    request(`/api/engine/runs/${runId}`),

  startEngine: () =>
    request('/api/engine/start', {
      method: 'POST',
    }),

  resetEngine: () =>
    request('/api/engine/reset', {
      method: 'POST',
    }),

  setScenario: (scenario) =>
    request('/api/engine/scenario', {
      method: 'POST',
      body: JSON.stringify({ scenario }),
    }),

  setMission: (duration_hours, expected_load_percent) =>
    request('/api/engine/mission', {
      method: 'POST',
      body: JSON.stringify({
        duration_hours,
        expected_load_percent,
      }),
    }),

  getHardwareStatus: () =>
    request('/api/engine/hardware-status'),

  // --------------------------------------------------
  // DATA SOURCE
  // --------------------------------------------------

  setSource: (source) =>
    request('/api/engine/source', {
      method: 'POST',
      body: JSON.stringify({ source }),
    }),

  getSource: () =>
    request('/api/engine/source'),

  // --------------------------------------------------
  // ARDUINO SERIAL CONNECTION
  // --------------------------------------------------

  getSerialPorts: () =>
    request('/api/engine/serial/ports'),

  connectSerial: (port) =>
    request('/api/engine/serial/connect', {
      method: 'POST',
      body: JSON.stringify({ port }),
    }),

  disconnectSerial: () =>
    request('/api/engine/serial/disconnect', {
      method: 'POST',
    }),
}

export const WS_URL =
  'wss://aerotwin-sih-2u55.onrender.com' +
  '/ws/engine'
